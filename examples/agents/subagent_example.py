"""
Demonstrates spawning a nested agent from inside a tool without leaking
the parent agent's LangChain callback context.

Without isolation the subagent's tool calls bleed into the parent thread.
With spawn() they stay inside the subagent's own ThreadContainer.

Run:
    uv run python examples/agents/subagent_example.py
"""

from dotenv import load_dotenv

from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.thread.models import MessageBlockType
from spaik_sdk.tools.tool_provider import BaseTool, ToolProvider, tool


class EchoTools(ToolProvider):
    def get_tools(self) -> list[BaseTool]:
        @tool
        def echo(message: str) -> str:
            """Echo the message back."""
            return message

        return [echo]


class SubAgent(BaseAgent):
    def get_tool_providers(self) -> list[ToolProvider]:
        return [EchoTools()]


class SpawnTools(ToolProvider):
    def get_tools(self) -> list[BaseTool]:
        @tool
        def spawn_sub(task: str) -> str:
            """Delegate a task to a subagent that echoes the message."""
            sub = SubAgent(system_prompt="Use the echo tool to echo the message exactly.")
            msg = sub.spawn(task)
            return msg.get_text_content()

        return [spawn_sub]


class MainAgent(BaseAgent):
    def get_tool_providers(self) -> list[ToolProvider]:
        return [SpawnTools()]


def main() -> None:
    agent = MainAgent(system_prompt="Use spawn_sub to delegate tasks.")
    response = agent.get_response("Spawn a subagent that echoes: hello world")

    parent_tool_names = [
        b.tool_name
        for b in response.blocks
        if b.type == MessageBlockType.TOOL_USE and b.tool_name is not None
    ]
    print(f"Parent thread tool calls: {parent_tool_names}")
    print("  -> should only contain ['spawn_sub'], not 'echo'")

    assert parent_tool_names == ["spawn_sub"], (
        f"Expected only ['spawn_sub'] but got {parent_tool_names}. "
        "The subagent's tool calls leaked into the parent thread."
    )
    print("\nAll good — subagent context isolated correctly.")


if __name__ == "__main__":
    load_dotenv()
    main()
