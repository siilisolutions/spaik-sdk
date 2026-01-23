from typing import AsyncGenerator

from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.server.response.agent_response_generator import AgentResponseGenerator
from spaik_sdk.thread.models import ThreadEvent


class SimpleAgentResponseGenerator(AgentResponseGenerator):
    def __init__(self, agent: BaseAgent):
        async def call_agent(agent: BaseAgent) -> AsyncGenerator[ThreadEvent, None]:
            async for event in agent.get_event_stream():
                yield event

        super().__init__(agent, call_agent)
