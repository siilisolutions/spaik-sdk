# Agent SDK

A powerful Python SDK for building AI agents with multi-LLM support, streaming capabilities, and production-ready infrastructure.

## 🚀 Features

- **Multi-LLM Support**: Unified interface for OpenAI, Anthropic, Google, and Azure models
- **Streaming-First**: Real-time response streaming with event-driven architecture
- **Tool Integration**: Easy custom tool creation with LangChain compatibility
- **Thread Management**: Conversation state management with persistent storage
- **Production Ready**: FastAPI server with authentication, job queues, and pub/sub
- **Type Safe**: Full TypeScript-style type annotations throughout

## 📋 Quick Start

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd agent-sdk
chmod +x setup.sh
./setup.sh

# Copy environment variables
cp env.example .env
# Edit .env with your API keys
```

### Basic Usage

```python
from siili_ai_sdk.demo_agents.minimal_agent import MinimalAgent
from siili_ai_sdk.models.llm_model import LLMModel

# Create an agent
agent = MinimalAgent(llm_model=LLMModel.GEMINI_2_5_FLASH)

# Get a simple response
response = agent.get_response_text("What is the capital of France?")
print(response)

# Run interactive CLI
agent.run_cli()
```

## 🏗️ Architecture Overview

The SDK follows a modular, event-driven architecture where agents orchestrate conversations between users and LLMs through a sophisticated thread management system.

### Core Components

- **BaseAgent**: Orchestrates all interactions, manages tools and configuration
- **LangChainService**: Handles LLM communication using LangChain framework
- **ThreadContainer**: Manages conversation state and emits events
- **ModelFactory/Provider**: Creates and configures LLM instances
- **ToolProvider**: Provides custom tools to agents
- **Server Infrastructure**: FastAPI-based REST/SSE APIs with job queues

## 🔧 Core Concepts

### Agents

Agents inherit from `BaseAgent` and define their behavior through system prompts and tools:

```python
from typing import List
from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.tools.tool_provider import ToolProvider

class MyAgent(BaseAgent):
    def get_tool_providers(self) -> List[ToolProvider]:
        return [MyCustomTool()]

# Usage
agent = MyAgent(llm_model=LLLModel.CLAUDE_4_SONNET)
response = await agent.get_response("Hello!")
```

### Thread System

Conversations are managed through `ThreadContainer` which maintains message history and emits real-time events:

```python
from siili_ai_sdk.thread.thread_container import ThreadContainer

# Create a thread
thread = ThreadContainer()

# Subscribe to events
def on_new_block(event):
    print(f"New block: {event.block.content}")

thread.subscribe("BlockAddedEvent", on_new_block)

# Messages contain structured blocks
message = thread.add_message("user", "Hello!")
# Blocks can be: PLAIN text, REASONING, TOOL_USE, ERROR
```

### Tools

Create custom tools by inheriting from `ToolProvider`:

```python
from typing import List
from langchain_core.tools import BaseTool, tool
from siili_ai_sdk.tools.tool_provider import ToolProvider

class WeatherTool(ToolProvider):
    def get_tools(self) -> List[BaseTool]:
        @tool
        def get_weather(city: str) -> str:
            """Get current weather for a city."""
            # Your weather API logic here
            return f"The weather in {city} is sunny"
        
        @tool  
        def get_forecast(city: str, days: int = 3) -> str:
            """Get weather forecast for multiple days."""
            return f"{days}-day forecast for {city}: sunny"
            
        return [get_weather, get_forecast]

# Use in agent
class WeatherAgent(BaseAgent):
    def get_tool_providers(self) -> List[ToolProvider]:
        return [WeatherTool()]
```

### LLM Configuration

The SDK supports multiple LLM providers with unified configuration:

```python
from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.model_registry import ModelRegistry

# Available models
models = [
    LLMModel.CLAUDE_4_SONNET,      # Anthropic
    LLMModel.GPT_4_1,              # OpenAI  
    LLMModel.GEMINI_2_5_FLASH,     # Google
    LLMModel.O4_MINI,              # OpenAI o1
]

# Model aliases supported
model = ModelRegistry.from_name("sonnet")  # -> CLAUDE_4_SONNET
model = ModelRegistry.from_name("gpt 4.1")  # -> GPT_4_1
```

## 📚 Usage Examples

### 1. Simple Text Generation

```python
from siili_ai_sdk.demo_agents.minimal_agent import MinimalAgent
from siili_ai_sdk.models.llm_model import LLMModel

agent = MinimalAgent(llm_model=LLMModel.CLAUDE_4_SONNET)
response = agent.get_response_text("Explain quantum computing")
print(response)
```

### 2. Structured Responses

```python
from pydantic import BaseModel

