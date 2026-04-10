"""
Subagent example: orchestrator delegates focused tasks to isolated subagents.

Demonstrates:
- A SubAgent with its own tools and system prompt
- A MainAgent that spawns subagents via a tool
- The _run_isolated() helper that prevents LangChain callback ContextVars
  from leaking the subagent's tool calls into the main thread stream.

The leak occurs because asyncio.run() copies the calling coroutine's
ContextVar context, which includes LangChain's internal callback handlers.
Running in a new thread with a fresh contextvars.Context() prevents this.

See: SUBAGENT_ISOLATION.md in the repo root for details and SDK-level options.
"""
import asyncio
import contextvars
import threading

from dotenv import load_dotenv

from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.tools.tool_provider import BaseTool, ToolProvider, tool


# ── Isolation helper ──────────────────────────────────────────────────────────

def run_isolated(coro):
    """Run a coroutine in a new thread with a blank ContextVar context.

    Use this instead of asyncio.run() when running a nested BaseAgent from
    inside a tool call. Without this, LangChain's callback ContextVars are
    inherited and the subagent's tool_use blocks appear in the main thread stream.
    """
    result: list = []
    error: list = []

    def _thread():
        ctx = contextvars.Context()  # no inherited ContextVars
        try:
            ctx.run(lambda: result.append(asyncio.run(coro)))
        except Exception as exc:
            error.append(exc)

    t = threading.Thread(target=_thread)
    t.start()
    t.join()
    if error:
        raise error[0]
    return result[0]


# ── SubAgent ──────────────────────────────────────────────────────────────────

class ResearchTools(ToolProvider):
    """Toy research tools for the subagent."""

    def get_tools(self) -> list[BaseTool]:
        @tool
        def lookup(topic: str) -> str:
            """Look up a fact about a topic (stub — replace with real web/DB call)."""
            facts = {
                "python": "Python is a high-level, interpreted programming language.",
                "asyncio": "asyncio is Python's standard library for async I/O.",
                "langchain": "LangChain is a framework for building LLM applications.",
            }
            return facts.get(topic.lower(), f"No fact found for '{topic}'.")

        return [lookup]


class ResearchSubAgent(BaseAgent):
    def get_tool_providers(self) -> list[ToolProvider]:
        return [ResearchTools()]


# ── Orchestrator ──────────────────────────────────────────────────────────────

class SpawnTools(ToolProvider):
    """Gives the orchestrator a spawn_subagent tool."""

    def get_tools(self) -> list[BaseTool]:
        @tool
        def spawn_subagent(task: str) -> str:
            """Spawn a focused subagent to research a single topic.

            The subagent runs in complete isolation — its tool calls do not
            appear in the main thread stream."""
            subagent = ResearchSubAgent(
                system_prompt=(
                    "You are a focused research subagent. "
                    "Use the lookup tool to answer the given question, "
                    "then return a concise answer."
                )
            )
            message = run_isolated(subagent.get_response_async(task))
            return message.get_text_content()

        return [spawn_subagent]


class OrchestratorAgent(BaseAgent):
    def get_tool_providers(self) -> list[ToolProvider]:
        return [SpawnTools()]


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    load_dotenv()

    orchestrator = OrchestratorAgent(
        system_prompt=(
            "You are an orchestrator. When asked a question, use spawn_subagent "
            "to delegate the research. Summarise the findings in your reply."
        )
    )

    response = orchestrator.get_response_text(
        "What is Python and what is asyncio? Use one subagent per question."
    )

    print("\n=== Orchestrator response ===")
    print(response)

    print("\n=== Main thread tool blocks ===")
    for msg in orchestrator.thread_container.messages:
        for block in msg.blocks:
            if block.type.value == "tool_use":
                print(f"  [{block.tool_name}]  (should only see spawn_subagent here)")
