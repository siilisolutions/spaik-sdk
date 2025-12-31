# Agent SDK

**Build AI agent POCs that scale to production in minutes, not months.**

The Agent SDK is designed around one core principle: making it *ridiculously fast* to build agentic AI solutions that work in production. Not just demos, not just prototypes - actual production-grade systems that deliver business value.

## The Problem

Building AI agents is easy. Building AI agents that work reliably in production is hard. Really hard.

You've got model provider differences, streaming complexities, tool orchestration nightmares, state management, persistence, authentication, error handling, testing... The list goes on. Most of these problems are invisible until you try to put your POC in front of real users.

## The Solution

Hide all that complexity behind a clean, convention-over-configuration API. Give you production-ready infrastructure out of the box, but let you customize everything when you need to.

**Hello World:**
```python
from siili_ai_sdk.agent.base_agent import BaseAgent

class HelloAgent(BaseAgent):
    pass

agent = HelloAgent(system_prompt="You are a helpful assistant")
print(agent.get_response_text("Hello!"))
```

**Production-ready in one more step:**
```python
# Add FastAPI server + streaming + persistence + auth
api_builder = ApiBuilder.local(agent=agent)
app.include_router(api_builder.build_thread_router())
```

## What It Actually Does

### Backend (Python SDK)
- **Multi-LLM Support**: Seamlessly switch between OpenAI, Anthropic, Google, Azure
- **Response Harmonization**: Tool calls, reasoning, streaming - all work identically across providers
- **Production Infrastructure**: FastAPI servers, persistence, auth, error handling built-in
- **Streaming Made Easy**: Real-time responses with proper cancellation support
- **Serverless-First**: Works perfectly in cloud functions and serverless environments
- **Testing & Debugging**: Record/playback LLM responses, built-in tracing, CLI tools

### Frontend (React Hooks)
- **Drop-in Chat UI**: Complete state management for chat interfaces
- **Real-time Streaming**: WebSocket reconnection, error handling, all handled
- **Type Safety**: Full TypeScript support with Zod validation
- **Production Ready**: Built for complex serverless deployments

## Structure

```
agent-sdk/
├── packages/
│   ├── agent-sdk/          # Core Python SDK
│   └── agent-sdk-hooks/    # React hooks for frontend integration
└── examples/
    ├── agents/             # Simple Python examples
    ├── backend/            # FastAPI backend examples
    └── frontend/           # React frontend examples
```

## Quick Start

### Prerequisites
- Python 3.10+
- Bun 1.0+
- uv (Python package manager)

### Setup
```bash
# Python dependencies
cd examples/backend && uv sync

# TypeScript dependencies (do this in project root)
bun install
```

### Run Full Stack Example
```bash
# Terminal 1: Backend
cd examples/backend
uv run uvicorn main:app --reload

# Terminal 2: Frontend
cd examples/frontend  
bun run dev
```

Visit `http://localhost:5173` for a full-featured chat interface.

## Key Features

### Convention Over Configuration
- Zero setup for local development
- Sane defaults for everything
- Easy to override when you need control

### Model Provider Abstraction
- Identical API across all providers
- Easy model switching and A/B testing
- Handles provider-specific quirks automatically

### Production-Ready Infrastructure
- Built-in persistence layer
- Authentication and authorization
- Rate limiting and error handling
- Serverless-friendly architecture

### Developer Experience
- Excellent TypeScript/Python typing
- Built-in debugging and tracing tools
- CLI helpers for local testing
- Comprehensive test automation support

## Documentation

- **[Python SDK](packages/agent-sdk/README.md)** - Core agent functionality
- **[React Hooks](packages/agent-sdk-hooks/README.md)** - Frontend integration
- **[Examples](examples/)** - Working examples for all use cases

## VSCode imports
If your python imports when viewing for example main.py show red lines under try adding the `./examples/backend/.venv/bin/python` to python interpreters by pressing _Ctrl + Shift + P_ and selecting Select Python interpreter.

## Development Status

**v0.01** - Extremely unstable. Do not use in production or internally yet.

This is pre-alpha software under active development. APIs will change frequently without notice. 