class Recipe(BaseModel):
    name: str
    ingredients: list[str]
    instructions: list[str]
    prep_time: int

response = agent.get_structured_response(
    "Create a simple pasta recipe", 
    Recipe
)
print(f"Recipe: {response.name}")
```

### 3. Streaming Responses

```python
import asyncio

async def stream_example():
    agent = MinimalAgent(llm_model=LLMModel.GEMINI_2_5_FLASH)
    
    async for chunk in agent.get_response_stream("Write a story"):
        print(chunk.content, end="", flush=True)

asyncio.run(stream_example())
```

### 4. Interactive CLI

```python
# Run interactive chat
agent = MinimalAgent()
agent.run_cli()  # Starts interactive session
```

### 5. Agent with Custom Tools

```python
class CalculatorTool(ToolProvider):
    def get_tools(self) -> List[BaseTool]:
        @tool
        def calculate(expression: str) -> str:
            """Safely evaluate mathematical expressions."""
            try:
                result = eval(expression)  # In production, use safe_eval
                return str(result)
            except Exception as e:
                return f"Error: {e}"
        
        return [calculate]

class MathAgent(BaseAgent):
    def get_tool_providers(self) -> List[ToolProvider]:
        return [CalculatorTool()]

# Usage
math_agent = MathAgent(llm_model=LLMModel.CLAUDE_4_SONNET)
result = math_agent.get_response_text("What is 15 * 23 + 47?")
```

## 🖥️ Server Deployment

### Local Development Server

```python
from siili_ai_sdk.server.playground.server import create_app
import uvicorn

app = create_app()
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Production Server with Custom Agent

```python
from siili_ai_sdk.server.api.routers.api_builder import ApiBuilder
from siili_ai_sdk.server.response.simple_agent_response_generator import SimpleAgentResponseGenerator

# Create response generator with your agent
response_generator = SimpleAgentResponseGenerator(
    agent_class=MyCustomAgent,
    llm_model=LLMModel.CLAUDE_4_SONNET
)

# Build API
api_builder = ApiBuilder.local(response_generator=response_generator)
app = api_builder.build_app()
```

### REST API Endpoints

```bash
# Health check
GET /health

# Create thread
POST /threads
{
  "system_prompt": "You are a helpful assistant"
}

# Send message (streaming)
POST /threads/{thread_id}/messages/stream
{
  "content": "Hello!",
  "role": "user"
}

# Get thread messages
GET /threads/{thread_id}/messages

# List threads
GET /threads?limit=10&offset=0
```

### Server-Sent Events (SSE)

```javascript
// Frontend JavaScript example
const eventSource = new EventSource('/threads/123/messages/stream');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('New content:', data);
};
```

## ⚙️ Configuration

### Environment Variables

```bash
# API Keys
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key  
GOOGLE_API_KEY=your-google-key

# Azure (if using Azure AI Foundry)
AZURE_API_KEY=your-azure-key
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2024-04-01-preview
AZURE_O3_MINI_DEPLOYMENT=o3-mini
AZURE_GPT_4_1_DEPLOYMENT=gpt-41

# Default model
DEFAULT_MODEL=claude-4-sonnet
MODEL_PROVIDER=anthropic

# Storage (for server mode)
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_STORAGE_CONTAINER_NAME=threads

# Authentication
AUTH_BYPASS=false  # Set to true for development
MS_TENANT_ID=your-tenant-id
MS_AUDIENCE=your-client-id
```

### Programmatic Configuration

```python
from siili_ai_sdk.models.llm_config import LLMConfig
from siili_ai_sdk.models.providers.provider_type import ProviderType

config = LLMConfig(
    model=LLMModel.CLAUDE_4_SONNET,
    provider_type=ProviderType.ANTHROPIC,
    temperature=0.7,
    max_tokens=4000,
    streaming=True,
    tool_usage=True,
    reasoning=False
)

agent = BaseAgent(llm_config=config)
```

## 🔄 Advanced Patterns

### Agent Interaction Flow

This diagram shows how a user request flows through the system:

### Custom Thread Adapters

Create custom adapters to handle thread events differently:

```python
from siili_ai_sdk.thread.adapters.streaming_block_adapter import StreamingBlockAdapter

class CustomAdapter(StreamingBlockAdapter):
    async def on_streaming_updated(self, event):
        # Custom logic for streaming updates
        print(f"Streaming: {event.content}")
    
    async def on_block_added(self, event):
        # Custom logic for new blocks
        await self.process_new_block(event.block)

# Use with agent
adapter = CustomAdapter(thread_container)
agent = MyAgent(thread_container=thread_container)
```

### Recording and Playback

Record agent interactions for testing and debugging:

