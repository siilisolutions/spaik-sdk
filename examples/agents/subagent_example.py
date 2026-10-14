"""Delegates work to a subagent from inside a tool.

`spawn()` runs the subagent in its own thread container, so its tool calls stay out of the
parent agent's transcript.

Run from this directory with `uv run python subagent_example.py`.
"""

from dotenv import load_dotenv
from spaik_sdk import BaseAgent, message_text
from spaik_sdk.tools.tool_provider import BaseTool, ToolProvider, tool

POLICIES = {
    "returns": "Unused items can be returned within 30 days of delivery for a full refund.",
    "shipping": "Orders ship within 2 business days. Delivery inside the EU takes 3 to 5 business days.",
    "warranty": "Electronics carry a 24-month warranty covering manufacturing defects.",
}


@tool
def read_policy(topic: str) -> str:
    """Read a customer policy. Known topics: returns, shipping, warranty."""
    return POLICIES.get(topic.lower(), f"No policy found for '{topic}'. Known topics: {', '.join(POLICIES)}.")


class PolicyResearcher(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            system_prompt="Answer questions about company policy using only the read_policy tool. Quote the policy you relied on.",
            tools=[read_policy],
        )


class ResearchTools(ToolProvider):
    def get_tools(self) -> list[BaseTool]:
        @tool
        def research_policy(question: str) -> str:
            """Ask the policy researcher a question about returns, shipping or warranty."""
            return message_text(PolicyResearcher().spawn(question))

        return [research_policy]


class SupportAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            system_prompt="You are a customer support agent. Use research_policy to check policy before answering.",
            tool_providers=[ResearchTools()],
        )


def main() -> None:
    agent = SupportAgent()
    print(agent.get_response_text("My headphones broke after 14 months and I want to send them back. What are my options?"))

    parent_tool_calls = [
        call.function.name
        for message in agent.thread_container.messages
        if message.role == "assistant"
        for call in message.tool_calls or []
    ]
    print(f"\nTool calls in the support agent's thread: {parent_tool_calls}")


if __name__ == "__main__":
    load_dotenv()
    main()
