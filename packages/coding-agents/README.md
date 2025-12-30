# Siili Coding Agents

Pre-built coding agents powered by [siili-ai-sdk](https://pypi.org/project/siili-ai-sdk/) for AI-assisted software development.

## Features

- **Claude Code Agent**: Wrapper for Claude Code SDK with streaming support
- **Cursor Agent**: Integration with Cursor AI editor
- **SDK Integration**: Built on siili-ai-sdk for consistent streaming and message handling

## Installation

```bash
pip install siili-coding-agents
```

## Quick Start

### Claude Code Agent

```python
import anyio
from siili_coding_agents import ClaudeAgent, ClaudeCodeOptions

async def main():
    agent = ClaudeAgent(
        options=ClaudeCodeOptions(cwd="."),
        yolo=True  # Bypass permission prompts
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

## Requirements

- Python 3.10+
- [siili-ai-sdk](https://pypi.org/project/siili-ai-sdk/) >= 0.2.0
- Claude Code SDK

## License

MIT License - Copyright (c) 2025 Siili Solutions Oyj

