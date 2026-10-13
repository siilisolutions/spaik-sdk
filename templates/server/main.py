from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from spaik_sdk import BaseAgent
from spaik_sdk.server.api.routers.api_builder import ApiBuilder
from spaik_sdk.tools.tool_provider import tool

load_dotenv()


@tool
def greeting(name: str) -> str:
    """Return a personal greeting."""
    return f"Hello, {name}!"


app = FastAPI(title="Spaik AG-UI example")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
agent = BaseAgent(system_prompt="You are a helpful assistant. Use the greeting tool when appropriate.", tools=[greeting])
api = ApiBuilder.local(agent=agent)
app.include_router(api.build_thread_router())
app.include_router(api.build_file_router())
app.include_router(api.build_audio_router())
