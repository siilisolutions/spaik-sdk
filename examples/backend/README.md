# Backend Example

FastAPI server demonstrating the Spaik SDK.

## Setup

```bash
cd examples/backend
uv sync
```

Create `.env`:

```bash
ANTHROPIC_API_KEY=your-key
# or
OPENAI_API_KEY=your-key
# or
GOOGLE_API_KEY=your-key
```

## Run

```bash
uv run uvicorn main:app --reload --port 8000
```

## Endpoints

- `GET /docs` - Swagger UI
- `POST /threads` - Create thread
- `GET /threads` - List threads
- `GET /threads/{id}` - Get thread
- `POST /threads/{id}/messages/stream` - Send message (SSE)
- `DELETE /threads/{id}` - Delete thread
- `POST /files` - Upload file
- `GET /files/{id}` - Download file
- `POST /audio/speech` - Text to speech
- `POST /audio/transcribe` - Speech to text

## Structure

```
backend/
├── main.py           # Server setup and agent definition
└── prompts/
    └── agent/
        └── DemoAgent/
            └── system.md   # System prompt (optional)
```

## Agent Configuration

```python
from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.tools.tool_provider import ToolProvider, BaseTool, tool

class MyTools(ToolProvider):
    def get_tools(self) -> list[BaseTool]:
        @tool
        def my_function(arg: str) -> str:
            """Description for the LLM."""
            return f"Result: {arg}"
        return [my_function]

class MyAgent(BaseAgent):
    def get_tool_providers(self) -> list[ToolProvider]:
        return [MyTools()]

# Use with ApiBuilder
agent = MyAgent(llm_model=ModelRegistry.CLAUDE_4_SONNET)
api_builder = ApiBuilder.local(agent=agent)
app.include_router(api_builder.build_thread_router())
```

## Model Selection

```python
from spaik_sdk.models.model_registry import ModelRegistry

agent = MyAgent(llm_model=ModelRegistry.CLAUDE_4_SONNET)
# or
agent = MyAgent(llm_model=ModelRegistry.GPT_4_1)
# or
agent = MyAgent(llm_model=ModelRegistry.GEMINI_2_5_FLASH)
```

## Frontend Integration

Works with `examples/frontend`. CORS is enabled for all origins.
