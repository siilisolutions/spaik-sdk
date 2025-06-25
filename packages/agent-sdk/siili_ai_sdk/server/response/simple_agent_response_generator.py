from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.server.response.agent_response_generator import AgentResponseGenerator


class SimpleAgentResponseGenerator(AgentResponseGenerator):
    def __init__(self, agent: BaseAgent):
        async def call_agent(agent: BaseAgent) -> None:
            await agent.get_response_async()

        super().__init__(agent, call_agent)
