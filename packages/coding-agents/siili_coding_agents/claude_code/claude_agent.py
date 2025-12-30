from typing import AsyncGenerator

import anyio
from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient
from siili_ai_sdk import MessageBlock

from siili_coding_agents.claude_code.to_sdk_message import to_sdk_message_blocks


class ClaudeAgent:
    def __init__(self, options: ClaudeCodeOptions = ClaudeCodeOptions(), yolo: bool = False):
        self.options = options
        if yolo:
            self.options.permission_mode = "bypassPermissions"



    def run(self, prompt: str) -> None:
        async def run():
            async for message in self.stream_blocks(prompt):
                print(message)
        
        anyio.run(run)


    async def stream_blocks(self, prompt: str) -> AsyncGenerator[MessageBlock, None]:
        async with ClaudeSDKClient(
            options=self.options
        ) as client:
            await client.query(prompt=prompt)

            async for message in client.receive_response():
                blocks = to_sdk_message_blocks(message)
                for block in blocks:
                    yield block
                
