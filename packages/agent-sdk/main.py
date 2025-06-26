#!/usr/bin/env python3

from dotenv import load_dotenv
from pydantic import BaseModel

from siili_ai_sdk.demo_agents.minimal_agent import MinimalAgent
from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.models.model_registry import ModelRegistry
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


# Load environment variables from .env file


class DummySchema(BaseModel):
    joke: str
    explanation: str

# agent = MinimalAgent(llm_model=ModelRegistry.GEMINI_2_5_FLASH)
agent = MinimalAgent(llm_model=ModelRegistry.CLAUDE_4_SONNET)

async def main() -> None:

    
    # response = agent.get_structured_response("create a joke about a cat", DummySchema)
    # print(response)
    # agent.thread_container.print_all()
    # agent = DemoAgent()
    # agent.run_cli()
    #print(agent.get_response_text("hello"))
    async for event in agent.get_event_stream("hello"):
        print(event)
        
    # agent.thread_container.print_all()

    # asyncio.run(agent.run("hello"))
    # asyncio.run(agent.run_interactive())
    # agent.run_sync("hello")
    # asyncio.run(agent.run_stream_tokens("jeejeejee"))
    # asyncio.run(agent.run_stream_tokens("joojoojoo"))llm_model=LLMModel.GEMINI_2_5_FLASH
    # asyncio.run(agent.run_stream_tokens("derp"))

    # agent.run_sync("koitan testata toimiiko taa viestien ketjutus ja annan sulle taikasanan 'kikkelis kokkelis'. toista se kun pyydan")
    # agent.run_sync("toista nyt se taikasana")
    # agent.run_sync("tassa on viesti.ja tassa on seuraava viesti. moi")
    # agent.run_sync("jeejeejee")
    # agent.run_sync(" <<<< toista mulle numeroituna listana kaikki viestit mita oot saanut")


if __name__ == "__main__":
    load_dotenv()

    import asyncio
    asyncio.run(main())
    asyncio.run(main())
