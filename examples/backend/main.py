import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, List

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.attachments import get_or_create_file_storage
from siili_ai_sdk.image_gen import ImageGenerator, ImageGenOptions, ImageFormat
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


class ImageGeneratorTool(ToolProvider):
    """Tool provider for generating and storing images."""

    def get_tools(self) -> List[BaseTool]:
        @tool
        async def generate_image(prompt: str) -> str:
            """
            Generate an image based on a text prompt and store it in the file service.
            
            After calling this tool, you MUST include the image in your response using:
            <StoredImage id="THE_FILE_ID_RETURNED" />
            
            This will render the generated image inline in your message.
            
            Args:
                prompt: A detailed description of the image to generate.
                        Be specific about style, content, colors, composition, etc.
            
            Returns:
                The file ID of the stored image. Use this ID with <StoredImage id="..." /> tag.
            """
            # Get the file storage instance
            file_storage = get_or_create_file_storage()
            
            # Create image generator (uses env var for model, defaults to gpt-image-1)
            generator = ImageGenerator(
                model="gpt-image-1",  # OpenAI's DALL-E model
                output_dir="/tmp/agent-images",
            )
            
            # Generate the image
            options = ImageGenOptions(
                width=1024,
                height=1024,
                output_format=ImageFormat.PNG,
            )
            
            image_path = await generator.generate_image(prompt=prompt, options=options)
            
            # Read the image bytes and store via file service
            image_bytes = image_path.read_bytes()
            
            # Store in file service
            # Use "system" as owner for agent-generated content (readable by all users)
            metadata = await file_storage.store(
                data=image_bytes,
                mime_type="image/png",
                owner_id="system",
                filename=image_path.name,
            )
            
            # Clean up temp file
            image_path.unlink(missing_ok=True)
            
            return metadata.file_id

        return [generate_image]


class DemoAgent(BaseAgent):
    """Demo agent with greeting tools and image generation capability."""

    def get_system_prompt(self) -> str:
        return """You are a helpful AI assistant with the ability to generate images.

When the user asks you to create, draw, or generate an image:
1. Call the generate_image tool with a detailed prompt
2. After receiving the file_id, include the image in your response using: <StoredImage id="FILE_ID_HERE" />
3. Add a brief description of what you created

Example response after generating an image:
"Here's the image I created for you:

<StoredImage id="abc123-def456" />

I generated a [description of the image based on the prompt]."

Always be creative and helpful!"""

    def get_tool_providers(self) -> List[ToolProvider]:
        return [DemoTool(), ImageGeneratorTool()]


class MinimalAgent(BaseAgent):
    pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    agent = DemoAgent(llm_model=ModelRegistry.CLAUDE_4_SONNET)

    api_builder = ApiBuilder.local(agent=agent)
    thread_router = api_builder.build_thread_router()
    file_router = api_builder.build_file_router()
    audio_router = api_builder.build_audio_router()  # TTS/STT endpoints
    app.include_router(thread_router)
    app.include_router(file_router)
    app.include_router(audio_router)
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
