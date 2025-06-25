v 0.01 - extremely unstable. Do not use in production or internally yet.



# Agent SDK Monorepo

A Python SDK for building various kinds of agentic + AI solutions with TypeScript React hooks for frontend integration.

## Structure

```
agent-sdk/
├── packages/
│   ├── agent-sdk/          # Core Python SDK
│   └── agent-sdk-hooks/    # React hooks for frontend integration
└── examples/
    ├── agents/             # Python agent examples
    ├── backend/            # FastAPI backend examples
    └── frontend/           # React frontend examples
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- uv (Python package manager)
- yarn (Node.js package manager)

### Setup

1. **Install Python dependencies for examples:**
   ```bash
   # Agent examples
   cd examples/agents
   uv sync

   # Backend examples  
   cd examples/backend
   uv sync
   ```

2. **Install TypeScript dependencies:**
   ```bash
   # Install all JS/TS dependencies
   yarn install:all
   ```

### Development

- **Run Python agent examples:**
  ```bash
  cd examples/agents
  uv run python hello_agent.py
  ```

- **Run FastAPI backend:**
  ```bash
  cd examples/backend
  uv run uvicorn main:app --reload
  ```

- **Run React frontend:**
  ```bash
  cd examples/frontend
  yarn dev
  ```

## Packages

### `packages/agent-sdk`
Core Python SDK for building AI agents with LLM integration, streaming, and tool support.

### `packages/agent-sdk-hooks`
React hooks library with Zustand state management and Zod type validation for connecting frontends to agent backends.

## Examples

### `examples/agents`
Simple Python examples showing how to use the agent SDK.

### `examples/backend`
FastAPI backend examples that expose agent APIs.

### `examples/frontend`
React frontend examples using the agent hooks library.

---

**Note:** This is a development setup. All packages are configured for local development with file:// dependencies. 