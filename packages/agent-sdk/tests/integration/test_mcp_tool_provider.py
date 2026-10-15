import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterator

import pytest

from spaik_sdk.tools.impl.mcp_tool_provider import (
    McpToolProvider,
    mcp_server_http,
    mcp_server_stdio,
)

ECHO_SERVER = [str(Path(__file__).with_name("echo_mcp_server.py"))]


def echo_server(env: dict[str, str] | None = None):
    return mcp_server_stdio(command=sys.executable, args=ECHO_SERVER, env=env)


def _accepts_connections(port: int) -> bool:
    with socket.socket() as client:
        return client.connect_ex(("127.0.0.1", port)) == 0


@pytest.fixture
def http_echo_url() -> Iterator[str]:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    process = subprocess.Popen([sys.executable, *ECHO_SERVER, str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 15
        while not _accepts_connections(port):
            if time.monotonic() > deadline:
                raise TimeoutError("HTTP echo server did not start")
            time.sleep(0.1)
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.mark.integration
async def test_mcp_tool_provider_loads_tools_from_echo_server():
    servers = {
        "echo": echo_server(),
    }
    provider = await McpToolProvider.create(servers)
    tools = provider.get_tools()

    assert len(tools) > 0
    tool_names = [t.name for t in tools]
    assert "echo_tool" in tool_names


@pytest.mark.integration
async def test_mcp_tool_provider_can_call_echo_tool():
    servers = {
        "echo": echo_server(),
    }
    provider = await McpToolProvider.create(servers)
    tools = provider.get_tools()

    echo_tool = next(t for t in tools if t.name == "echo_tool")
    result = await echo_tool.ainvoke({"message": "hello world"})
    assert "hello world" in str(result)


@pytest.mark.integration
async def test_mcp_tool_provider_load_from_stdio():
    tools = await McpToolProvider.load_from_stdio(command=sys.executable, args=ECHO_SERVER)

    assert len(tools) > 0
    tool_names = [t.name for t in tools]
    assert "echo_tool" in tool_names


@pytest.mark.integration
async def test_mcp_tool_provider_get_tools_raises_if_not_loaded():
    servers = {"echo": echo_server()}
    provider = McpToolProvider(servers)

    with pytest.raises(RuntimeError, match="MCP tools not loaded"):
        provider.get_tools()


@pytest.mark.integration
async def test_mcp_tool_provider_load_tools_async():
    servers = {"echo": echo_server()}
    provider = McpToolProvider(servers)

    tools = await provider.load_tools()
    assert len(tools) > 0

    same_tools = provider.get_tools()
    assert tools == same_tools


@pytest.mark.integration
async def test_mcp_stdio_server_receives_configured_env():
    provider = await McpToolProvider.create({"echo": echo_server(env={"SECRET_KEY": "s3cret"})})
    echo_tool = next(t for t in provider.get_tools() if t.name == "echo_tool")
    assert "SECRET_KEY is: s3cret" in str(await echo_tool.ainvoke({"message": "hi"}))


@pytest.mark.integration
async def test_tools_from_several_servers_keep_their_names():
    provider = await McpToolProvider.create({"first": echo_server(), "second": echo_server()})
    assert [t.name for t in provider.get_tools()] == ["echo_tool", "echo_tool"]


@pytest.mark.integration
async def test_mcp_tool_provider_calls_http_server(http_echo_url: str):
    provider = await McpToolProvider.create({"echo": mcp_server_http(http_echo_url, headers={"X-Test": "1"})})
    echo_tool = next(t for t in provider.get_tools() if t.name == "echo_tool")
    assert "Tool echo: over http" in str(await echo_tool.ainvoke({"message": "over http"}))