```python
from siili_ai_sdk.recording.impl.local_recorder import LocalRecorder
from siili_ai_sdk.recording.impl.local_playback import LocalPlayback

# Record mode
recorder = LocalRecorder("./recordings")
agent = MyAgent(recorder=recorder)
response = agent.get_response_text("test message")  # Gets recorded

# Playback mode  
playback = LocalPlayback("./recordings")
agent = MyAgent(recorder=playback)
response = agent.get_response_text("test message")  # Plays back recording
```

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
make test

# Run only unit tests  
make test-unit
pytest tests/unit/ -m unit

# Run integration tests
make test-integration
pytest tests/integration/ -m integration

# With coverage
pytest --cov=siili_ai_sdk --cov-report=html
```

### Test Structure

- **Unit tests**: `tests/unit/siili_ai_sdk/{module}/test_{file}.py`
- **Integration tests**: `tests/integration/` (freeform structure)
- **Shared fixtures**: `tests/conftest.py`
- **Test utilities**: `tests/utils.py`

### Writing Tests

```python
import pytest
from siili_ai_sdk.agent.base_agent import BaseAgent

@pytest.mark.unit
def test_agent_creation():
    agent = ConcreteTestAgent()
    assert agent is not None

@pytest.mark.integration  
async def test_agent_with_llm():
    agent = MyAgent(llm_model=LLMModel.GEMINI_2_5_FLASH)
    response = await agent.get_response("test")
    assert len(response.content) > 0
```

## 🛠️ Development

### Project Structure

```
siili_ai_sdk/
├── agent/          # Core agent implementations
├── llm/            # LangChain service and streaming
├── models/         # LLM configuration and providers  
├── thread/         # Conversation management
├── tools/          # Tool system
├── server/         # FastAPI server infrastructure
├── config/         # Environment configuration
├── prompt/         # Prompt loading system
├── recording/      # Recording and playback
└── utils/          # Shared utilities
```

### Code Standards

- **Absolute imports**: Always use `from siili_ai_sdk.module import Class`
- **Type annotations**: All functions must have type hints
- **No star imports**: Avoid `from module import *`
- **Minimal comments**: Code should be self-documenting
- **uv + ruff**: Use for package management and linting

### Development Commands

```bash
# Setup development environment
./setup.sh

# Format and lint
ruff check --fix
ruff format

# Type checking
mypy siili_ai_sdk/

# Run specific test
pytest tests/unit/siili_ai_sdk/agent/test_base_agent.py::test_specific_function

# Start development server
python siili_ai_sdk/server/playground/server.py
```

## 🚀 Production Deployment

### Docker Container

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY siili_ai_sdk/ ./siili_ai_sdk/
COPY main.py .

CMD ["python", "-m", "uvicorn", "siili_ai_sdk.server.playground.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Setup

```bash
# Production environment variables
export ANTHROPIC_API_KEY="your-key"
export AZURE_STORAGE_CONNECTION_STRING="your-connection"
export AUTH_BYPASS=false
export MS_TENANT_ID="your-tenant-id"

# Start server
uvicorn siili_ai_sdk.server.playground.server:app --host 0.0.0.0 --port 8000
```

### Monitoring and Logging

```python
from siili_ai_sdk.utils.init_logger import init_logger
from siili_ai_sdk.tracing.agent_trace import AgentTrace

# Enable logging
logger = init_logger(__name__)

# Enable tracing
trace = AgentTrace("my-agent")
agent = MyAgent(trace=trace)
```

## 📖 Additional Resources

### Key Files to Understand

- **`siili_ai_sdk/agent/base_agent.py`**: Core agent implementation
- **`siili_ai_sdk/llm/langchain_service.py`**: LLM integration
- **`siili_ai_sdk/thread/thread_container.py`**: Conversation management
- **`siili_ai_sdk/models/model_registry.py`**: Available models
- **`main.py`**: Basic usage example

### Example Projects

See the demo agents for reference implementations:
- **`siili_ai_sdk/demo_agents/minimal_agent.py`**: Simple agent
- **`siili_ai_sdk/demo_agents/demo_agent.py`**: Agent with tools
- **`siili_ai_sdk/demo_agents/demo_tool.py`**: Custom tool example

## 🤝 Contributing

1. Follow the established code style and patterns
2. Add type annotations for all new code
3. Write tests for new functionality (focus on corner cases, not trivial getters/setters)
4. Use absolute imports
5. Keep functions focused and well-named
6. Add integration tests for workflows that span multiple components

## 📄 License

[Add your license information here]

---

**Happy building with Agent SDK! 🚀**

For questions or issues, please check the code examples above or examine the demo agents in the `siili_ai_sdk/demo_agents/` directory. 