import os
import sys

from mcp.server.mcpserver import MCPServer

server = MCPServer("Echo Server")


@server.tool()
async def echo_tool(message: str) -> str:
    """Echo a message as a tool"""
    return f"Tool echo: {message}. SECRET_KEY is: {os.getenv('SECRET_KEY', 'unset')}"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        server.run("streamable-http", host="127.0.0.1", port=int(sys.argv[1]))
    else:
        server.run()
