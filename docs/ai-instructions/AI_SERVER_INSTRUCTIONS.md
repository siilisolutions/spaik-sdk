# AI Instructions - Server API Usage

This document provides instructions for using the Agent SDK's public server APIs to build FastAPI-based applications. Focus on the actual public interfaces and methods available in the SDK.

## Public Server Interface: ApiBuilder

The main public interface for creating server applications is `ApiBuilder` (`spaik_sdk/server/api/routers/api_builder.py`):

### Basic Usage Pattern

```python
from fastapi import FastAPI
from spaik_sdk.server.api.routers.api_builder import ApiBuilder
from spaik_sdk.agent.base_agent import BaseAgent

app = FastAPI()

# Create your agent
agent = MyAgent()

# Build API router with local storage (development)
api_builder = ApiBuilder.local(agent=agent)
thread_router = api_builder.build_thread_router()

# Add to FastAPI app
app.include_router(thread_router)
```

### ApiBuilder Class Methods

#### `ApiBuilder.local(agent, response_generator=None, in_memory=False)`
Creates API builder for local development/testing:
- `agent`: Your BaseAgent instance
- `response_generator`: Optional custom ResponseGenerator (defaults to SimpleAgentResponseGenerator)  
- `in_memory`: Use InMemoryThreadRepository (True) vs LocalFileThreadRepository (False, default)

#### `ApiBuilder.stateful(repository, authorizer, agent=None, response_generator=None)`
Creates API builder with custom storage and authorization:
- `repository`: BaseThreadRepository implementation for persistence
- `authorizer`: BaseAuthorizer implementation for user management
- `agent`: Optional BaseAgent instance
- `response_generator`: Optional ResponseGenerator

#### `build_thread_router() -> APIRouter`
Returns FastAPI APIRouter with all thread management endpoints configured.

## Generated API Endpoints

The `build_thread_router()` method creates these REST endpoints:

### Thread Management
- **POST** `/threads` - Create new thread
  - Request: `CreateThreadRequest`
  - Response: `ThreadResponse`
  
- **GET** `/threads/{thread_id}` - Get thread with messages
  - Response: `ThreadResponse`
  
- **DELETE** `/threads/{thread_id}` - Delete thread
  - Response: `{"message": "Thread deleted successfully"}`

- **GET** `/threads` - List threads with filtering
  - Query params: `thread_type`, `title_contains`, `min_messages`, `max_messages`, `hours_ago`
  - Response: `ListThreadsResponse`

### Message Management  
- **POST** `/threads/{thread_id}/messages` - Create message (non-streaming)
  - Request: `CreateMessageRequest`
  - Response: `MessageResponse`

- **POST** `/threads/{thread_id}/messages/stream` - Create message with streaming response
  - Request: `CreateMessageRequest` 
  - Response: Server-Sent Events stream

- **GET** `/threads/{thread_id}/messages` - Get thread messages
  - Response: `List[MessageResponse]`

- **GET** `/threads/{thread_id}/messages/{message_id}` - Get specific message
  - Response: `MessageResponse`

- **DELETE** `/threads/{thread_id}/messages/{message_id}` - Delete message
  - Response: `{"message": "Message deleted successfully"}`

## Request/Response Models

Located in `spaik_sdk/server/services/thread_models.py`:

### Request Models
```python
class CreateThreadRequest(BaseModel):
    job_id: Optional[str] = "unknown"

class CreateMessageRequest(BaseModel):
    content: str
```

### Response Models
```python
class ThreadResponse(BaseModel):
    id: str
    messages: List[MessageResponse]

class MessageResponse(BaseModel):
    id: str
    ai: bool
    author_id: str
    author_name: str
    timestamp: int
    blocks: List[MessageBlockResponse]

class ListThreadsResponse(BaseModel):
    threads: List[ThreadMetadataResponse] 
    total_count: int

class ThreadMetadataResponse(BaseModel):
    thread_id: str
    title: str
    message_count: int
    last_activity_time: int
    created_at: int
    author_id: str
    type: str
```

## Storage Repositories

Available storage implementations for persistence:

### InMemoryThreadRepository
```python
from spaik_sdk.server.storage.impl.in_memory_thread_repository import InMemoryThreadRepository

# For testing/development only
repository = InMemoryThreadRepository()
```

### LocalFileThreadRepository  
```python
from spaik_sdk.server.storage.impl.local_file_thread_repository import LocalFileThreadRepository

# File-based persistence 
repository = LocalFileThreadRepository()
```

### Custom Repository
Implement `BaseThreadRepository` for custom storage (database, etc.):
```python
from spaik_sdk.server.storage.base_thread_repository import BaseThreadRepository

class MyRepository(BaseThreadRepository):
    async def save_thread(self, thread_container):
        # Your implementation
        pass
    
    async def load_thread(self, thread_id):
        # Your implementation
        pass
    # ... other required methods
```

## Authorization Interface

### DummyAuthorizer (Default)
Built-in authorizer that allows all operations - used automatically with `ApiBuilder.local()`.

### Custom Authorization
Implement `BaseAuthorizer` for custom user management:
```python
from spaik_sdk.server.authorization.base_authorizer import BaseAuthorizer
from spaik_sdk.server.authorization.base_user import BaseUser

class MyAuthorizer(BaseAuthorizer):
    async def get_user(self, request) -> BaseUser:
        # Extract user from request
        pass
        
    async def can_create_thread(self, user) -> bool:
        # Authorization logic
        return True
        
    async def can_read_thread(self, user, thread) -> bool:
        # Authorization logic  
        return True
    # ... other permission methods
```

## Complete Working Example

Based on `examples/backend/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.tools.tool_provider import ToolProvider, tool, BaseTool
from spaik_sdk.server.api.routers.api_builder import ApiBuilder
from spaik_sdk.models.model_registry import ModelRegistry
from typing import List

app = FastAPI(title="Agent SDK Backend", version="0.0.1")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

## Key Usage Notes

1. **Agent Integration**: Pass your `BaseAgent` instance to `ApiBuilder.local()` or `ApiBuilder.stateful()`

2. **Router Integration**: Use `app.include_router(thread_router)` to add endpoints to your FastAPI app

3. **Storage Options**: Choose between in-memory (testing), file-based (development), or custom repository (production)

4. **Authorization**: Use `DummyAuthorizer` for development, implement `BaseAuthorizer` for production user management

5. **Streaming**: The `/messages/stream` endpoint provides Server-Sent Events for real-time responses

6. **Thread Filtering**: Use query parameters in GET `/threads` for filtering thread lists

This covers the complete public server API interface available in the Agent SDK for building server applications.