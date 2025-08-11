from re import A
from typing import AsyncGenerator
import anyio
from claude_code_sdk import TextBlock, query, AssistantMessage
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

class ClaudeAgent:
    def __init__(self, options: ClaudeCodeOptions = ClaudeCodeOptions(), yolo: bool = False):
        self.options = options
        if yolo:
            self.options.permission_mode = "bypassPermissions"



    def run(self, prompt: str) -> None:
        async def run():
            async for message in self.stream(prompt):
                print(message)
        
        anyio.run(run)


    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        async with ClaudeSDKClient(
            options=self.options
        ) as client:
            await client.query(prompt=prompt)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            yield block.text
                