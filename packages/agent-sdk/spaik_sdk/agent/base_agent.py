import asyncio
import contextvars
import threading
import uuid
from abc import ABC
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, TypeVar

from ag_ui import core as ui
from ag_ui.core import AssistantMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import message_to_dict
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from spaik_sdk.attachments.models import Attachment
from spaik_sdk.config.env import env_config
from spaik_sdk.llm.cancellation_handle import CancellationHandle
from spaik_sdk.llm.cost.cost_estimate import CostSummary
from spaik_sdk.llm.cost.cost_provider import CostContext, CostProvider
from spaik_sdk.llm.langchain_service import LangChainService, RunCancelled
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.prompt.get_prompt_loader import get_prompt_loader
from spaik_sdk.prompt.prompt_loader import PromptLoader
from spaik_sdk.prompt.prompt_loader_mode import PromptLoaderMode
from spaik_sdk.recording.conditional_recorder import ConditionalRecorder
from spaik_sdk.thread.models import Invocation
from spaik_sdk.thread.thread_container import ThreadContainer, message_text
from spaik_sdk.tools.tool_provider import ToolProvider
from spaik_sdk.tracing.agent_trace import AgentTrace
from spaik_sdk.tracing.trace_sink import TraceSink
from spaik_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC):
    def __init__(
        self,
        system_prompt_args: Dict[str, Any] = {},
        system_prompt_version: Optional[str] = None,
        system_prompt: Optional[str] = None,
        prompt_loader: Optional[PromptLoader] = None,
        prompt_loader_mode: Optional[PromptLoaderMode] = None,
        llm_config: Optional[LLMConfig] = None,
        llm_model: Optional[LLMModel | str] = None,
        reasoning: Optional[bool] = None,
        chat_model: Optional[BaseChatModel] = None,
        provider: Optional[str] = None,
        provider_kwargs: Optional[Dict[str, Any]] = None,
        trace: Optional[AgentTrace] = None,
        trace_sink: Optional[TraceSink] = None,
        thread_container: Optional[ThreadContainer] = None,
        tools: Optional[List[BaseTool]] = None,
        tool_providers: Optional[List[ToolProvider]] = None,
        recorder: Optional[ConditionalRecorder] = None,
        cancellation_handle: Optional[CancellationHandle] = None,
        cost_provider: Optional[CostProvider] = None,
    ):
        logger.debug("Initializing BaseAgent")
        # Generate unique instance ID for trace correlation
        self.agent_instance_id: str = str(uuid.uuid4())
        self.tool_providers = tool_providers if tool_providers is not None else self.get_tool_providers()
        self.prompt_loader = prompt_loader if prompt_loader is not None else get_prompt_loader(prompt_loader_mode)
        self.system_prompt = (
            system_prompt if system_prompt is not None else self._get_system_prompt(system_prompt_args, system_prompt_version)
        )
        self.trace = (
            trace
            if trace is not None
            else AgentTrace(
                self.system_prompt,
                self.__class__.__name__,
                trace_sink=trace_sink,
                agent_instance_id=self.agent_instance_id,
            )
        )
        self.thread_container = thread_container if thread_container is not None else ThreadContainer(self.system_prompt)
        self.tools = tools if tools is not None else self._create_tools(self.tool_providers)
        self.thread_container.bind_tool_providers(self.tool_providers)
        if chat_model is not None and (llm_config is not None or llm_model is not None):
            raise ValueError("chat_model cannot be combined with llm_config or llm_model")
        self.llm_config = (
            llm_config
            if llm_config is not None
            else (
                LLMConfig(chat_model=chat_model)
                if chat_model is not None
                else self.create_llm_config(llm_model, reasoning, provider, provider_kwargs)
            )
        )
        self.recorder = recorder.get_recorder() if recorder is not None else None
        self.playback = recorder.get_playback() if recorder is not None else None
        self.cancellation_handle = cancellation_handle
        kwargs = self.llm_config.provider_kwargs
        injected = self.llm_config.chat_model
        key = kwargs.get("api_key", env_config.get_proxy_api_key()) or getattr(injected, "openai_api_key", None)
        if hasattr(key, "get_secret_value"):
            key = key.get_secret_value()
        self.cost_provider = cost_provider or CostProvider(
            self.llm_config.provider_name,
            base_url=str(kwargs.get("base_url") or getattr(injected, "openai_api_base", None) or env_config.get_proxy_base_url()),
            api_key=key or None,
        )
        self._running = False

    async def get_event_stream(
        self, user_input: str | None = None, attachments: list[Attachment] | None = None, run_id: str | None = None
    ) -> AsyncGenerator[ui.BaseEvent, None]:
        if self._running:
            raise RuntimeError("This agent is already running")
        self._running = True
        run_id = run_id or str(uuid.uuid4())
        try:
            self.trace.add_input(user_input)
            if user_input is not None:
                self.thread_container.add_message(
                    ui.UserMessage(id=str(uuid.uuid4()), content=user_input), {"attachments": [a.to_dict() for a in attachments or []]}
                )
            yield ui.RunStartedEvent(thread_id=self.thread_container.thread_id, run_id=run_id)
            yield ui.MessagesSnapshotEvent(messages=self.thread_container.messages)
            yield ui.StateSnapshotEvent(snapshot=self.thread_container.envelope.metadata.get("state", {}))
            async for event in self._create_langchain_service().stream():
                if isinstance(event, ui.ToolCallResultEvent):
                    self.trace.add_step(f"Tool {event.tool_call_id}: {event.content}")
                yield event
            yield ui.MessagesSnapshotEvent(messages=self.thread_container.messages)
            yield ui.RunFinishedEvent(thread_id=self.thread_container.thread_id, run_id=run_id)
        except RunCancelled:
            yield ui.MessagesSnapshotEvent(messages=self.thread_container.messages)
            yield ui.RunFinishedEvent(
                thread_id=self.thread_container.thread_id, run_id=run_id, outcome=ui.RunFinishedCancelledOutcome(type="cancelled")
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.trace.add_step(f"Run failed: {exc}")
            yield ui.RunErrorEvent(message=str(exc), code="agent_error")
        finally:
            self._running = False
            latest = self.thread_container.get_latest_ai_message()
            if latest is not None:
                self.trace.add_step(message_text(latest))

    def get_response_stream(self, user_input=None, attachments=None):
        return self.get_event_stream(user_input, attachments)

    async def get_response_async(self, user_input=None, attachments=None) -> AssistantMessage:
        async for event in self.get_event_stream(user_input, attachments):
            if isinstance(event, ui.RunErrorEvent):
                raise RuntimeError(event.message)
        response = self.thread_container.get_latest_ai_message()
        if response is None:
            raise ValueError("No response received")
        return response

    def get_response(self, user_input=None, attachments=None) -> AssistantMessage:
        return asyncio.run(self.get_response_async(user_input, attachments))

    def get_response_text(self, user_input=None, attachments=None) -> str:
        return message_text(self.get_response(user_input, attachments))

    async def get_response_text_async(self, user_input=None, attachments=None) -> str:
        return message_text(await self.get_response_async(user_input, attachments))

    def spawn(
        self,
        task: str,
        attachments: Optional[List[Attachment]] = None,
    ) -> "AssistantMessage":
        """Run this agent as an isolated subagent.

        Prevents LangChain callback context from leaking into this agent's thread,
        which would cause the subagent's tool calls to appear in the parent thread.
        """
        return BaseAgent.run_isolated(self.get_response_async(task, attachments))

    @staticmethod
    def run_isolated(coro: Any) -> Any:
        """Run a coroutine in a blank ContextVar context.

        Use this when calling a nested agent from inside a tool so that LangChain's
        callback handlers (stored in ContextVars) are not inherited by the subagent.
        """
        result: list = []
        error: list = []

        def _thread() -> None:
            ctx = contextvars.Context()
            try:
                ctx.run(lambda: result.append(asyncio.run(coro)))
            except Exception as exc:
                error.append(exc)

        t = threading.Thread(target=_thread)
        t.start()
        t.join()
        if error:
            raise error[0]
        return result[0]

    async def get_structured_response_async(self, prompt: str, output_schema: Type[T], reasoning_effort: Optional[str] = None) -> T:
        self.trace.add_structured_response_input(prompt, output_schema)
        if self.playback is not None:
            result = output_schema.model_validate(next(self.playback))
        else:
            config = self.llm_config.as_structured_response_config(reasoning_effort)
            model = config.get_model_wrapper().get_langchain_model()
            options = {"method": "json_schema"} if self.llm_config.provider_name == "anthropic" else {}
            response = await model.with_structured_output(output_schema, include_raw=True, **options).ainvoke(prompt)
            if not isinstance(response, dict):
                raise TypeError("Structured output with include_raw must return a dictionary")
            raw = response["raw"]
            raw_text = (
                raw.content if isinstance(raw.content, str) else "".join(b.get("text", "") for b in raw.content if isinstance(b, dict))
            )
            message = ui.AssistantMessage(id=str(uuid.uuid4()), content=raw_text)
            self.thread_container.add_message(ui.UserMessage(id=str(uuid.uuid4()), content=prompt))
            self.thread_container.add_message(message)
            self.thread_container.envelope.replay[message.id] = {"langchain": message_to_dict(raw)}
            metadata = raw.response_metadata or {}
            cost = await self.cost_provider.resolve(
                CostContext(provider=self.llm_config.provider_name, response_id=metadata.get("id") or raw.id, metadata=metadata)
            )
            self.thread_container.add_invocation(
                Invocation(
                    id=raw.id or str(uuid.uuid4()),
                    message_id=message.id,
                    provider=self.llm_config.provider_name,
                    model=self.llm_config.model_name,
                    usage=raw.usage_metadata,
                    cost=cost,
                )
            )
            if response.get("parsing_error"):
                raise response["parsing_error"]
            result = output_schema.model_validate(response["parsed"])
            message.content = result.model_dump_json()
        if self.recorder is not None:
            self.recorder.record_structured(result.model_dump())
        self.trace.add_structured_response_output(result)
        return result

    def get_structured_response(self, prompt: str, output_schema: Type[T], reasoning_effort: Optional[str] = None) -> T:
        return asyncio.run(self.get_structured_response_async(prompt, output_schema, reasoning_effort))

    def run_cli(self):
        async def run():
            while True:
                prompt = await asyncio.to_thread(input, "> ")
                if prompt.strip() in {"exit", "quit"}:
                    break
                async for event in self.get_event_stream(prompt):
                    if isinstance(event, ui.TextMessageContentEvent):
                        print(event.delta, end="", flush=True)
                    elif isinstance(event, ui.RunErrorEvent):
                        print(event.message)
                print()

        asyncio.run(run())

    def create_llm_config(self, llm_model=None, reasoning=None, provider=None, provider_kwargs=None) -> LLMConfig:
        model = llm_model if llm_model is not None else self.get_llm_model()
        preset = model if isinstance(model, LLMModel) else ModelRegistry.by_id(model)
        provider = provider or env_config.get_key("MODEL_PROVIDER", required=False) or (preset.family if preset else None)
        if provider is None:
            raise ValueError("An arbitrary model ID requires provider")
        return LLMConfig(
            model=model,
            provider_type=provider,
            provider_kwargs=provider_kwargs or {},
            reasoning=reasoning if reasoning is not None else True,
        )

    def get_llm_model(self) -> LLMModel:
        return env_config.get_default_model()

    def get_tool_providers(self) -> List[ToolProvider]:
        return []

    def set_thread_container(self, thread_container: ThreadContainer) -> None:
        self.thread_container = thread_container
        if self.thread_container.system_prompt is None:
            self.thread_container.system_prompt = self.system_prompt
        self.thread_container.bind_tool_providers(self.tool_providers)

    def set_cancellation_handle(self, cancellation_handle):
        self.cancellation_handle = cancellation_handle

    def _get_system_prompt(self, args, version=None) -> str:
        return self.prompt_loader.get_system_prompt(self.__class__, args, version)

    def _get_prompt(self, prompt_name, args, version=None) -> str:
        return self.prompt_loader.get_agent_prompt(self.__class__, prompt_name, args, version)

    def _create_tools(self, tool_providers=None):
        tools = []
        for provider in tool_providers or self.tool_providers:
            for tool in provider.get_tools():
                setattr(tool, "_spaik_tool_provider_id", provider.get_provider_id())
                setattr(tool, "_spaik_tool_provider", provider)
                tools.append(tool)
        return tools

    def _create_langchain_service(self):
        return LangChainService(
            self.llm_config, self.thread_container, self.cost_provider, self.tools, self.recorder, self.playback, self.cancellation_handle
        )

    def get_cost(self, latest_only: bool = False) -> CostSummary | None:
        return self.thread_container.get_cost_summary(latest_only)

    def get_langchain_model(self) -> BaseChatModel:
        return self.llm_config.get_model_wrapper().get_langchain_model()

    def get_react_agent(self):
        return self._create_langchain_service().create_executor()
