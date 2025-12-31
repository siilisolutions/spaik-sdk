from typing import Dict, List, Literal, TypedDict, Union

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from siili_ai_sdk.tools.tool_provider import ToolProvider


class StdioServerConfig(TypedDict, total=False):
    transport: Literal["stdio"]
    command: str
    args: List[str]
    env: Dict[str, str]


class HttpServerConfig(TypedDict, total=False):
    transport: Literal["http"]
    url: str
    headers: Dict[str, str]


McpServerConfig = Union[StdioServerConfig, HttpServerConfig]


class McpToolProvider(ToolProvider):
    def __init__(
        self,
        servers: Dict[str, McpServerConfig],
        tools: List[BaseTool] | None = None,
    ):
        self._servers = servers
        self._tools = tools

    async def load_tools(self) -> List[BaseTool]:
        if self._tools is not None:
            return self._tools

        client = MultiServerMCPClient(self._servers)  # type: ignore[arg-type]
        self._tools = await client.get_tools()
        return self._tools

    def get_tools(self) -> List[BaseTool]:
        if self._tools is None:
            raise RuntimeError(
                "MCP tools not loaded. Call `await provider.load_tools()` first, or use `McpToolProvider.create()` async factory method."
            )
        return self._tools

    @classmethod
    async def create(cls, servers: Dict[str, McpServerConfig]) -> "McpToolProvider":
        provider = cls(servers)
        await provider.load_tools()
        return provider

    @staticmethod
    async def load_from_stdio(
        command: str,
        args: List[str] | None = None,
        env: Dict[str, str] | None = None,
    ) -> List[BaseTool]:
        server_params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env,
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await load_mcp_tools(session)


def mcp_server_stdio(
    command: str,
    args: List[str] | None = None,
    env: Dict[str, str] | None = None,
) -> StdioServerConfig:
    config: StdioServerConfig = {"transport": "stdio", "command": command, "args": args or []}
    if env:
        config["env"] = env
    return config


def mcp_server_http(
    url: str,
    headers: Dict[str, str] | None = None,
) -> HttpServerConfig:
    config: HttpServerConfig = {"transport": "http", "url": url}
    if headers:
        config["headers"] = headers
    return config
