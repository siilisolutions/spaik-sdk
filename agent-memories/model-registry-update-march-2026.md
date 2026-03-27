# Model Registry Update - March 2026

## Files involved in model updates
- `packages/agent-sdk/spaik_sdk/models/model_registry.py` — model definitions + aliases
- `packages/agent-sdk/spaik_sdk/models/providers/azure_provider.py` — Azure deployment env var mappings
- `packages/agent-sdk/spaik_sdk/llm/cost/builtin_cost_provider.py` — pricing per model
- `packages/agent-sdk/tests/unit/spaik_sdk/models/test_model_registry.py` — registry tests
- `packages/agent-sdk/tests/unit/spaik_sdk/models/factories/test_openai_factory.py` — OpenAI factory tests
- `packages/agent-sdk/tests/unit/spaik_sdk/models/factories/test_google_factory.py` — Google factory tests
- `packages/agent-sdk/tests/unit/spaik_sdk/agent/test_base_agent.py` — agent tests (uses recordings!)
- `packages/agent-sdk/tests/integration/test_cost_tracking_integration.py` — cost tracking tests

## Important notes
- Base agent tests use pre-recorded API responses. New models need recordings before they can be in parametrized agent tests.
- Tests run with: `uv run python3 -m pytest tests/unit/ -m "unit" --no-cov`
- Working directory is already `packages/agent-sdk` (not the repo root)
- Cost provider uses startswith() matching; order matters (e.g., gemini-3.1-flash-lite must come before gemini-3-flash)
- GPT-5 base models use reasoning_min_effort="minimal", GPT-5.1+ default to "none"