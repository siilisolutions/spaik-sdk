# AI Instructions - Backend (Python SDK)

This document provides comprehensive instructions for working with the Agent SDK backend components (`packages/agent-sdk/`).

## Core Backend Components

### BaseAgent (`siili_ai_sdk/agent/base_agent.py:32`)

The primary class for creating AI agents. Inherits from ABC and provides the foundation for all agent implementations.

#### Constructor Parameters
```python
def __init__(
    self,
    system_prompt_args: Dict[str, Any] = {},
    system_prompt_version: Optional[str] = None,
    system_prompt: Optional[str] = None,
    prompt_loader: Optional[PromptLoader] = None,
    prompt_loader_mode: Optional[PromptLoaderMode] = None,
    llm_config: Optional[LLMConfig] = None,
    llm_model: Optional[LLMModel] = None,
    reasoning: Optional[bool] = None,
    trace: Optional[AgentTrace] = None,
    thread_container: Optional[ThreadContainer] = None,
    tools: Optional[List[BaseTool]] = None,
    tool_providers: Optional[List[ToolProvider]] = None,
    recorder: Optional[ConditionalRecorder] = None,
    cancellation_handle: Optional[CancellationHandle] = None,
)
```

#### Public Methods

**Response Generation Methods:**

- **`get_response_stream(user_input: Optional[str]) -> AsyncGenerator[Dict[str, Any], None]`** (`siili_ai_sdk/agent/base_agent.py:62`)
  - Returns async generator for streaming responses
  - Yields dictionaries with response chunks
  - Use for real-time streaming applications

- **`get_event_stream(user_input: Optional[str]) -> AsyncGenerator[ThreadEvent, None]`** (`siili_ai_sdk/agent/base_agent.py:67`)
  - Returns async generator for structured events
  - Yields ThreadEvent objects for detailed response handling
  - Use for event-driven architectures

- **`get_response(user_input: Optional[str]) -> ThreadMessage`** (`siili_ai_sdk/agent/base_agent.py:75`)
  - Synchronous method returning complete response
  - Blocks until full response is received
  - Use for simple request/response patterns

- **`get_response_async(user_input: Optional[str]) -> ThreadMessage`** (`siili_ai_sdk/agent/base_agent.py:78`)
  - Async version of get_response
  - Non-blocking, returns awaitable ThreadMessage
  - Preferred for async applications

- **`get_response_text(user_input: Optional[str]) -> str`** (`siili_ai_sdk/agent/base_agent.py:87`)
  - Convenience method returning just text content
  - Synchronous, blocks until completion
  - Use for simple text-only responses

- **`get_response_text_async(user_input: Optional[str]) -> str`** (`siili_ai_sdk/agent/base_agent.py:90`)
  - Async version of get_response_text
  - Returns awaitable string
  - Preferred for async text-only responses

- **`get_structured_response(prompt: str, output_schema: Type[T]) -> T`** (`siili_ai_sdk/agent/base_agent.py:93`)
  - Returns response parsed as Pydantic model
  - Type-safe structured output
  - Use for data extraction and structured generation

**Configuration Methods:**

- **`create_llm_config(llm_model: Optional[LLMModel], reasoning: Optional[bool]) -> LLMConfig`** (`siili_ai_sdk/agent/base_agent.py:104`)
  - Creates LLM configuration with model and reasoning settings
  - Returns LLMConfig object for model configuration

- **`get_llm_model() -> LLMModel`** (`siili_ai_sdk/agent/base_agent.py:114`)
  - Returns default LLM model from environment configuration
  - Override in subclasses for custom model selection

- **`is_reasoning() -> bool`** (`siili_ai_sdk/agent/base_agent.py:117`)
  - Returns whether reasoning mode is enabled
  - Default: True. Override for custom reasoning behavior

**Tool Integration Methods:**

- **`get_tool_providers() -> List[ToolProvider]`** (`siili_ai_sdk/agent/base_agent.py:120`)
  - Override to define agent tools
  - Return list of ToolProvider instances
  - Tools are automatically integrated into agent responses

**Thread Management Methods:**

- **`set_thread_container(thread_container: ThreadContainer) -> None`** (`siili_ai_sdk/agent/base_agent.py:123`)
  - Sets custom thread container for conversation state
  - Automatically subscribes to thread events

- **`set_cancellation_handle(cancellation_handle: Optional[CancellationHandle]) -> None`** (`siili_ai_sdk/agent/base_agent.py:129`)
  - Sets cancellation handle for request cancellation
  - Use for implementing request timeouts and cancellation

**CLI Method:**

- **`run_cli() -> None`** (`siili_ai_sdk/agent/base_agent.py:101`)
  - Starts interactive CLI interface
  - Use for testing and development
  - Blocks until CLI session ends

#### Basic Usage Patterns

**Simple Agent:**
```python
class HelloAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt="You are a helpful assistant.")

agent = HelloAgent()
response = agent.get_response_text("Hello!")
```

**Agent with Custom Model:**
```python
from siili_ai_sdk.models.model_registry import ModelRegistry

class ClaudeAgent(BaseAgent):
    def get_llm_model(self) -> LLMModel:
        return ModelRegistry.CLAUDE_4_SONNET

agent = ClaudeAgent()
```

**Agent with Tools:**
```python
class WeatherAgent(BaseAgent):
    def get_tool_providers(self) -> List[ToolProvider]:
        return [WeatherToolProvider()]
```

### Tool System

#### ToolProvider (`siili_ai_sdk/tools/tool_provider.py`)

Base class for defining agent tools.

