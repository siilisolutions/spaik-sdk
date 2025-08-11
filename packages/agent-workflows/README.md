# Agent Workflows 🤘

**YAML-driven workflow engine for AI agents - GitHub Actions lite, on steroids!**

Agent Workflows is a minimal but badass workflow runner that parses `.agent-workflow.yml` specs, builds DAGs, and executes steps in parallel. Think GitHub Actions but simpler, faster, and more hackable.

## 🚀 Quick Start

```bash
# Install 
pip install -e .

# Run a workflow
agent-workflow run

# Or specify a custom file
agent-workflow run -f my-workflow.yml

# Validate workflow
agent-workflow validate .agent-workflow.yml

# Check run history
agent-workflow history
```

## 💾 Example Workflow

Create a `.agent-workflow.yml` file:

```yaml
name: scaffold-and-deploy
env:
  STACK: nextjs

jobs:
  generate:
    steps:
      - uses: templates/match@v0.3
        with: 
          prompt: "Slack-bot syncing Git ⇆ Notion"
      - uses: agents/smol_dev@v0.7
        with:
          language: python
      - uses: git/push@v1
        with:
          branch: main
          
  test:
    needs: generate
    steps:
      - uses: qa/run-unit-tests@v1
      - uses: qa/run-lint@v1
      
  deploy:
    needs: test
    steps:
      - uses: cloud/terraform-apply@v2
```

## 🧩 Plugin System

Plugins are Python modules that expose an `async def execute(ctx)` function:

```python
# agent_workflows/plugins/my_namespace/my_plugin.py
async def execute(ctx: dict) -> None:
    """
    ctx = {
        "env": {...},           # merged environment
        "step": {...},          # raw step dict
        "workspace": Path(...), # workspace directory
        "logger": <callable>,   # logger function
        "with": {...}           # step parameters
    }
    """
    logger = ctx['logger']
    workspace = ctx['workspace']
    step_with = ctx.get('with', {})
    
    logger("🔥 Doing something awesome...")
    # Your plugin logic here
```

## 🎯 Features

- ✅ **YAML Parsing**: Load and validate `.agent-workflow.yml` workflows
- ✅ **DAG Execution**: Topological sort with parallel job execution  
- ✅ **Plugin System**: Extensible plugin architecture
- ✅ **Async Everything**: Full async/await support
- ✅ **Error Handling**: Fail fast with proper error reporting
- ✅ **Run History**: Persistent metadata in `.agent-workflows/history/`
- ✅ **CLI Interface**: Clean command-line interface

## 🔧 Architecture

```
agent_workflows/
├── parser.py     ✅ YAML validation
├── dag.py        ✅ Topological sort + cycle detection  
├── engine.py     ✅ Async execution engine
├── cli.py        ✅ CLI commands
└── plugins/      ✅ Plugin system
    ├── git/push.py
    ├── templates/match.py
    └── agents/smol_dev.py
```

## 🧪 Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run specific test
pytest tests/test_parser.py -v

# Type checking (if mypy is available)
mypy agent_workflows/
```

## 🛠️ Workflow Schema

```yaml
name: workflow-name          # Optional: workflow name
env:                         # Optional: global environment
  KEY: value

jobs:
  job-name:
    needs: [other-job]       # Optional: dependencies
    env:                     # Optional: job-specific env
      JOB_KEY: value
    steps:
      - uses: plugin/name@version
        with:                # Optional: step parameters
          param: value
```

## 📊 CLI Commands

- `agent-workflow run [-f FILE] [-w WORKSPACE]` - Run workflow
- `agent-workflow validate FILE` - Validate workflow syntax
- `agent-workflow history [-l LIMIT]` - Show run history
- `agent-workflow --help` - Show help

## ⚡ Performance Features

- **Parallel Execution**: Jobs run in parallel when possible
- **Fast Parsing**: Minimal YAML validation overhead
- **Async Plugins**: Non-blocking plugin execution
- **Streaming Logs**: Real-time output with timestamps

## 🎤 Drop the Mic

**Agent Workflows v0.1.0 - GitHub Actions lite, on steroids!** 🎤🔥

Built with:
- Python 3.10+ async/await
- PyYAML for parsing
- Click for CLI
- Pure Python DAG implementation