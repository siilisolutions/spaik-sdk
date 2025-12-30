import asyncio
from abc import ABC
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, TypeVar

from langchain_core.tools import BaseTool
from pydantic import BaseModel

from siili_ai_sdk.config.env import env_config
from siili_ai_sdk.llm.cancellation_handle import CancellationHandle
from siili_ai_sdk.llm.cost.builtin_cost_provider import BuiltinCostProvider
from siili_ai_sdk.llm.cost.cost_estimate import CostEstimate
from siili_ai_sdk.llm.cost.cost_provider import CostProvider
from siili_ai_sdk.llm.langchain_service import LangChainService
from siili_ai_sdk.models.llm_config import LLMConfig
from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.providers.provider_type import ProviderType
from siili_ai_sdk.prompt.get_prompt_loader import get_prompt_loader
from siili_ai_sdk.prompt.prompt_loader import PromptLoader
from siili_ai_sdk.prompt.prompt_loader_mode import PromptLoaderMode
from siili_ai_sdk.recording.conditional_recorder import ConditionalRecorder
from siili_ai_sdk.thread.adapters.cli.live_cli import LiveCLI
from siili_ai_sdk.thread.adapters.event_adapter import EventAdapter
from siili_ai_sdk.thread.adapters.sync_adapter import SyncAdapter
from siili_ai_sdk.thread.models import BlockFullyAddedEvent, ThreadEvent, ThreadMessage
from siili_ai_sdk.thread.thread_container import ThreadContainer
from siili_ai_sdk.tools.tool_provider import ToolProvider
from siili_ai_sdk.tracing.agent_trace import AgentTrace
from siili_ai_sdk.utils.init_logger import init_logger

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
        llm_model: Optional[LLMModel] = None,
        reasoning: Optional[bool] = None,
        trace: Optional[AgentTrace] = None,
        thread_container: Optional[ThreadContainer] = None,
        tools: Optional[List[BaseTool]] = None,
        tool_providers: Optional[List[ToolProvider]] = None,
        recorder: Optional[ConditionalRecorder] = None,
        cancellation_handle: Optional[CancellationHandle] = None,
        cost_provider: Optional[CostProvider] = None,
    ):
        logger.debug("Initializing BaseAgent")
        self.prompt_loader = prompt_loader or get_prompt_loader(prompt_loader_mode)
        self.system_prompt = system_prompt or self._get_system_prompt(system_prompt_args, system_prompt_version)
        self.trace = trace or AgentTrace(self.system_prompt, self.__class__.__name__)
        self.thread_container = thread_container or ThreadContainer(self.system_prompt)
        self.tools = tools or self._create_tools(tool_providers)
        self.llm_config = llm_config or self.create_llm_config(llm_model, reasoning)
        self.recorder = recorder.get_recorder() if recorder is not None else None
        self.playback = recorder.get_playback() if recorder is not None else None
        self.thread_container.subscribe(self._on_thread_event)
        self.cancellation_handle = cancellation_handle
        self.cost_provider = cost_provider or BuiltinCostProvider()

    def get_response_stream(self, user_input: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        self.trace.add_input(user_input)
        langchain_service = self._create_langchain_service()
        return langchain_service.execute_stream_tokens(user_input, self.tools)

    async def get_event_stream(self, user_input: Optional[str] = None) -> AsyncGenerator[ThreadEvent, None]:
        event_adapter = EventAdapter(self.thread_container)
        async for _event in self.get_response_stream(user_input):
            new_events = event_adapter.flush()
            for new_event in new_events:
                yield new_event
        event_adapter.cleanup()

    def get_response(self, user_input: Optional[str] = None) -> ThreadMessage:
        return asyncio.run(self.get_response_async(user_input))

    async def get_response_async(self, user_input: Optional[str] = None) -> ThreadMessage:
        sync_adapter = SyncAdapter(self.thread_container)
        await sync_adapter.run_async(self.get_response_stream(user_input))
        ret = await sync_adapter.wait_for_completion_async()
        if ret is None:
            raise ValueError("No response received")
        self.thread_container.complete_generation()
        return ret

    def get_response_text(self, user_input: Optional[str] = None) -> str:
        return self.get_response(user_input).get_text_content()

    async def get_response_text_async(self, user_input: Optional[str] = None) -> str:
        return (await self.get_response_async(user_input)).get_text_content()

    def get_structured_response(self, prompt: str, output_schema: Type[T]) -> T:
        self.trace.add_structured_response_input(prompt, output_schema)
        llm_config = self.llm_config.as_structured_response_config()
        langchain_service = self._create_langchain_service(llm_config)
        ret = langchain_service.get_structured_response(prompt, output_schema)
        self.trace.add_structured_response_output(ret)
        return ret

    def run_cli(self):
        asyncio.run(LiveCLI(self.thread_container).run_interactive(self))

    def create_llm_config(self, llm_model: Optional[LLMModel] = None, reasoning: Optional[bool] = None) -> LLMConfig:
        if llm_model is None:
            llm_model = self.get_llm_model()

        provider_type = ProviderType.from_family(llm_model.family)

        return LLMConfig(
            model=llm_model,
            provider_type=provider_type,
            reasoning=reasoning if reasoning is not None else llm_model.reasoning,
            tool_usage=len(self.tools) > 0,
        )

    def get_llm_model(self) -> LLMModel:
        return env_config.get_default_model()

    def is_reasoning(self) -> bool:
        return True

    def get_tool_providers(self) -> List[ToolProvider]:
        return []

    def set_thread_container(self, thread_container: ThreadContainer) -> None:
        self.thread_container = thread_container
        if self.thread_container.system_prompt is None:
            self.thread_container.system_prompt = self.system_prompt
        self.thread_container.subscribe(self._on_thread_event)

    def set_cancellation_handle(self, cancellation_handle: Optional[CancellationHandle]) -> None:
        self.cancellation_handle = cancellation_handle

    def _get_prompt(self, prompt_name: str, args: Dict[str, Any], version: Optional[str] = None) -> str:
        return self.prompt_loader.get_agent_prompt(self.__class__, prompt_name, args, version)

    def _get_system_prompt(self, args: Dict[str, Any], version: Optional[str] = None) -> str:
        return self.prompt_loader.get_system_prompt(self.__class__, args, version)

    def _create_tools(self, tool_providers: Optional[List[ToolProvider]] = None) -> List[BaseTool]:
        tool_providers = tool_providers or self.get_tool_providers()
        tools = []
        for provider in tool_providers:
            tools.extend(provider.get_tools())
        return tools

    def _create_langchain_service(self, llm_config: Optional[LLMConfig] = None) -> LangChainService:
        if self.thread_container is None:
            raise ValueError("Thread container is not set")
        return LangChainService(
            llm_config or self.llm_config,
            self.thread_container,
            self.__class__.__name__,
            self.__class__.__name__,
            self.recorder,
            self.playback,
            self.cancellation_handle,
        )

    def _on_thread_event(self, event: ThreadEvent) -> None:
        logger.debug(f"Thread event: {event}")
        """Handle thread events and forward to trace"""
        if isinstance(event, BlockFullyAddedEvent):
            self.trace.add_block(event.block)

    def get_cost(self, latest_only: bool = False) -> CostEstimate:
        token_usage = self.thread_container.get_token_usage()
        if latest_only:
            token_usage = self.thread_container.get_latest_token_usage()
        if token_usage is None:
            from siili_ai_sdk.llm.consumption.token_usage import TokenUsage
            token_usage = TokenUsage(input_tokens=0, output_tokens=0)
        return self.cost_provider.get_cost_estimate(self.get_llm_model(), token_usage)
