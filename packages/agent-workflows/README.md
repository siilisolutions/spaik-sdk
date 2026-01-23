# Agent Workflows

YAML-driven workflow engine for AI agents.

Spaik SDK is an open-source project developed by engineers at Siili Solutions Oyj. This is not an official Siili product.

## Installation

```bash
# Install globally with uvx (recommended)
uvx siili-agent-workflows --help

# Or install with pip
pip install siili-agent-workflows

# Or install locally for development
cd packages/agent-workflows
uv sync
```

## Quick Start

```bash
# Run a workflow by name
siili-agent-workflows my-workflow --param value

# List all available workflows
siili-agent-workflows --list

# Validate a workflow without running
siili-agent-workflows my-workflow --validate

# Show help
siili-agent-workflows --help
```

## Workflow Discovery

Workflows are discovered from multiple locations (in order):

1. **Current directory**: `./workflow-name.yml`, `./workflow-name.yaml`, etc.
2. **Local workflows dir**: `./.agent_workflows/workflow-name.yml`
3. **Global config**: `~/.config/siili-agent-workflows/workflow-name.yml`
4. **Bundled**: Workflows shipped with the package

Supported extensions: `.yml`, `.yaml`, `.agent-workflow.yml`, `.agent-workflow.yaml`

## Environment Variables

Environment files are loaded in order (later overrides earlier):

1. `~/.config/siili-agent-workflows/.env` (global)
2. `./.env` (current directory)
3. `--env-file <path>` (explicit)

## Workflow Format

Create `my-workflow.yml`:

```yaml
name: my-workflow
env:
  API_KEY: ${{ env.MY_API_KEY }}

vars:
  project_name: my-project

jobs:
  setup:
    steps:
      - uses: terminal/run
        with:
          command: npm install

  generate:
    needs: setup
    steps:
      - uses: agents/claude_code
        with:
          prompt: "Create a README for ${{ vars.project_name }}"
          cwd: "."

  test:
    needs: generate
    steps:
      - uses: terminal/run
        with:
          command: npm test
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--list` | List available workflows |
| `--validate` | Validate workflow without running |
| `--env-file PATH` | Load environment from file |
| `-w, --workspace DIR` | Set workspace directory |
| `--set PLUGIN.KEY=VALUE` | Override step values |
| `--var KEY=VALUE` | Set workflow variables |
| `--dest PATH` | Shorthand for git/download.dest |

You can also pass variables as positional args:

```bash
siili-agent-workflows apply-template --template agent --path ./my-agent
```

## Built-in Plugins

### Terminal

```yaml
# Run shell commands
- uses: terminal/run
  with:
    command: "echo hello"
    shell: true              # optional, default true
    continue_on_error: false # optional
    timeout: 30              # optional, seconds

# Run scripts
- uses: terminal/script
  with:
    path: "./scripts/setup.sh"
    args: ["--verbose"]      # optional
    interpreter: "/bin/bash" # optional
    cwd: "."                 # optional
```

### Git

```yaml
# Clone/download from repository
- uses: git/download
  with:
    repo: "https://github.com/user/repo.git"
    ref: "main"              # optional branch/tag
    files:                   # optional, specific files/dirs
      - "templates/agent"
    dest: "./output"         # destination directory

# Push changes
- uses: git/push
  with:
    message: "chore: automated update"
    branch: "main"           # optional
```

### Agents

```yaml
# Claude Code agent (requires ANTHROPIC_API_KEY)
- uses: agents/claude_code
  with:
    prompt: "Implement feature X"
    cwd: "."                 # working directory

# General LLM agent (returns text response only)
- uses: agents/general
  with:
    prompt: "Analyze this code"
    system_prompt: "You are a code reviewer"  # optional
    output_var: analysis     # variable to store response

# Structured JSON response
- uses: agents/structured
  with:
    prompt: "Extract topics from this text: ..."
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
```

### Audio (Speech)

```yaml
# Speech-to-text recording
- uses: audio/stt
  with:
    language: "en"           # optional
    output_var: "user_input" # variable to store result

# Text-to-speech
- uses: audio/tts
  with:
    text: "Hello, world!"
    voice: "alloy"           # optional
    output: "./output.mp3"   # optional
```

## Variable Interpolation

Supports two syntaxes:

```yaml
# GitHub Actions style
prompt: "${{ vars.name }} - ${{ env.API_KEY }}"

# Python format style
prompt: "{name} - {API_KEY}"
```

## Custom Plugins

Create `agent_workflows/plugins/my_namespace/my_plugin.py`:

```python
from typing import Any, Dict

async def execute(ctx: Dict[str, Any]) -> Dict[str, Any]:
    logger = ctx['logger']
    workspace = ctx['workspace']
    params = ctx.get('with', {})
    
    logger("Running my plugin...")
    
    # Do work...
    result = "some output"
    
    # Return values are available to subsequent steps
    return {"output": result}
```

## Features

- **Parallel Execution**: Jobs without dependencies run concurrently
- **DAG Support**: Declare dependencies with `needs:`
- **Variable Interpolation**: Use `${{ vars.x }}` or `{x}` syntax
- **Environment Inheritance**: Global → Job → Step
- **Run History**: Track execution history in `.agent-workflows/history/`
- **Fail-fast**: Stop on first error (configurable per step)

## Development

```bash
cd packages/agent-workflows
uv sync --dev
uv run pytest tests/
uv run ruff check .
uv run ty check agent_workflows
```

## License

MIT - Copyright (c) 2025 Siili Solutions Oyj
