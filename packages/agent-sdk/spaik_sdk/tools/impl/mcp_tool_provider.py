from typing import Dict, List, Literal, Mapping, TypedDict, Union, cast

from langchain_core.tools import BaseTool

from spaik_sdk.tools.tool_provider import ToolProvider


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
        servers: Mapping[str, McpServerConfig],
        tools: List[BaseTool] | None = None,
    ):
        self._servers = servers
        self._tools = tools

    async def load_tools(self) -> List[BaseTool]:
        if self._tools is not None:
            return self._tools

        tools: List[BaseTool] = []
        for config in self._servers.values():
            tools.extend(await _load_server_tools(config))
        self._tools = tools
        return tools

    def get_tools(self) -> List[BaseTool]:
        if self._tools is None:
            raise RuntimeError(
                "MCP tools not loaded. Call `await provider.load_tools()` first, or use `McpToolProvider.create()` async factory method."
            )
        return self._tools

    @classmethod
    async def create(cls, servers: Mapping[str, McpServerConfig]) -> "McpToolProvider":
        provider = cls(servers)
        await provider.load_tools()
        return provider

    @staticmethod
    async def load_from_stdio(
        command: str,
        args: List[str] | None = None,
        env: Dict[str, str] | None = None,
    ) -> List[BaseTool]:
        return await _load_server_tools(mcp_server_stdio(command, args, env))


async def _load_server_tools(config: McpServerConfig) -> List[BaseTool]:
    from fastmcp.client.transports import ClientTransport, StdioTransport, StreamableHttpTransport
    from langchain_core._api import suppress_langchain_beta_warning

    with suppress_langchain_beta_warning():
        from langchain.mcp import MCPAdapter

    transport: ClientTransport
    if config.get("transport") == "http":
        http = cast(HttpServerConfig, config)
        transport = StreamableHttpTransport(http["url"], headers=http.get("headers"))
    else:
        stdio = cast(StdioServerConfig, config)
        transport = StdioTransport(stdio["command"], stdio.get("args", []), env=stdio.get("env"))
    # One adapter per server keeps MCP tool names unprefixed
    return await MCPAdapter(transport).list_tools()


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
