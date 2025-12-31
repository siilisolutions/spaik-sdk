"""Claude Code agent plugin.

Runs Claude Code CLI agent to perform coding tasks.

with:
  prompt: <str>          # required - The task prompt
  cwd: <str>             # optional - Working directory (default: workspace)
  output_var: <str>      # optional - Variable name to store the response
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Dict

from siili_ai_sdk import MessageBlock, MessageBlockType
from siili_coding_agents import ClaudeAgent, ClaudeAgentOptions


def format_block(block: MessageBlock, logger: Callable[[str], None]) -> str | None:
    """Format a MessageBlock for display.

    Returns the content if it's a plain response, None otherwise.
    """
    if block.type == MessageBlockType.PLAIN:
        content = block.content or ""
        if content.strip():
            # Truncate very long content for display
            display = content[:500] + ("..." if len(content) > 500 else "")
            logger(f"   🤖 {display}")
        return content

    elif block.type == MessageBlockType.REASONING:
        content = block.content or ""
        if content.strip():
            # Show truncated reasoning
            display = content[:200] + ("..." if len(content) > 200 else "")
            logger(f"   🧠 {display}")
        return None

    elif block.type == MessageBlockType.TOOL_USE:
        tool_name = block.tool_name or "unknown"
        args_str = ""
        if block.tool_call_args:
            try:
                # Pretty format tool args, but keep it compact
                args_str = json.dumps(block.tool_call_args, indent=2)
                if len(args_str) > 200:
                    args_str = args_str[:200] + "..."
            except (TypeError, ValueError):
                args_str = str(block.tool_call_args)[:200]
        logger(f"   🔧 {tool_name}")
        if args_str:
            for line in args_str.split("\n")[:5]:  # Max 5 lines
                logger(f"      {line}")
        return None

    elif block.type == MessageBlockType.ERROR:
        content = block.content or "Unknown error"
        logger(f"   ❌ {content}")
        return None

    else:
        # Unknown type, just show it
        content = block.content or ""
        if content.strip():
            logger(f"   📝 {content[:200]}")
        return content


async def execute(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Claude Code agent with the given prompt.

    Returns:
        Dict with 'response' key containing the agent's final response text.
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

    # Collect response parts (only plain text responses)
    response_parts: list[str] = []

    async for block in agent.stream_blocks(prompt):
        content = format_block(block, logger)
        if content:
            response_parts.append(content)

    await asyncio.sleep(0.1)  # Allow final output to flush

    full_response = "\n".join(response_parts)
    logger(f"✅ Claude Code completed ({len(full_response)} chars)")

    # Store in context if output_var specified
    output_var = step_with.get("output_var", "claude_code_response")

    return {
        "response": full_response,
        output_var: full_response,
    }
