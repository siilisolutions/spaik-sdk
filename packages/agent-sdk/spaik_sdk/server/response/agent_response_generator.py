import time
from collections.abc import Callable
from typing import Any, AsyncGenerator, Dict, Optional, TypeVar

from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.llm.cancellation_handle import CancellationHandle
from spaik_sdk.server.response.response_generator import OnCheckpoint, ResponseGenerator
from spaik_sdk.thread.models import MessageFullyAddedEvent, ThreadEvent, ToolResponseReceivedEvent
from spaik_sdk.thread.thread_container import ThreadContainer
from spaik_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)

TAgent = TypeVar("TAgent", bound=BaseAgent)

_CHECKPOINT_EVENT_TYPES = (ToolResponseReceivedEvent, MessageFullyAddedEvent)


class AgentResponseGenerator(ResponseGenerator):
    def __init__(self, agent: TAgent, call_agent: Callable[[TAgent], AsyncGenerator[ThreadEvent, None]]):
        self.agent = agent
        self.call_agent = call_agent

    async def stream_response(
        self,
        thread: ThreadContainer,
        cancellation_handle: Optional[CancellationHandle] = None,
        on_checkpoint: OnCheckpoint = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        self.agent.set_thread_container(thread)
        self.agent.set_cancellation_handle(cancellation_handle)

        async for event in self.call_agent(self.agent):
            if on_checkpoint and isinstance(event, _CHECKPOINT_EVENT_TYPES):
                try:
                    await on_checkpoint()
                except Exception:
                    logger.exception("Checkpoint failed; stream continues")
            if not event.is_publishable():
                continue
            yield self._convert_event(event, thread.thread_id)

    def _convert_event(self, event: ThreadEvent, thread_id: str) -> Dict[str, Any]:
        return {
            "thread_id": thread_id,
            "event_type": event.get_event_type(),
            "timestamp": int(time.time() * 1000),
            "data": event.get_event_data(),
        }
