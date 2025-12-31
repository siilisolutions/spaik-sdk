"""Structured response agent plugin.

Runs an LLM to get a structured JSON response matching a schema.

with:
  prompt: <str>          # required - The user prompt
  schema: <dict>         # required - JSON schema for the response
  system_prompt: <str>   # optional - System prompt override
  model: <str>           # optional - Model name/alias (default: from env)
  output_var: <str>      # optional - Variable name to store the response

Example usage in workflow:
  - uses: agents/structured
    with:
      prompt: "Extract the main topics from this text: ..."
      schema:
        type: object
        properties:
          topics:
            type: array
            items:
              type: string
          summary:
            type: string
        required:
          - topics
          - summary
      output_var: extracted_data
"""

import json
from typing import Any, Dict, Type

from pydantic import BaseModel, create_model
from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.models.model_registry import ModelRegistry


class StructuredAgent(BaseAgent):
    """Agent for structured responses."""

    pass


def schema_to_pydantic(schema: Dict[str, Any], name: str = "DynamicModel") -> Type[BaseModel]:
    """Convert a JSON schema dict to a Pydantic model.

    Supports basic types: string, integer, number, boolean, array, object.
    """
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    field_definitions: Dict[str, Any] = {}

    for field_name, field_schema in properties.items():
        field_type = field_schema.get("type", "string")

        # Map JSON schema types to Python types
        if field_type == "string":
            py_type = str
        elif field_type == "integer":
            py_type = int
        elif field_type == "number":
            py_type = float
        elif field_type == "boolean":
            py_type = bool
        elif field_type == "array":
            item_type = field_schema.get("items", {}).get("type", "string")
            if item_type == "string":
                py_type = list[str]
            elif item_type == "integer":
                py_type = list[int]
            elif item_type == "number":
                py_type = list[float]
            else:
                py_type = list[Any]
        elif field_type == "object":
            py_type = dict[str, Any]
        else:
            py_type = Any

        # Handle optional vs required
        if field_name in required:
            field_definitions[field_name] = (py_type, ...)
        else:
            field_definitions[field_name] = (py_type | None, None)

    return create_model(name, **field_definitions)


async def execute(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Execute structured response agent.

    Returns:
        Dict with 'response' as the parsed dict and the output_var.
    """
    logger = ctx["logger"]
    step_with: Dict[str, Any] = ctx.get("with", {})

    prompt = step_with.get("prompt")
    if not prompt:
        raise ValueError("'with.prompt' is required")

    schema = step_with.get("schema")
    if not schema:
        raise ValueError("'with.schema' is required")

    system_prompt = step_with.get(
        "system_prompt",
        "You are a helpful assistant that provides structured responses.",
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

    logger(f"📊 Structured: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")

    agent = StructuredAgent(
        system_prompt=system_prompt,
        llm_model=model,
    )

    # Convert schema to Pydantic model
    response_model = schema_to_pydantic(schema)

    # Get structured response
    result = await agent.get_structured_response_async(prompt, response_model)

    # Convert to dict
    response_dict = result.model_dump()

    # Pretty print
    logger("")
    logger("─" * 40)
    logger("📊 Structured Response:")
    formatted = json.dumps(response_dict, indent=2)
    for line in formatted.split("\n")[:15]:  # Max 15 lines
        logger(f"   {line}")
    if len(formatted.split("\n")) > 15:
        logger("   ...")
    logger("─" * 40)
    logger("")

    # Store in context
    output_var = step_with.get("output_var", "structured_response")

    return {
        "response": response_dict,
        output_var: response_dict,
    }
