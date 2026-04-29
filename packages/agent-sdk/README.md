# Spaik SDK

Python SDK for building AI agents with multi-LLM support, streaming, and production infrastructure.

Spaik SDK is an open-source project developed by engineers at Siili Solutions Oyj. This is not an official Siili product.

## Installation

```bash
pip install spaik-sdk
```

## Quick Start

```python
from spaik_sdk.agent.base_agent import BaseAgent

class MyAgent(BaseAgent):
    pass

agent = MyAgent(system_prompt="You are a helpful assistant.")
print(agent.get_response_text("Hello!"))
```

## Features

- **Multi-LLM Support**: OpenAI, Anthropic, Google, Azure AI Foundry, DeepSeek, Mistral, Meta Llama, Cohere, xAI (Grok), Moonshot (Kimi), Ollama
- **Unified API**: Same interface across all providers
- **Streaming**: Real-time response streaming via SSE
- **Tools**: Function calling with LangChain integration
- **Subagents**: Isolated nested agent execution with `spawn()`
- **Tracing**: Configurable trace persistence with pluggable sinks
- **Structured Output**: Pydantic model responses
- **Server**: FastAPI with thread persistence, auth, file uploads
- **Audio**: Text-to-speech and speech-to-text
- **Cost Tracking**: Token usage and cost estimation

## Agent API

### Basic Response Methods

```python
from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.models.model_registry import ModelRegistry

agent = MyAgent(
    system_prompt="You are helpful.",
    llm_model=ModelRegistry.CLAUDE_4_SONNET
)

# Sync - text only
text = agent.get_response_text("Hello")

# Sync - full message with blocks
message = agent.get_response("Hello")
print(message.get_text_content())

# Async
message = await agent.get_response_async("Hello")
```

### Streaming

```python
# Token stream
async for chunk in agent.get_response_stream("Write a story"):
    print(chunk, end="", flush=True)

# Event stream (for SSE)
async for event in agent.get_event_stream("Write a story"):
    if event.get_event_type() == "StreamingUpdated":
        print(event.content, end="")
```

### Structured Output

```python
from pydantic import BaseModel

class Recipe(BaseModel):
    name: str
    ingredients: list[str]
    steps: list[str]

recipe = agent.get_structured_response("Give me a pasta recipe", Recipe)
print(recipe.name)
```

### Interactive CLI

```python
agent.run_cli()  # Starts interactive chat in terminal
```

### LangGraph Interop

Expose the configured LangChain model and a ready-to-use LangGraph ReAct agent when you need to compose Spaik agents into custom LangChain or LangGraph workflows.

```python
agent = MyAgent(system_prompt="You are helpful.")

llm = agent.get_langchain_model()
react_agent = agent.get_react_agent()
```

## Tools

```python
from spaik_sdk.tools.tool_provider import ToolProvider, BaseTool, tool

class WeatherTools(ToolProvider):
    def get_tools(self) -> list[BaseTool]:
        @tool
        def get_weather(city: str) -> str:
            """Get current weather for a city."""
            return f"Sunny, 22°C in {city}"
        
        @tool
        def get_forecast(city: str, days: int = 3) -> str:
            """Get weather forecast."""
            return f"{days}-day forecast for {city}: Sunny"
        
        return [get_weather, get_forecast]

class WeatherAgent(BaseAgent):
    def get_tool_providers(self) -> list[ToolProvider]:
        return [WeatherTools()]

agent = WeatherAgent(system_prompt="You provide weather info.")
print(agent.get_response_text("What's the weather in Tokyo?"))
```

### Built-in Tool Providers

```python
from spaik_sdk.tools.impl.search_tool_provider import SearchToolProvider
from spaik_sdk.tools.impl.mcp_tool_provider import MCPToolProvider

class MyAgent(BaseAgent):
    def get_tool_providers(self):
        return [
            SearchToolProvider(),      # Web search (Tavily)
            MCPToolProvider(server),   # MCP server tools
        ]
```

### Controlling Tool-Call Replay in History

Each `ToolProvider` controls how its tool-use blocks are rendered back into model history when a thread is replayed. By default, the replay contains the tool name, call id, arguments, response, and error state.

