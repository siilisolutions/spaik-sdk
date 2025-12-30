from typing import List

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.models.model_registry import ModelRegistry
from siili_ai_sdk.server.api.routers.api_builder import ApiBuilder
from siili_ai_sdk.tools.tool_provider import BaseTool, ToolProvider, tool

load_dotenv()

# FastAPI app
app = FastAPI(title="Agent SDK Backend Example", version="0.0.1")

# Add CORS middleware
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

class MinimalAgent(BaseAgent):
    pass

@app.on_event("startup")
async def startup_event():

    agent = DemoAgent(llm_model=ModelRegistry.CLAUDE_4_SONNET)
    
    api_builder = ApiBuilder.local(agent=agent)
    thread_router = api_builder.build_thread_router()
    app.include_router(thread_router)


def run_server():
    """Run the uvicorn server"""
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")


if __name__ == "__main__":
    run_server()
