import time
from typing import List

from langchain_core.tools import BaseTool, tool

from siili_ai_sdk.tools.tool_provider import ToolProvider
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class DemoTool(ToolProvider):
    def get_tools(self) -> List[BaseTool]:
        @tool
        def get_secret_greeting() -> str:
            """Returns the users secret greeting."""
            logger.debug("Getting secret greeting...")
            time.sleep(1)
            return "kikkelis kokkelis"

        @tool
        def get_user_name() -> str:
            """Returns the users name."""
            logger.debug("Getting user name...")
            time.sleep(1)
            return "Seppo Hovi"

        return [get_secret_greeting, get_user_name]