Use `persist_tool_block_history=False` when a provider should replay only a name marker instead of full call details. This is useful for tools whose output is large, sensitive, or not useful to show the model again.

```python
class SearchTools(ToolProvider):
    def __init__(self) -> None:
        super().__init__(persist_tool_block_history=False)

    def get_tools(self) -> list[BaseTool]:
        ...
```

Override `render_tool_block_for_history()` when you need provider-specific history text.

```python
from spaik_sdk.thread.models import MessageBlock

class SearchTools(ToolProvider):
    def render_tool_block_for_history(self, block: MessageBlock) -> str:
        return f'<search tool="{block.tool_name}" />'
```

Tool-use blocks persist the owning provider id on the thread, so after a thread reload the SDK rebinds the correct `ToolProvider` and applies the same history-rendering policy. Override `get_provider_id()` if a provider needs a stable id across package or class renames.

## Subagents

To call one agent from inside another agent's tool, use `spawn()` instead of `get_response()`. This prevents LangChain's callback context from leaking into the subagent, which would otherwise cause the subagent's internal tool calls to appear in the parent thread.

```python
class ResearchTools(ToolProvider):
    def get_tools(self) -> list[BaseTool]:
        @tool
        def research(topic: str) -> str:
            """Delegate a research task to a specialist subagent."""
            sub = ResearchAgent(system_prompt="You are a research specialist.")
            return sub.spawn(topic).get_text_content()
        return [research]
```

For cases where you need to isolate an arbitrary coroutine rather than a full agent call, use the static `BaseAgent.run_isolated(coro)` helper directly.

## Tracing

Every agent run produces an `AgentTrace`. Configure trace persistence with the `trace_sink` constructor argument or the `TRACE_SINK_MODE` environment variable.

```python
from spaik_sdk.tracing.local_trace_sink import LocalTraceSink
from spaik_sdk.tracing.noop_trace_sink import NoOpTraceSink

# Disable trace persistence
agent = MyAgent(system_prompt="...", trace_sink=NoOpTraceSink())

# Write traces to a custom directory
agent = MyAgent(system_prompt="...", trace_sink=LocalTraceSink(traces_dir="./custom-traces"))
```

`TRACE_SINK_MODE=local` forces local file traces and `TRACE_SINK_MODE=noop` disables trace persistence. Implement `TraceSink` for remote or database-backed trace storage.

## Models

```python
from spaik_sdk.models.model_registry import ModelRegistry

# Anthropic
ModelRegistry.CLAUDE_4_SONNET
ModelRegistry.CLAUDE_4_OPUS
ModelRegistry.CLAUDE_4_5_SONNET
ModelRegistry.CLAUDE_4_5_OPUS
ModelRegistry.CLAUDE_4_6_SONNET
ModelRegistry.CLAUDE_4_6_OPUS

# OpenAI
ModelRegistry.GPT_4_1
ModelRegistry.GPT_4O
ModelRegistry.O4_MINI
ModelRegistry.GPT_5_4

# Google
ModelRegistry.GEMINI_2_5_FLASH
ModelRegistry.GEMINI_2_5_PRO
ModelRegistry.GEMINI_3_1_PRO

# Azure AI Foundry and other provider families
ModelRegistry.DEEPSEEK_V3_2
ModelRegistry.MISTRAL_LARGE_3
ModelRegistry.LLAMA_4_MAVERICK
ModelRegistry.COHERE_COMMAND_A
ModelRegistry.GROK_4
ModelRegistry.KIMI_K2_THINKING

# Aliases
ModelRegistry.from_name("sonnet")      # CLAUDE_4_6_SONNET
ModelRegistry.from_name("gpt 4.1")     # GPT_4_1
ModelRegistry.from_name("gemini 2.5")  # GEMINI_2_5_FLASH

# Custom model
from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.llm_families import LLMFamilies

custom = LLMModel(
    family=LLMFamilies.OPENAI,
    name="gpt-4-custom",
    reasoning=False
)
ModelRegistry.register_custom(custom)
```

