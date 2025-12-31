# Agent Workflows

YAML-driven workflow engine for AI agents.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Run workflow
agent-workflow run

# Custom file
agent-workflow run -f my-workflow.yml

# Validate
agent-workflow validate .agent-workflow.yml

# History
agent-workflow history
```

## Workflow Format

Create `.agent-workflow.yml`:

```yaml
name: my-workflow
env:
  KEY: value

jobs:
  build:
    steps:
      - uses: terminal/run@v1
        with:
          command: npm install
      - uses: agents/claude_code@v1
        with:
          prompt: "Generate unit tests"

  test:
    needs: build
    steps:
      - uses: terminal/run@v1
        with:
          command: npm test
```

## Plugins

### Built-in Plugins

- `terminal/run` - Run shell commands
- `terminal/script` - Run script files
- `git/push` - Push changes
- `git/download` - Clone repos
- `templates/match` - Template matching
- `agents/claude_code` - Claude Code agent
- `agents/smol_dev` - Smol Dev agent
- `agents/general` - General agent

### Custom Plugins

Create `agent_workflows/plugins/my_namespace/my_plugin.py`:

```python
async def execute(ctx: dict) -> None:
    logger = ctx['logger']
    workspace = ctx['workspace']
    params = ctx.get('with', {})
    
    logger("Running my plugin...")
    # Plugin logic
```

## Features

- DAG execution with parallel jobs
- Environment variable inheritance
- Run history tracking
- Async plugin system
- Fail-fast error handling

## CLI Commands

| Command | Description |
|---------|-------------|
| `run [-f FILE] [-w WORKSPACE]` | Run workflow |
| `validate FILE` | Validate syntax |
| `history [-l LIMIT]` | Show history |

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT - Copyright (c) 2025 Siili Solutions Oyj
