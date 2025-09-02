import time
from collections.abc import Callable
from typing import Any, AsyncGenerator, Dict, Optional, TypeVar

from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.llm.cancellation_handle import CancellationHandle
from siili_ai_sdk.server.response.response_generator import ResponseGenerator
from siili_ai_sdk.thread.models import ThreadEvent
from siili_ai_sdk.thread.thread_container import ThreadContainer

TAgent = TypeVar("TAgent", bound=BaseAgent)


class AgentResponseGenerator(ResponseGenerator):
    def __init__(self, agent: TAgent, call_agent: Callable[[TAgent], AsyncGenerator[ThreadEvent, None]]):
        self.agent = agent
        self.call_agent = call_agent

    async def stream_response(
        self, thread: ThreadContainer, cancellation_handle: Optional[CancellationHandle] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        self.agent.set_thread_container(thread)
        self.agent.set_cancellation_handle(cancellation_handle)

        # Stream from the agent execution
        async for event in self.call_agent(self.agent):
            if not event.is_publishable():
                continue
            yield self._convert_event(event, thread.thread_id)

    def _convert_event(self, event: ThreadEvent, thread_id: str) -> Dict[str, Any]:
        """Convert ThreadContainer event to publishable format"""

        return {
            "thread_id": thread_id,
            "event_type": event.get_event_type(),
            "timestamp": int(time.time() * 1000),
            "data": event.get_event_data(),
        }