```python
from siili_ai_sdk.tools.tool_provider import ToolProvider, tool, BaseTool
from typing import List

class MyToolProvider(ToolProvider):
    def get_tools(self) -> List[BaseTool]:
        @tool
        def calculate_sum(a: int, b: int) -> int:
            """Calculates the sum of two numbers."""
            return a + b
        
        @tool
        def get_weather(city: str) -> str:
            """Gets weather information for a city."""
            return f"Weather in {city}: Sunny, 25°C"
        
        return [calculate_sum, get_weather]
```

**Key Requirements:**
- Use `@tool` decorator on functions
- Provide clear docstrings (used by LLM)
- Use type hints for all parameters and return values
- Keep functions focused and atomic

### Model Configuration

#### ModelRegistry (`siili_ai_sdk/models/model_registry.py`)

Centralized registry of available models:

```python
from siili_ai_sdk.models.model_registry import ModelRegistry

# OpenAI models
ModelRegistry.GPT_4_TURBO
ModelRegistry.GPT_4O
ModelRegistry.O1_PREVIEW
ModelRegistry.O1_MINI

# Anthropic models
ModelRegistry.CLAUDE_4_SONNET
ModelRegistry.CLAUDE_3_5_SONNET
ModelRegistry.CLAUDE_3_OPUS

# Google models
ModelRegistry.GEMINI_2_5_FLASH
ModelRegistry.GEMINI_2_5_FLASH_THINKING

# Azure models (if configured)
ModelRegistry.AZURE_GPT_4O
```

#### LLMConfig (`siili_ai_sdk/models/llm_config.py`)

Configuration object for LLM settings:

```python
from siili_ai_sdk.models.llm_config import LLMConfig
from siili_ai_sdk.models.providers.provider_type import ProviderType

config = LLMConfig(
    model=ModelRegistry.CLAUDE_4_SONNET,
    provider_type=ProviderType.ANTHROPIC,
    reasoning=True,
    tool_usage=True,
    temperature=0.7,  # Optional
    max_tokens=4000,  # Optional
)
```

### Thread Management

#### ThreadContainer (`siili_ai_sdk/thread/thread_container.py`)

Manages conversation state and message history:

```python
from siili_ai_sdk.thread.thread_container import ThreadContainer

# Create thread container
container = ThreadContainer(system_prompt="You are a helpful assistant.")

# Set on agent
agent.set_thread_container(container)

# Access messages
messages = container.get_messages()
```

#### ThreadMessage (`siili_ai_sdk/thread/models.py`)

Represents a single message in conversation:

```python
# Access message content
message = agent.get_response("Hello")
text_content = message.get_text_content()
blocks = message.blocks  # List of MessageBlock objects
```

### Recording and Playback

#### ConditionalRecorder (`siili_ai_sdk/recording/conditional_recorder.py`)

Records LLM interactions for testing and debugging:

```python
from siili_ai_sdk.recording.conditional_recorder import ConditionalRecorder

recorder = ConditionalRecorder.create_if_recording()
agent = MyAgent(recorder=recorder)

# Interactions are automatically recorded
response = agent.get_response_text("Test message")
```

### Environment Configuration

#### env_config (`siili_ai_sdk/config/env.py`)

Manages environment-based configuration:

```python
from siili_ai_sdk.config.env import env_config

# Get default model from environment
default_model = env_config.get_default_model()

# Check if recording is enabled
is_recording = env_config.is_recording_enabled()
```

**Required Environment Variables:**
```bash
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key
GOOGLE_API_KEY=your-google-key
AZURE_API_KEY=your-azure-key          # Optional
AZURE_ENDPOINT=your-azure-endpoint    # Optional
```

## Development Commands

```bash
# Environment setup
cd packages/agent-sdk
uv sync

# Testing
make test                    # All tests
make test-unit              # Unit tests only
make test-integration       # Integration tests only
make test-cov              # Tests with coverage
make test-unit-single PATTERN=test_name  # Single test

# Code quality
make lint                   # Check linting
make lint-fix               # Fix linting issues
make typecheck             # Run mypy type checking
ruff check --fix           # Alternative linting
ruff format                # Format code
```

## Common Patterns

### Async/Await Pattern
```python
async def async_agent_example():
    agent = MyAgent()
    response = await agent.get_response_async("Hello")
    return response.get_text_content()
```

### Streaming Pattern
```python
async def streaming_example():
    agent = MyAgent()
    async for chunk in agent.get_response_stream("Tell me a story"):
        print(chunk.get('content', ''), end='', flush=True)
```

### Structured Response Pattern
```python
from pydantic import BaseModel

class UserInfo(BaseModel):
    name: str
    age: int
    city: str

agent = MyAgent()
user_info = agent.get_structured_response(
    "Extract user info: John is 30 years old and lives in New York",
    UserInfo
)
print(f"Name: {user_info.name}, Age: {user_info.age}")
```

### Error Handling Pattern
```python
try:
    response = agent.get_response_text("Hello")
except Exception as e:
    logger.error(f"Agent error: {e}")
    # Handle error appropriately
```

## Testing Strategies

### Unit Testing
- Use recorded responses for deterministic testing
- Test individual agent methods in isolation
- Mock external dependencies

### Integration Testing
- Test full agent workflows
- Use real API calls in integration tests
- Verify tool integration works correctly

### Coverage
- HTML coverage reports available in `htmlcov/`
- Aim for high coverage on core agent logic
- Use `make test-cov` for coverage analysis

## Best Practices

1. **System Prompts**: Keep concise and specific
2. **Tool Design**: Single responsibility, clear docstrings
3. **Error Handling**: Graceful degradation and logging
4. **Model Selection**: Use ModelRegistry constants
5. **Async Usage**: Prefer async methods for scalability
6. **Type Safety**: Use Pydantic models for structured responses
7. **Testing**: Record interactions for reliable tests