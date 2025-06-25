from collections.abc import Awaitable, Callable
from typing import Optional, TypeVar

from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.llm.cancellation_handle import CancellationHandle
from siili_ai_sdk.server.response.response_generator import ResponseGenerator
from siili_ai_sdk.thread.thread_container import ThreadContainer

TAgent = TypeVar("TAgent", bound=BaseAgent)


class AgentResponseGenerator(ResponseGenerator):
    def __init__(self, agent: TAgent, call_agent: Callable[[TAgent], Awaitable[None]]):
        self.agent = agent
        self.call_agent = call_agent

    async def trigger_response(self, thread: ThreadContainer, cancellation_handle: Optional[CancellationHandle] = None) -> None:
        self.agent.set_thread_container(thread)
        self.agent.set_cancellation_handle(cancellation_handle)
        await self.call_agent(self.agent)
