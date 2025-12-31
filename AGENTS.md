# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Agent SDK - a monorepo for building production-ready AI agents. It consists of:
- **Python SDK** (`packages/agent-sdk/`) - Core agent functionality with multi-LLM support
- **React Hooks** (`packages/agent-sdk-hooks/`) - Frontend integration library  
- **Examples** (`examples/`) - Working examples for agents, backend APIs, and frontend

The project enables rapid development of AI agents that work across OpenAI, Anthropic, Google, and Azure models with built-in streaming, persistence, and production infrastructure.

## Development Commands

### Python SDK (packages/agent-sdk/)
```bash
# Setup environment
cd packages/agent-sdk
uv sync

# Run tests
make test                    # All tests
make test-unit              # Unit tests only
make test-integration       # Integration tests only
make test-cov              # Tests with coverage
make test-unit-single PATTERN=test_name  # Single test by pattern

# Code quality
make lint                   # Check linting
make lint-fix               # Fix linting issues
make typecheck             # Run mypy type checking
ruff check --fix           # Alternative linting
ruff format                # Format code

# Development
./setup.sh                 # Initial setup script
./kill.sh                  # Stop running services
```

### React Hooks (packages/agent-sdk-hooks/)
```bash
cd packages/agent-sdk-hooks

# Build and development  
bun run build              # Build library
bun run dev                # Build in watch mode
bun run type-check         # TypeScript checking
bun run lint               # ESLint
bun run lint:fix           # ESLint with fixes
```

### Monorepo Commands (from root)
```bash
# Install all dependencies
bun install

# Development servers
bun run dev:backend        # Start FastAPI backend example
bun run dev:frontend       # Start React frontend example

# Build specific packages
bun run build:hooks        # Build React hooks package
```

## Architecture

### Core Components

**BaseAgent** (`packages/agent-sdk/siili_ai_sdk/agent/base_agent.py`): 
- Main entry point for creating agents
- Handles system prompts, tools, and model configuration
- Provides sync/async response methods and streaming

**LLM Providers** (`packages/agent-sdk/siili_ai_sdk/models/providers/`):
- Abstraction layer over different AI providers
- Unified interface for OpenAI, Anthropic, Google, Azure
- Model registry for easy model switching

**Thread Management** (`packages/agent-sdk/siili_ai_sdk/thread/`):
- Conversation state management with blocks and messages
- Streaming adapters for real-time responses
- CLI adapters for interactive development

**Server Infrastructure** (`packages/agent-sdk/siili_ai_sdk/server/`):
- FastAPI routers with SSE streaming
- Thread persistence and storage
- Authentication and authorization hooks

**React Integration** (`packages/agent-sdk-hooks/src/`):
- Zustand stores for thread and message state
- Real-time streaming via WebSocket/SSE
- Type-safe hooks for React components

### Key Patterns

- **Convention over Configuration**: Minimal setup required, sensible defaults
- **Provider Abstraction**: Same API across all LLM providers
- **Streaming-First**: Built for real-time responses
- **Type Safety**: Full TypeScript/Python typing throughout

## Testing Strategy

- Unit tests in `tests/unit/` with pytest
- Integration tests in `tests/integration/`
- Recorded LLM responses for deterministic testing
- Coverage reporting with HTML output in `htmlcov/`

## Environment Setup

Required environment variables:
```bash
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key  
GOOGLE_API_KEY=your-key
AZURE_API_KEY=your-key          # Optional
AZURE_ENDPOINT=your-endpoint    # Optional
```

## Package Management

- Python: `uv` for dependency management and virtual environments
- JavaScript: `bun` with workspaces for monorepo management  
- Versions: Python 3.10+, Bun 1.0+

## Development Status

This is pre-alpha software (v0.01) under active development. APIs change frequently without notice.