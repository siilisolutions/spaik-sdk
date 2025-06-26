# Agent SDK Backend Example

This is a FastAPI backend example that demonstrates how to use the Agent SDK to create a web API with agent capabilities.

## Features

- FastAPI server with Agent SDK integration
- Thread-based conversation management
- Multiple LLM model support (Claude, GPT, Gemini)
- CORS enabled for frontend integration
- Built-in health check endpoint

## Setup

1. **Install dependencies:**
   ```bash
   cd examples/backend
   uv sync
   ```

2. **Set up environment variables:**
   Create a `.env` file in this directory with your API keys:
   ```bash
   # Choose the API key for your preferred model
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   ```

3. **Run the server:**
   ```bash
   uv run python main.py
   ```

   Or with uvicorn directly:
   ```bash
   uv run uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

## Usage

Once running, the server will be available at `http://localhost:8001`:

- **Health Check:** `GET /health`
- **API Documentation:** `GET /docs` (Swagger UI)
- **Thread Management:** `POST /threads` to create conversations
- **Chat:** Use the thread endpoints to have conversations with the agent

## Configuration

You can easily switch between different LLM models by modifying the agent initialization in `main.py`:

```python
# Choose your preferred model
agent = DemoAgent(llm_model=ModelRegistry.CLAUDE_4_SONNET)
# agent = DemoAgent(llm_model=ModelRegistry.GPT_4_O_MINI)  
# agent = DemoAgent(llm_model=ModelRegistry.GEMINI_2_5_FLASH)
```

## Integration with Frontend

This backend is designed to work with the frontend example in `../frontend`. The CORS settings allow cross-origin requests from any domain, making it easy to integrate with web frontends.

## API Endpoints

The server automatically includes thread management endpoints:

- `POST /threads` - Create a new conversation thread
- `GET /threads` - List all threads
- `GET /threads/{thread_id}` - Get a specific thread
- `POST /threads/{thread_id}/messages` - Send a message to a thread
- `DELETE /threads/{thread_id}` - Delete a thread

See `/docs` when the server is running for complete API documentation. 