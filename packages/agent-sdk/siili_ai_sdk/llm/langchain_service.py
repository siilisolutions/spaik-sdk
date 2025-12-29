import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Type, TypeVar, cast

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool

# Using create_react_agent because create_agent from langchain.agents
# uses invoke() internally and does NOT emit on_chat_model_stream events,
# which breaks token-level streaming. See: https://github.com/langchain-ai/langchain/issues/34017
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from siili_ai_sdk.config.env import env_config
from siili_ai_sdk.llm.cancellation_handle import CancellationHandle
from siili_ai_sdk.llm.extract_error_message import extract_error_message
from siili_ai_sdk.llm.langchain_loop_manager import get_langchain_loop_manager, should_use_loop_manager
from siili_ai_sdk.llm.message_handler import MessageHandler
from siili_ai_sdk.models.llm_config import LLMConfig
from siili_ai_sdk.recording.base_playback import BasePlayback
from siili_ai_sdk.recording.base_recorder import BaseRecorder
from siili_ai_sdk.thread.models import MessageBlock, MessageBlockType, ThreadMessage
from siili_ai_sdk.thread.thread_container import ThreadContainer
from siili_ai_sdk.utils.init_logger import init_logger

DEBUG = env_config.is_debug_mode("langchain")
logger = init_logger(__name__)

# Suppress noisy HTTP request logs from anthropic and httpx
logging.getLogger("anthropic._base_client").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

if DEBUG:
    from langchain_core.globals import set_debug

    set_debug(True)

config = RunnableConfig(recursion_limit=100)

T = TypeVar("T", bound=BaseModel)


class LangChainService:
    def __init__(
        self,
        llm_config: LLMConfig,
        thread_container: ThreadContainer,
        assistant_name: str,
        assistant_id: str,
        recorder: Optional[BaseRecorder] = None,
        playback: Optional[BasePlayback] = None,
        cancellation_handle: Optional[CancellationHandle] = None,
    ):
        self.llm_config = llm_config

        self.thread_container = thread_container
        self.message_handler = MessageHandler(self.thread_container, assistant_name, assistant_id, recorder)
        self.is_used = False
        self.recorder = recorder
        self.playback = playback
        self.cancellation_handle = cancellation_handle

    def create_executor(self, tools: list[BaseTool]):
        return create_react_agent(self._get_model(), tools)

    def _get_model(self):
        return self.llm_config.get_model_wrapper().get_langchain_model()

    def get_structured_response(self, input: str, output_schema: Type[T]) -> T:
        # Handle playback mode
        if self.playback is not None:
            ret = output_schema.model_validate(next(self.playback))
            self._on_request_completed()
            return ret

        self.thread_container.add_message(
            ThreadMessage(
                id=str(uuid.uuid4()),
                ai=False,
                author_id="structured_response  ",
                author_name="structured_response",
                timestamp=int(time.time() * 1000),
                blocks=[MessageBlock(id=str(uuid.uuid4()), streaming=False, type=MessageBlockType.PLAIN, content=input)],
            )
        )
        model_with_tools = self._get_model().with_structured_output(output_schema)
        ret = cast(T, model_with_tools.invoke(input))

        # Record structured response if recorder is present
        if self.recorder is not None:
            self.recorder.record_structured(ret.model_dump())

        as_json_block = "```json\n" + json.dumps(ret.model_dump()) + "\n```"
        self.thread_container.add_message(
            ThreadMessage(
                id=str(uuid.uuid4()),
                ai=True,
                author_id=self.message_handler.assistant_id,
                author_name=self.message_handler.assistant_name,
                timestamp=int(time.time() * 1000),
                blocks=[MessageBlock(id=str(uuid.uuid4()), streaming=False, type=MessageBlockType.PLAIN, content=as_json_block)],
            )
        )
        self._on_request_completed()
        return ret

    async def execute_stream_tokens(self, user_input: Optional[str] = None, tools: List[BaseTool] = []):
        """Execute agent and yield individual tokens as they arrive.

        Gemini models have weird hickups regarding event loops and require a hack.

        See documentation of LangChainLoopManager for more details.
        """
        if self.is_used:
            raise ValueError("LangChainService is single use because of reasons")
        self.is_used = True

        try:
            if should_use_loop_manager(self.llm_config):
                logger.debug("Using loop manager for Google model in standalone context")
                async for token_data in get_langchain_loop_manager().stream_in_loop(self._execute_stream_tokens_direct(user_input, tools)):
                    yield token_data
            else:
                async for token_data in self._execute_stream_tokens_direct(user_input, tools):
                    yield token_data

        except Exception as e:
            yield {"type": "error", "error": self._handle_error(e)}
        finally:
            self._on_request_completed()

    async def _execute_stream_tokens_direct(self, user_input: Optional[str] = None, tools: List[BaseTool] = []):
        """Direct execution of stream tokens (core logic)"""
        if self.playback is not None:
            # Playback mode - yield recorded tokens
            async for token_data in self.message_handler.process_agent_token_stream(self.playback):
                # Check for cancellation even in playback mode
                if self.cancellation_handle and await self.cancellation_handle.is_cancelled():
                    self.message_handler.handle_cancellation()
                    return
                yield token_data
            return

        agent = self.create_executor(tools)
        if user_input is not None:
            self.message_handler.add_user_message(user_input, "user", "user")  # TODO proper user ids

        # Use astream_events to get individual token events
        agent_stream = agent.astream_events({"messages": self.thread_container.get_langchain_messages()}, version="v2", config=config)

        # Let MessageHandler handle the token stream processing
        async for token_data in self.message_handler.process_agent_token_stream(agent_stream):
            if self.cancellation_handle and await self.cancellation_handle.is_cancelled():
                self.message_handler.handle_cancellation()
                return
            yield token_data

    def _handle_error(self, error: Exception) -> Dict[str, str]:
        """Handle and format errors consistently."""
        error_message = extract_error_message(error)
        logger.error(f"Error executing agent: {error_message}")

        # Add error to thread container
        self.message_handler.add_error(error_message, "system")

        return {"error": error_message}

    def _on_request_completed(self):
        if self.recorder is not None:
            self.recorder.request_completed()
