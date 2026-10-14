# AGENTS.md — spaik-sdk (Python)

Read the [root AGENTS.md](../../AGENTS.md) first for architecture and product rules. This file covers working in the Python package.

The SDK should give good developer experience: fast to build proofs of concept with, and good enough quality to take to production.

## Style

- Absolute imports only; no relative or star imports.
- Always use type annotations.
- Comments are a code smell. Avoid docstrings unless they add something the code cannot say.
- Keep `__init__.py` empty unless otherwise specified.
- No inline imports, except lazy imports of optional extras (provider SDKs, server, audio, MCP).
- Small files and small functions with clear separation of concerns.
- Use `uv` for packages and `ruff` for linting.

Get a logger like this:

```python
from spaik_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)
```

## Tests

- Unit tests live at `tests/unit/{path of the file under test}/test_{filename}.py`. For example, `spaik_sdk/agent/base_agent.py` is tested in `tests/unit/spaik_sdk/agent/test_base_agent.py`. Mark them `@pytest.mark.unit` and mock external services.
- Integration tests go in `tests/integration/` with any layout. Mark them `@pytest.mark.integration`.
- Configuration is in `pyproject.toml` under `[tool.pytest.ini_options]`, and shared fixtures are in `tests/conftest.py`.
- Run them with `make test`, `make test-unit` or `make test-integration`.

Test the public interface, not the implementation. Focus on corner cases and things that can actually break, including failure paths. Coverage is not a goal. Do not write do-nothing tests like this one, which only checks that a dataclass stores its arguments:

```python
def test_valid_config_creation():
    config = LLMConfig(model=ModelRegistry.CLAUDE_HAIKU_5_5, provider_type=ProviderType.ANTHROPIC, reasoning=True)
    assert config.model == ModelRegistry.CLAUDE_HAIKU_5_5
    assert config.reasoning is True
```

## After a substantial change

After touching several files, review what you wrote for clarity, separation of concerns and leftover smells, then run:

```bash
make lint-fix && make typecheck && make test-unit
```

To add or change model presets, follow the [model-update skill](../../.agents/skills/model-update/SKILL.md).
