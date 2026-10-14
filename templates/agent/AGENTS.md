# AGENTS.md

This project builds Python agents with [spaik-sdk](https://github.com/siilisolutions/spaik-sdk/blob/main/packages/agent-sdk/README.md) 1.x. Run `uv sync`, configure provider credentials in `.env`, then run `uv run python hello_agent.py`.

## Using spaik-sdk

- Build agents on `BaseAgent` with a `system_prompt`. Choose the model with `llm_model`: a `ModelRegistry` preset (aliases such as `sonnet` or `gpt` via `ModelRegistry.from_name`), an `LLMModel(family=..., name=...)` for a model without a preset, or a plain model ID together with `provider`. `DEFAULT_MODEL` and `MODEL_PROVIDER` set the environment default. Pass provider options in `provider_kwargs`; set `temperature` only for models without reasoning.
- `get_response()` returns an AG-UI assistant message: use `message_text(message)` or `get_response_text()` for its text. Streaming methods yield official AG-UI events.
- Add tools with LangChain `@tool` functions or a `ToolProvider`. Use `get_structured_response(prompt, Schema)` for typed output; it uses minimum reasoning unless you pass `reasoning_effort`.
- `get_cost()` returns provider-reported charges, or `None` when the provider reports none. Never hard-code prices.
- Install only the extras you use, e.g. `spaik-sdk[openai,server]`.

## Style

- Absolute imports, type annotations everywhere, no star imports.
- Comments are a code smell. Keep files and functions small.
- Use `uv` and `ruff`. After changes, run `uv run --extra dev ruff check --fix . && uv run --extra dev ty check`.
