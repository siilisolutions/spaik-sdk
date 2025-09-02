from dotenv import load_dotenv

from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.tools.impl.search_tool_provider import SearchToolProvider


class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt="You are a search agent. You will use the search tool to find information.")

    def get_tool_providers(self):
        return [SearchToolProvider()]


def test_search():
    agent = SearchAgent()
    agent.run_cli()


if __name__ == "__main__":
    load_dotenv()
    test_search()
