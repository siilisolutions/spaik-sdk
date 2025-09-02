from typing import AsyncGenerator

from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.server.response.agent_response_generator import AgentResponseGenerator
from siili_ai_sdk.thread.models import ThreadEvent


class SimpleAgentResponseGenerator(AgentResponseGenerator):
    def __init__(self, agent: BaseAgent):
        async def call_agent(agent: BaseAgent) -> AsyncGenerator[ThreadEvent, None]:
            async for event in agent.get_event_stream():
                yield event

        super().__init__(agent, call_agent)
