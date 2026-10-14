from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from spaik_sdk import BaseAgent
from spaik_sdk.server.api.routers.api_builder import ApiBuilder
from spaik_sdk.tools.tool_provider import tool

load_dotenv()


@tool
def current_time(timezone: str) -> str:
    """Return the current date and time in an IANA timezone such as Europe/Helsinki or America/New_York."""
    try:
        return datetime.now(ZoneInfo(timezone)).strftime("%A %d %B %Y, %H:%M %Z")
    except (ZoneInfoNotFoundError, ValueError):
        return f"Unknown timezone '{timezone}'. Use an IANA name such as Europe/Helsinki."


app = FastAPI(title="Spaik Agent API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
agent = BaseAgent(
    system_prompt="You are a helpful assistant. Answer clearly and concisely. Use current_time for questions about dates and times.",
    tools=[current_time],
)
api = ApiBuilder.local(agent=agent)
app.include_router(api.build_thread_router())
app.include_router(api.build_file_router())
app.include_router(api.build_audio_router())
