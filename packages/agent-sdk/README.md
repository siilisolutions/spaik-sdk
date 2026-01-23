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

- **Multi-LLM Support**: OpenAI, Anthropic, Google, Azure, Ollama
- **Unified API**: Same interface across all providers
- **Streaming**: Real-time response streaming via SSE
- **Tools**: Function calling with LangChain integration
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

## Models

```python
from spaik_sdk.models.model_registry import ModelRegistry

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
ModelRegistry.from_name("sonnet")      # CLAUDE_4_SONNET
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
# LLM Providers (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Optional
AZURE_API_KEY=...
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
DEFAULT_MODEL=claude-sonnet-4-20250514
```

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

MIT - Copyright (c) 2025 Siili Solutions Oyj
