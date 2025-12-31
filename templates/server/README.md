# Server Template

FastAPI server template for Siili AI SDK agents.

## Setup

```bash
# Run init script
./init_template.sh

# Or manually
uv sync
```

Create `.env`:

```bash
ANTHROPIC_API_KEY=your-key
```

## Run

```bash
uv run uvicorn main:app --reload --port 8000
```

## Customization

### Add Tools

```python
from siili_ai_sdk.tools.tool_provider import ToolProvider, BaseTool, tool

class MyTools(ToolProvider):
    def get_tools(self) -> list[BaseTool]:
        @tool
        def my_function(arg: str) -> str:
            """Tool description for the LLM."""
            return f"Result: {arg}"
        return [my_function]

class MyAgent(BaseAgent):
    def get_tool_providers(self) -> list[ToolProvider]:
        return [MyTools()]
```

### System Prompt from File

Create `prompts/agent/MyAgent/system.md`:

```markdown
You are a helpful assistant.

## Capabilities
- Answer questions
- Use tools when needed
```

The SDK automatically loads this based on agent class name.

### Change Model

```python
from siili_ai_sdk.models.model_registry import ModelRegistry

agent = MyAgent(llm_model=ModelRegistry.CLAUDE_4_SONNET)
# or GPT_4_1, GEMINI_2_5_FLASH, etc.
```

### Production Setup

```python
from siili_ai_sdk.server.storage.impl.local_file_thread_repository import LocalFileThreadRepository

api_builder = ApiBuilder.stateful(
    repository=LocalFileThreadRepository(base_path="./data"),
    authorizer=MyAuthorizer(),
    agent=agent,
)
```

## Endpoints

- `POST /threads` - Create thread
- `GET /threads` - List threads
- `GET /threads/{id}` - Get thread
- `POST /threads/{id}/messages/stream` - Send message (SSE)
- `DELETE /threads/{id}` - Delete thread
- `POST /files` - Upload file
- `GET /files/{id}` - Download file
- `POST /audio/speech` - TTS
- `POST /audio/transcribe` - STT
