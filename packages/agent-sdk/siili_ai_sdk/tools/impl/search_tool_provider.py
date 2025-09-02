import os

from langchain_tavily import TavilySearch

from siili_ai_sdk.config.get_credentials_provider import credentials_provider
from siili_ai_sdk.tools.tool_provider import ToolProvider


class SearchToolProvider(ToolProvider):
    def __init__(self, max_results=10):
        self._init_env()
        self.tool = TavilySearch(max_results=max_results)

    def _init_env(self):
        os.environ["TAVILY_API_KEY"] = credentials_provider.get_provider_key("tavily")

    def get_tools(self):
        return [self.tool]
