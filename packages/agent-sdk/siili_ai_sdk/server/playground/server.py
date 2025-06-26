import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from siili_ai_sdk.demo_agents.demo_agent import DemoAgent
from siili_ai_sdk.recording.impl.local_recorder import LocalRecorder
from siili_ai_sdk.server.api.routers.api_builder import ApiBuilder
from siili_ai_sdk.models.model_registry import ModelRegistry
from siili_ai_sdk.utils.init_logger import init_logger

load_dotenv()
logger = init_logger(__name__)

# FastAPI app
app = FastAPI(title="Agent SDK Playground", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Agent SDK Playground server...")

    # Initialize agent and processor
    # recorder=LocalRecorder(recording_name="test")
    # playback=LocalPlayback(recording_name="test")
    # recorder=LocalRecorder.create_conditional_recorder(recording_name="mystery_streaming_issue_claude_4_sonnet", delay=0.05)
    recorder=None
    # api_builder = ApiBuilder.local(agent=DemoAgent(llm_model=ModelRegistry.GEMINI_2_5_FLASH))
    agent= DemoAgent(llm_model=ModelRegistry.CLAUDE_4_SONNET, recorder=recorder)
    api_builder = ApiBuilder.local(agent=agent)
    thread_router = api_builder.build_thread_router()
    app.include_router(thread_router)

    logger.info("Server initialized successfully")


# Job and Thread endpoints are now handled by their respective RouterFactories


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Agent SDK Playground is running"}


def run_server():
    """Run the uvicorn server"""
    uvicorn.run("siili_ai_sdk.server.playground.server:app", host="0.0.0.0", port=8000, reload=True, log_level="info")


if __name__ == "__main__":
    run_server()
