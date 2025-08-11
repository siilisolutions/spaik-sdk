"""Generic agent"""

import asyncio
import json
from typing import Dict, Any
from siili_ai_sdk.agent.base_agent import BaseAgent

async def execute(ctx: Dict[str, Any]) -> None:
    logger = ctx['logger']
    workspace = ctx['workspace']
    step_with = ctx.get('with', {})
    prompt = step_with['prompt']
    agent=  GeneralAgent(
        system_prompt="You are a helpful assistant that can answer questions and help with tasks.",
    )
    response = await agent.get_response_text_async(prompt)
    logger(f"🤖 Running agent with prompt: {prompt}, response: {response}")
    await asyncio.sleep(0.3)
    logger(f"🎉 Agent completed successfully!") 




class GeneralAgent(BaseAgent):
    pass