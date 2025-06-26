# Siili AI SDK 

A Python SDK for building AI agents with multi-LLM support, streaming capabilities, and production-ready infrastructure.

## Features

- **Multi-LLM Support**: OpenAI, Anthropic, Google, Azure models
- **Streaming**: Real-time response streaming
- **Tools**: Custom tool integration with LangChain
- **Production Ready**: FastAPI server with REST/SSE APIs
- **Type Safe**: Full type annotations

## Quick Start

### Simple Agent

```python
from dotenv import load_dotenv
from siili_ai_sdk.agent.base_agent import BaseAgent

class HelloAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt="You're an unhelpful assistant that cant resist constantly talking about cats.")

if __name__ == "__main__":
    load_dotenv()
    agent = HelloAgent()
    print(agent.get_response_text("Hello"))
```

### Agent with Tools + FastAPI Server

```python
from typing import List
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.tools.tool_provider import ToolProvider, tool, BaseTool
from siili_ai_sdk.server.api.routers.api_builder import ApiBuilder
from siili_ai_sdk.models.model_registry import ModelRegistry

load_dotenv()

app = FastAPI(title="Agent SDK Backend Example", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DemoTool(ToolProvider):
    def get_tools(self) -> List[BaseTool]:
        @tool
        def get_secret_greeting() -> str:
            """Returns the users secret greeting."""
            return "kikkelis kokkelis"

        @tool
        def get_user_name() -> str:
            """Returns the users name."""
            return "Seppo Hovi"

        return [get_secret_greeting, get_user_name]

class DemoAgent(BaseAgent):
    def get_tool_providers(self) -> List[ToolProvider]:
        return [DemoTool()]

@app.on_event("startup")
async def startup_event():
    agent = DemoAgent(llm_model=ModelRegistry.CLAUDE_4_SONNET)
    api_builder = ApiBuilder.local(agent=agent)
    thread_router = api_builder.build_thread_router()
    app.include_router(thread_router)

def run_server():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

if __name__ == "__main__":
    run_server()
```

## Configuration

Set up your environment variables:

```bash
# API Keys
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key  
GOOGLE_API_KEY=your-google-key

# Azure (optional)
AZURE_API_KEY=your-azure-key
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
```

## Available Models

```python
from siili_ai_sdk.models.model_registry import ModelRegistry

# Use model registry for easy access
ModelRegistry.CLAUDE_4_SONNET
ModelRegistry.GPT_4_1
ModelRegistry.GEMINI_2_5_FLASH
ModelRegistry.O4_MINI

# Or use aliases
ModelRegistry.from_name("sonnet")      # -> CLAUDE_4_SONNET
ModelRegistry.from_name("gpt 4.1")     # -> GPT_4_1
```

## More Usage Examples

### Streaming Response

```python
async def stream_example():
    agent = DemoAgent()
    async for chunk in agent.get_response_stream("Write a story"):
        print(chunk.content, end="", flush=True)
```

### Structured Response

```python
from pydantic import BaseModel

class Recipe(BaseModel):
    name: str
    ingredients: list[str]
    instructions: list[str]

response = agent.get_structured_response("Create a pasta recipe", Recipe)
print(f"Recipe: {response.name}")
```

### Interactive CLI

```python
agent = DemoAgent()
agent.run_cli()  # Starts interactive chat
```

## API Endpoints

When running the FastAPI server:

```bash
# Health check
GET /health

# Create thread
POST /threads

# Send message (streaming)
POST /threads/{thread_id}/messages/stream

# Get messages
GET /threads/{thread_id}/messages
```

## Development

```bash
# Setup
./setup.sh

# Run tests
make test

# Format code
ruff check --fix
ruff format
```

## Project Structure

```
siili_ai_sdk/
├── agent/          # Core agent implementations
├── llm/            # LangChain service and streaming
├── models/         # LLM providers and configuration
├── thread/         # Conversation management
├── tools/          # Tool system
├── server/         # FastAPI server infrastructure
└── utils/          # Shared utilities
```

