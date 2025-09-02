from crawl4ai import AsyncWebCrawler

from siili_ai_sdk.tools.tool_provider import ToolProvider, tool


# NOTE: you need to run crawl4ai-setup! https://github.com/unclecode/crawl4ai
# TODO we prob want to switch to firecrawl, this seems v hacky
class CrawlToolProvider(ToolProvider):
    def get_tools(self):
        @tool
        async def crawl_web(url: str) -> str:
            """Crawl a web page and return the content in markdown format"""
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(
                    url=url,
                )
                return result.markdown

        return [crawl_web]
