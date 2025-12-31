"""Claude Code agent plugin.

Runs Claude Code CLI agent to perform coding tasks.

with:
  prompt: <str>          # required - The task prompt
  cwd: <str>             # optional - Working directory (default: workspace)
  output_var: <str>      # optional - Variable name to store the response
"""

import asyncio
from pathlib import Path
from typing import Any, Dict

from siili_coding_agents import ClaudeAgent, ClaudeAgentOptions


async def execute(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Claude Code agent with the given prompt.

    Returns:
        Dict with 'response' key containing the agent's full response text.
    """
    logger = ctx["logger"]
    workspace: Path = ctx["workspace"]
    step_with: Dict[str, Any] = ctx.get("with", {})

    prompt = step_with.get("prompt")
    if not prompt:
        raise ValueError("'with.prompt' is required")

    cwd = step_with.get("cwd", ".")
    working_dir = (workspace / cwd).resolve() if cwd else workspace

    logger(f"🤖 Claude Code: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    logger(f"   📁 Working directory: {working_dir}")

    agent = ClaudeAgent(
        options=ClaudeAgentOptions(
            working_directory=str(working_dir),
            yolo=True,
            verify_on_init=False,  # Skip verification - we're already in async context
        )
    )

    # Collect streamed response
    response_parts: list[str] = []

    async for block in agent.stream_blocks(prompt):
        # Log each block as it comes
        block_str = str(block)
        if block_str.strip():
            # Truncate long blocks for logging
            display = block_str[:200] + "..." if len(block_str) > 200 else block_str
            logger(f"   📝 {display}")
            response_parts.append(block_str)

    await asyncio.sleep(0.1)  # Allow final output to flush

    full_response = "\n".join(response_parts)
    logger(f"✅ Claude Code completed ({len(full_response)} chars)")

    # Store in context if output_var specified
    output_var = step_with.get("output_var", "claude_code_response")

    return {
        "response": full_response,
        output_var: full_response,
    }
