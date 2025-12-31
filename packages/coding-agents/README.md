# Siili Coding Agents

Pre-built coding agents for AI-assisted software development.

## Installation

```bash
pip install siili-coding-agents
```

## Agents

### Claude Code Agent

Wrapper for Claude Code SDK with streaming support.

```python
import anyio
from siili_coding_agents import ClaudeAgent, ClaudeAgentOptions

async def main():
    agent = ClaudeAgent(
        options=ClaudeAgentOptions(
            working_directory=".",
            yolo=True,  # Bypass permission prompts
        )
    )
    
    async for block in agent.stream_blocks("Create a hello world script"):
        print(block)

anyio.run(main)
```

### Synchronous Usage

```python
from siili_coding_agents import ClaudeAgent

agent = ClaudeAgent()
agent.run("Fix the bug in main.py")
```

### Cursor Agent

Integration with Cursor AI editor.

```python
from siili_coding_agents import CursorAgent

agent = CursorAgent()
result = agent.run("Refactor this function")
```

## Requirements

- Python 3.10+
- siili-ai-sdk >= 0.2.0
- Claude Code SDK (for ClaudeAgent)

## License

MIT - Copyright (c) 2025 Siili Solutions Oyj
