"""General LLM agent plugin.

Runs a general-purpose LLM agent for text generation tasks.
Returns only the final response text (no reasoning or tool calls).

with:
  prompt: <str>          # required - The user prompt
  system_prompt: <str>   # optional - System prompt override
  model: <str>           # optional - Model name/alias (default: from env)
  output_var: <str>      # optional - Variable name to store the response
"""

from typing import Any, Dict

from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.models.model_registry import ModelRegistry


class GeneralAgent(BaseAgent):
    """A general-purpose agent for text generation."""

    pass


async def execute(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Execute general LLM agent with the given prompt.

    Returns:
        Dict with 'response' key containing the agent's response text only.
    """
    logger = ctx["logger"]
    step_with: Dict[str, Any] = ctx.get("with", {})

    prompt = step_with.get("prompt")
    if not prompt:
        raise ValueError("'with.prompt' is required")

    system_prompt = step_with.get(
        "system_prompt",
        "You are a helpful assistant. Provide clear, concise responses.",
    )

    # Get model from config or use default
    model_name = step_with.get("model")
    if model_name:
        try:
            model = ModelRegistry.from_name(model_name)
        except ValueError:
            logger(f"⚠️  Unknown model '{model_name}', using default")
            model = None
    else:
        model = None

    logger(f"🤖 Agent: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")

    agent = GeneralAgent(
        system_prompt=system_prompt,
        llm_model=model,
    )

    # get_response_text_async returns only the final text (no reasoning/tools)
    response = await agent.get_response_text_async(prompt)

    # Print response nicely
    logger("")
    logger("─" * 40)
    display = response[:300] + ("..." if len(response) > 300 else "")
    logger(f"🤖 {display}")
    logger("─" * 40)
    logger("")

    # Store in context if output_var specified
    output_var = step_with.get("output_var", "agent_response")

    return {
        "response": response,
        output_var: response,
    }
