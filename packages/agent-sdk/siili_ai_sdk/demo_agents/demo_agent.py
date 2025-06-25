from typing import List

from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.demo_agents.demo_tool import DemoTool
from siili_ai_sdk.tools.tool_provider import ToolProvider


class DemoAgent(BaseAgent):
    def get_tool_providers(self) -> List[ToolProvider]:
        return [DemoTool()]
