from dotenv import load_dotenv

from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.tools.impl.crawl_tool_provider import CrawlToolProvider


class CrawlAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt="You are a web crawl agent. Use your crawl tool to read a page")

    def get_tool_providers(self):
        return [CrawlToolProvider()]


def test_crawl():
    agent = CrawlAgent()
    agent.run_cli()


if __name__ == "__main__":
    load_dotenv()
    test_crawl()
