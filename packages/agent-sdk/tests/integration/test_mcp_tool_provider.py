import pytest

from spaik_sdk.tools.impl.mcp_tool_provider import (
    McpToolProvider,
    mcp_server_stdio,
)


@pytest.mark.integration
async def test_mcp_tool_provider_loads_tools_from_echo_server():
    servers = {
        "echo": mcp_server_stdio(
            command="echo-mcp-server-for-testing",
        ),
    }
    provider = await McpToolProvider.create(servers)
    tools = provider.get_tools()

    assert len(tools) > 0
    tool_names = [t.name for t in tools]
    assert "echo_tool" in tool_names


@pytest.mark.integration
async def test_mcp_tool_provider_can_call_echo_tool():
    servers = {
        "echo": mcp_server_stdio(
            command="echo-mcp-server-for-testing",
        ),
    }
    provider = await McpToolProvider.create(servers)
    tools = provider.get_tools()

    echo_tool = next(t for t in tools if t.name == "echo_tool")
    result = await echo_tool.ainvoke({"message": "hello world"})  # type: ignore[missing-typed-dict-key,invalid-key]
    assert "hello world" in str(result)


@pytest.mark.integration
async def test_mcp_tool_provider_load_from_stdio():
    tools = await McpToolProvider.load_from_stdio(
        command="echo-mcp-server-for-testing",
    )

    assert len(tools) > 0
    tool_names = [t.name for t in tools]
    assert "echo_tool" in tool_names


@pytest.mark.integration
async def test_mcp_tool_provider_get_tools_raises_if_not_loaded():
    servers = {"echo": mcp_server_stdio(command="echo-mcp-server-for-testing")}
    provider = McpToolProvider(servers)

    with pytest.raises(RuntimeError, match="MCP tools not loaded"):
        provider.get_tools()


@pytest.mark.integration
async def test_mcp_tool_provider_load_tools_async():
    servers = {"echo": mcp_server_stdio(command="echo-mcp-server-for-testing")}
    provider = McpToolProvider(servers)

    tools = await provider.load_tools()
    assert len(tools) > 0

    same_tools = provider.get_tools()
    assert tools == same_tools
