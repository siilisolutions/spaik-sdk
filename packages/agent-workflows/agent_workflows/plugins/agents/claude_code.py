"""Claude Code agent wrapper"""

import asyncio
from typing import Any, Dict

from siili_coding_agents import ClaudeAgent, ClaudeAgentOptions


async def execute(ctx: Dict[str, Any]) -> None:
    logger = ctx["logger"]
    _workspace = ctx["workspace"]  # kept for parity with other agents
    step_with = ctx.get("with", {})
    prompt = step_with["prompt"]

    agent = ClaudeAgent(
        options=ClaudeAgentOptions(
            working_directory=step_with.get("cwd", "."),
            yolo=True,
        )
    )

    # Collect streamed response text into a single string
    logger(f"🤖 Running agent with prompt: {prompt}")

    async for part in agent.stream_blocks(prompt):
        logger(f"🤖 {part}")

    await asyncio.sleep(0.3)
    logger("🎉 Agent completed successfully!")


