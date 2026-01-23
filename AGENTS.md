# AGENTS.md

Guidance for AI coding assistants working with this repository.

## Project Structure

```
agent-sdk/
├── packages/
│   ├── agent-sdk/              # Python SDK - core agent functionality
│   ├── agent-sdk-hooks/        # React hooks for frontend state management
│   ├── agent-sdk-material/     # Material UI chat components
│   ├── coding-agents/          # Pre-built coding agents (Claude Code, Cursor)
│   └── agent-workflows/        # YAML-driven workflow engine
├── examples/
│   ├── agents/                 # Standalone agent examples
│   ├── backend/                # FastAPI server example
│   └── frontend/               # React frontend example
└── templates/                  # Project templates for scaffolding
```

## Python SDK (packages/agent-sdk/)

### Key Modules

- `agent/base_agent.py` - Main agent class, handles prompts, tools, streaming
- `models/model_registry.py` - LLM model definitions and aliases
- `models/providers/` - Provider implementations (OpenAI, Anthropic, Google, Ollama)
- `tools/tool_provider.py` - Tool definition system using LangChain
- `thread/` - Conversation state, message blocks, event streaming
- `server/api/routers/api_builder.py` - FastAPI router factory
- `orchestration/base_orchestrator.py` - Code-first workflow orchestration

### Commands

```bash
cd packages/agent-sdk

# Environment
uv sync

# Tests
make test                           # All tests
make test-unit                      # Unit only
make test-integration               # Integration only
make test-unit-single PATTERN=name  # Single test

# Quality
make lint                           # Check
make lint-fix                       # Fix
make typecheck                      # Type check
```

### Creating an Agent

```python
from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.tools.tool_provider import ToolProvider, BaseTool, tool

class MyTools(ToolProvider):
    def get_tools(self) -> list[BaseTool]:
        @tool
        def get_weather(city: str) -> str:
            """Get current weather for a city."""
            return f"Weather in {city}: sunny"
        return [get_weather]

class MyAgent(BaseAgent):
    def get_tool_providers(self) -> list[ToolProvider]:
        return [MyTools()]

agent = MyAgent(
    system_prompt="You are a helpful assistant.",
    llm_model=ModelRegistry.CLAUDE_4_SONNET
)
print(agent.get_response_text("What's the weather in Helsinki?"))
```

### Agent Methods

- `get_response_text(input)` - Sync, returns text
- `get_response(input)` - Sync, returns ThreadMessage
- `get_response_async(input)` - Async, returns ThreadMessage  
- `get_response_stream(input)` - Async generator for streaming
- `get_event_stream(input)` - Async generator for ThreadEvents
- `get_structured_response(prompt, Schema)` - Returns Pydantic model
- `run_cli()` - Interactive CLI mode

### FastAPI Server

```python
from fastapi import FastAPI
from spaik_sdk.server.api.routers.api_builder import ApiBuilder

app = FastAPI()
agent = MyAgent()
api_builder = ApiBuilder.local(agent=agent)

app.include_router(api_builder.build_thread_router())
app.include_router(api_builder.build_file_router())
app.include_router(api_builder.build_audio_router())
```

### Model Registry

```python
from spaik_sdk.models.model_registry import ModelRegistry

# Direct access
ModelRegistry.CLAUDE_4_SONNET
ModelRegistry.GPT_4_1
ModelRegistry.GEMINI_2_5_FLASH

# By alias
ModelRegistry.from_name("sonnet")      # CLAUDE_4_SONNET
ModelRegistry.from_name("gpt 4.1")     # GPT_4_1
ModelRegistry.from_name("opus 4.5")    # CLAUDE_4_5_OPUS
```

## React Hooks (packages/agent-sdk-hooks/)

### Commands

```bash
cd packages/agent-sdk-hooks
bun run build      # Build
bun run dev        # Watch mode
bun run type-check # TypeScript
bun run lint       # ESLint
```

### Usage

```tsx
import {
  AgentSdkClientProvider,
  AgentSdkClient,
  useThreadList,
  useThread,
  useThreadActions,
  useThreadSelection,
} from 'spaik-sdk-react';

const client = new AgentSdkClient({ baseUrl: 'http://localhost:8000' });

function App() {
  return (
    <AgentSdkClientProvider apiClient={client}>
      <Chat />
    </AgentSdkClientProvider>
  );
}

function Chat() {
  const { threadSummaries } = useThreadList();
  const { selectedThreadId, selectThread } = useThreadSelection();
  const { thread } = useThread(selectedThreadId);
  const { createThread, sendMessage } = useThreadActions();
  // ...
}
```

### Available Hooks

- `useThreadList()` - Thread summaries, loading state, refresh
- `useThread(threadId)` - Full thread with messages
- `useThreadActions()` - createThread, sendMessage
- `useThreadSelection()` - Selected thread ID management
- `useTextToSpeech()` - TTS functionality
- `useSpeechToText()` - STT functionality
- `usePushToTalk()` - Voice input
- `useFileUploadStore()` - File attachments

## Material UI Components (packages/agent-sdk-material/)

Pre-built chat UI components with theming support:

- `AgentChat` - Full chat interface
- `ChatPanel` - Message list with input
- `MessageCard` - Individual message display
- `ThreadSidebar` - Thread list navigation
- `MessageInput` - Input with attachments
- Audio controls (TTS, STT, push-to-talk)

## Monorepo Commands

```bash
# Root directory
bun install                    # Install all deps
bun run build:hooks            # Build React hooks
bun run build:material         # Build Material components
bun run dev:frontend           # Start example frontend
bun run dev:backend            # Start example backend
```

## Environment Variables

```bash
# LLM Providers (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Optional
AZURE_API_KEY=...
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
DEFAULT_MODEL=claude-sonnet-4-20250514
```

## API Endpoints

Thread router provides:
- `POST /threads` - Create thread
- `GET /threads` - List threads
- `GET /threads/{id}` - Get thread
- `POST /threads/{id}/messages/stream` - Send message (SSE streaming)
- `DELETE /threads/{id}` - Delete thread
- `POST /threads/{id}/cancel` - Cancel generation

File router:
- `POST /files` - Upload file
- `GET /files/{id}` - Download file

Audio router:
- `POST /audio/speech` - Text to speech
- `POST /audio/transcribe` - Speech to text

## Testing

Python tests use pytest with recorded LLM responses for determinism:
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Recordings: `tests/recordings/`

## License

MIT - Copyright (c) 2025 Siili Solutions Oyj
