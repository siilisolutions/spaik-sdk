---
name: model-update
description: Discover, verify and add or retire LLM presets in the Spaik SDK model registry. Use when asked to "update models", "add new models" or refresh model aliases.
---

# Model update

Presets in `ModelRegistry` are optional shortcuts. Any model works without one, either as `LLMModel(family=..., name=...)` or as a plain ID with a provider, and family settings apply either way. A preset is worth adding for a current, commonly used model, or to record capability flags (`reasoning`, `reasoning_min_effort`, `prompt_caching`) so that its plain string ID also picks them up. Spaik keeps no price tables or per-model Azure deployment maps; costs come from provider-reported charges.

LLMs hallucinate model names. Do not skip verification.

## 1. Files

All paths are under `packages/agent-sdk/`.

| File | What to change |
| --- | --- |
| `spaik_sdk/models/model_registry.py` | `LLMModel` preset constants, and the bare aliases in `from_name` (`sonnet`, `opus`, `haiku`, `fable`, `claude`, `gpt`, `gemini flash`) |
| `spaik_sdk/models/llm_model.py` | `LLMModel` fields: `family`, `name` (exact API ID), `reasoning`, `reasoning_min_effort`, `prompt_caching` |
| `spaik_sdk/models/family_settings.py` | Translates an `LLMModel`'s fields into its family's current request shape; never checks model names |
| `spaik_sdk/models/llm_families.py` | Family constants (new provider families only) |
| `spaik_sdk/models/providers/provider_type.py` | `ProviderType`, `from_model_name` prefixes and `from_family` (new providers only) |
| `tests/unit/spaik_sdk/models/test_model_registry.py`, `test_family_settings.py` | Alias resolution and family settings |

How `family_settings.py` applies reasoning (only when `model.reasoning` is true; Anthropic always gets `max_tokens`):

- **Anthropic**: adaptive thinking with `output_config.effort` and summarized display when reasoning is on. With reasoning off, and for structured responses unless `structured_reasoning_effort` or the per-call `reasoning_effort` is set, the model's `reasoning_min_effort` applies: `"none"` disables thinking, `"between_tools"` thinks only between tool calls, and an effort level such as `"low"` (for models that cannot disable thinking, such as Opus 5.5 and Fable 5.1) keeps adaptive thinking at that effort.
- **OpenAI reasoning models**: Responses API with `reasoning.effort`. With reasoning off, it uses the model's `reasoning_min_effort`. Set this to the lowest effort the model accepts, for example `"low"` for GPT-6.1 Sol and GPT-6 Astra.
- **Google**: `thinking_level`: `high` with reasoning, otherwise the model's `reasoning_min_effort`, or `minimal` when unset (set `"low"` for models without minimal thinking, such as Pro).
- **Ollama**: passes the `reasoning` flag.

Record a model's own limits on its preset, usually `reasoning_min_effort`; never add model names to `family_settings.py`. A family is a request shape, not a vendor: when a generation's reasoning API differs meaningfully, give it its own family (a constant in `llm_families.py`, its provider in `ProviderType.from_family`, and a function in `family_settings.py`) with a test. Older generations otherwise configure reasoning through `provider_kwargs`.

## 2. Official sources

Always fetch these pages. Do not trust memory or training data.

- Anthropic: https://platform.claude.com/docs/en/models/overview
- OpenAI: https://developers.openai.com/api/docs/models/all and the per-model pages, e.g. `https://developers.openai.com/api/docs/models/<id>`; release notes at https://help.openai.com/en/articles/9624314-model-release-notes
- Google: https://ai.google.dev/gemini-api/docs/models and https://ai.google.dev/gemini-api/docs/changelog
- Azure AI Foundry: https://ai.azure.com/catalog and https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/concepts/models-from-partners

## 3. Verify each model

- [ ] The exact model ID, copied character for character from official API docs, not blog posts.
- [ ] Available in the API, not only in a consumer app or a preview CLI.
- [ ] Reasoning support, and the lowest accepted effort or thinking mode.
- [ ] Prompt caching support.
- [ ] The family it belongs to.
- [ ] Deprecation or shutdown dates for presets already in the registry. Remove retired presets and move aliases to their successors.

Do not add a model if any of these apply:

- Its ID appears only in blog posts or speculation.
- It is labelled "coming soon" or only exists in a consumer UI.
- Its version number cannot be found in the official model list.

## 4. Update docs in the same change

When aliases or the visible presets change, update the model examples in `README.md`, `packages/agent-sdk/README.md` and `AGENTS.md`. Moving a bare alias to a new model changes behaviour for users, so record it in the release notes or PR.

## 5. Check

In `packages/agent-sdk/`:

```bash
make lint-fix && make typecheck && make test-unit
```

Also confirm that:

- every new alias resolves with `ModelRegistry.from_name("alias")`,
- no model ID is duplicated, and
- when credentials are available, `scripts/smoke_providers.py` runs a minimal live call per changed provider.

## 6. Report

Tell the user:

1. Presets added: constant, API ID, reasoning behaviour and source link.
2. Alias changes.
3. Presets removed or deprecated, with dates.
4. Models whose IDs are uncertain, or that exist but are not yet in the API, and so were not added.
