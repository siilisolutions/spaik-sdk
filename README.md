# Siili AI SDK

Build production-ready AI agents with multi-LLM support, streaming, and a complete frontend/backend stack.

Siili AI SDK is an open-source project developed and maintained by Siili Solutions Oyj.

**Early Release**  
This project is an early release. While it is functional and actively used,
some APIs may continue to evolve and occasional issues may exist.

Licensed under the MIT License. Provided "as is", without warranty of any kind.  
Siili Solutions Oyj assumes no liability for the use of this software.

## Features

**Python SDK**
- Multi-provider support: OpenAI, Anthropic, Google, Azure, Ollama
- Unified API across all providers
- Streaming responses with SSE
- Tool/function calling with LangChain
- Structured outputs via Pydantic
- FastAPI server with thread persistence
- File attachments and audio (TTS/STT)
- Cost tracking and token usage

**React Hooks**
- State management with Zustand
- Real-time streaming via SSE
- Thread and message management
- File uploads and audio controls
- Type-safe with Zod validation

**Material UI Components**
- Pre-built chat interface
- Theming support
- Message blocks (text, reasoning, tool calls)
- Audio controls

## Packages

| Package | Description | npm/PyPI |
|---------|-------------|----------|
| `siili-ai-sdk` | Python SDK | [PyPI](https://pypi.org/project/siili-ai-sdk/) |
| `@siilisolutions/ai-sdk-react` | React hooks | npm |
| `@siilisolutions/ai-sdk-material` | Material UI components | npm |
| `siili-coding-agents` | Pre-built coding agents | [PyPI](https://pypi.org/project/siili-coding-agents/) |

## Quick Start

### Minimal Agent

```python
from siili_ai_sdk.agent.base_agent import BaseAgent

class MyAgent(BaseAgent):
    pass

agent = MyAgent(system_prompt="You are a helpful assistant.")
print(agent.get_response_text("Hello!"))
```

### Agent with Tools

```python
from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.tools.tool_provider import ToolProvider, BaseTool, tool

class MyTools(ToolProvider):
    def get_tools(self) -> list[BaseTool]:
        @tool
        def search(query: str) -> str:
            """Search for information."""
            return f"Results for: {query}"
        return [search]

class MyAgent(BaseAgent):
    def get_tool_providers(self) -> list[ToolProvider]:
        return [MyTools()]

agent = MyAgent(system_prompt="You can search for information.")
print(agent.get_response_text("Search for Python tutorials"))
```

### FastAPI Server

```python
from fastapi import FastAPI
from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.server.api.routers.api_builder import ApiBuilder

app = FastAPI()

class MyAgent(BaseAgent):
    pass

@app.on_event("startup")
def startup():
    agent = MyAgent(system_prompt="You are helpful.")
    api_builder = ApiBuilder.local(agent=agent)
    app.include_router(api_builder.build_thread_router())
```

### React Frontend

```tsx
import {
  AgentSdkClientProvider,
  AgentSdkClient,
  useThread,
  useThreadActions,
} from '@siilisolutions/ai-sdk-react';

const client = new AgentSdkClient({ baseUrl: 'http://localhost:8000' });

function App() {
  return (
    <AgentSdkClientProvider apiClient={client}>
      <Chat threadId="my-thread" />
    </AgentSdkClientProvider>
  );
}

function Chat({ threadId }: { threadId: string }) {
  const { thread } = useThread(threadId);
  const { sendMessage } = useThreadActions();

  return (
    <div>
      {thread?.messages.map(msg => (
        <div key={msg.id}>
          {msg.blocks.map(block => (
            <p key={block.id}>{block.content}</p>
          ))}
        </div>
      ))}
      <button onClick={() => sendMessage(threadId, { content: "Hello!" })}>
        Send
      </button>
    </div>
  );
}
```

## Installation

### Python SDK

```bash
pip install siili-ai-sdk
```

### React Hooks

```bash
npm install @siilisolutions/ai-sdk-react
# or
bun add @siilisolutions/ai-sdk-react
```

### Material UI Components

```bash
npm install @siilisolutions/ai-sdk-material
```

## Running Examples

```bash
# Clone repo
git clone https://github.com/siilisolutions/siili-ai-sdk.git
cd siili-ai-sdk

# Backend
cd examples/backend
uv sync
echo "ANTHROPIC_API_KEY=your-key" > .env
uv run uvicorn main:app --reload

# Frontend (new terminal)
cd examples/frontend
bun install
bun run dev
```

Open `http://localhost:5173`

## Environment Variables

```bash
# At least one LLM provider API key required
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Optional
AZURE_API_KEY=...
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
DEFAULT_MODEL=claude-sonnet-4-20250514
```

## Model Support

```python
from siili_ai_sdk.models.model_registry import ModelRegistry

# Anthropic
ModelRegistry.CLAUDE_4_SONNET
ModelRegistry.CLAUDE_4_OPUS
ModelRegistry.CLAUDE_4_5_SONNET
ModelRegistry.CLAUDE_4_5_OPUS

# OpenAI
ModelRegistry.GPT_4_1
ModelRegistry.GPT_4O
ModelRegistry.O4_MINI

# Google
ModelRegistry.GEMINI_2_5_FLASH
ModelRegistry.GEMINI_2_5_PRO

# Aliases
ModelRegistry.from_name("sonnet")  # -> CLAUDE_4_SONNET
ModelRegistry.from_name("opus")    # -> CLAUDE_4_5_OPUS
```

## Documentation

- [Python SDK](packages/agent-sdk/README.md)
- [React Hooks](packages/agent-sdk-hooks/README.md)
- [Examples](examples/)

## Development

```bash
# Python SDK
cd packages/agent-sdk
uv sync
make test
make lint-fix

# React packages
bun install
bun run build:hooks
bun run build:material
```

## License

MIT - Copyright (c) 2025 Siili Solutions Oyj

## Security and Compliance Notice

Users are solely responsible for ensuring that their use of this software complies with applicable laws, regulations, and third-party service terms, including but not limited to data protection, privacy, and AI governance requirements.

Siili Solutions Oyj does not assume responsibility for how this software is configured or used in downstream applications.
