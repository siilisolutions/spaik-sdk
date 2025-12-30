from contextlib import asynccontextmanager
from typing import AsyncIterator, List

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.models.model_registry import ModelRegistry
from siili_ai_sdk.server.api.routers.api_builder import ApiBuilder
from siili_ai_sdk.tools.tool_provider import BaseTool, ToolProvider, tool

load_dotenv()


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


class MinimalAgent(BaseAgent):
    pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    agent = DemoAgent(llm_model=ModelRegistry.CLAUDE_4_SONNET)

    api_builder = ApiBuilder.local(agent=agent)
    thread_router = api_builder.build_thread_router()
    app.include_router(thread_router)
    yield


app = FastAPI(title="Agent SDK Backend Example", version="0.0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_server() -> None:
    """Run the uvicorn server"""
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")


if __name__ == "__main__":
    run_server()