## FastAPI Server

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.server.api.routers.api_builder import ApiBuilder

class MyAgent(BaseAgent):
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    agent = MyAgent(system_prompt="You are helpful.")
    api_builder = ApiBuilder.local(agent=agent)
    
    app.include_router(api_builder.build_thread_router())
    app.include_router(api_builder.build_file_router())
    app.include_router(api_builder.build_audio_router())
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Endpoints

Thread management:
- `POST /threads` - Create thread
- `GET /threads` - List threads
- `GET /threads/{id}` - Get thread with messages
- `POST /threads/{id}/messages/stream` - Send message (SSE)
- `DELETE /threads/{id}` - Delete thread
- `POST /threads/{id}/cancel` - Cancel generation

Files:
- `POST /files` - Upload file
- `GET /files/{id}` - Download file

Audio:
- `POST /audio/speech` - Text to speech
- `POST /audio/transcribe` - Speech to text

### Production Setup

```python
from spaik_sdk.server.storage.impl.local_file_thread_repository import LocalFileThreadRepository
from spaik_sdk.server.authorization.base_authorizer import BaseAuthorizer

# Custom repository and auth
api_builder = ApiBuilder.stateful(
    repository=LocalFileThreadRepository(base_path="./data"),
    authorizer=MyAuthorizer(),
    agent=agent,
)
```

Long-running streams are checkpointed incrementally. The built-in response generator calls `update_thread` after each `ToolResponseReceivedEvent` and `MessageFullyAddedEvent`, so completed tool results and messages survive crashes or restarts during a run.

## Orchestration

Code-first workflow orchestration without graph DSLs:

```python
from spaik_sdk.orchestration import BaseOrchestrator, OrchestratorEvent
from dataclasses import dataclass
from typing import AsyncIterator

@dataclass
class State:
    items: list[str]

@dataclass
class Result:
    count: int

class MyOrchestrator(BaseOrchestrator[State, Result]):
    async def run(self) -> AsyncIterator[OrchestratorEvent[Result]]:
        state = State(items=[])
        
        # Run step with automatic status events
        async for event in self.step("fetch", "Fetching data", self.fetch, state):
            yield event
            if event.result:
                state = event.result
        
        # Progress updates
        for i, item in enumerate(state.items):
            yield self.progress("process", i + 1, len(state.items))
            await self.process(item)
        
        yield self.ok(Result(count=len(state.items)))
    
    async def fetch(self, state: State) -> State:
        return State(items=["a", "b", "c"])
    
    async def process(self, item: str):
        pass

# Run
orchestrator = MyOrchestrator()
result = orchestrator.run_sync()
```

## Configuration

Environment variables:

```bash
# Direct mode: at least one LLM provider API key required
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Optional
AZURE_API_KEY=...
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
DEFAULT_MODEL=claude-sonnet-4-20250514
```

### Proxy Mode

Set `LLM_AUTH_MODE=proxy` to route every provider through a single proxy endpoint such as LiteLLM or an internal gateway. Provider API keys are not required in this mode.

| Env Variable | Description |
|--------------|-------------|
| `LLM_AUTH_MODE` | `direct` (default) or `proxy` |
| `LLM_PROXY_BASE_URL` | Proxy endpoint URL |
| `LLM_PROXY_API_KEY` | Auth key sent to the proxy |
| `LLM_PROXY_HEADERS` | Extra headers, comma-separated `Key:Value` pairs |

## Development

```bash
# Setup
uv sync

# Tests
make test                           # All
make test-unit                      # Unit only
make test-integration               # Integration only
make test-unit-single PATTERN=name  # Single test

# Quality
make lint                           # Check linting
make lint-fix                       # Fix linting
make typecheck                      # Type check
```

## Message Structure

Messages contain blocks of different types:

```python
from spaik_sdk.thread.models import MessageBlockType

# Block types
MessageBlockType.PLAIN      # Regular text
MessageBlockType.REASONING  # Chain of thought
MessageBlockType.TOOL_USE   # Tool call
MessageBlockType.ERROR      # Error message
```

## License

MIT - Copyright (c) 2026 Siili Solutions Oyj
