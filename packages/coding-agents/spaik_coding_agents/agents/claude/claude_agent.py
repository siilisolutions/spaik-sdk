from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

import anyio
from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient
from spaik_sdk import MessageBlock

from ..base import BaseCodingAgent, CommonOptions
from .to_sdk_message import to_sdk_message_blocks


@dataclass
class ClaudeAgentOptions(CommonOptions):
    """Claude-specific options extending common options"""
    # Claude-specific settings can be added here
    max_turns: Optional[int] = None
    system_prompt: Optional[str] = None


class ClaudeAgent(BaseCodingAgent):
    """Wrapper for Claude Code SDK that integrates with the Siili AI SDK"""
    
    def __init__(self, options: Optional[ClaudeAgentOptions] = None):
        opts = options or ClaudeAgentOptions()
        super().__init__(opts)
        self.options = opts
        self._claude_options = self._build_claude_options()
        self._post_init()
    
    def _build_claude_options(self) -> ClaudeCodeOptions:
        """Build ClaudeCodeOptions from our options"""
        claude_opts = ClaudeCodeOptions()
        
        if self.options.working_directory:
            claude_opts.cwd = self.options.working_directory
        if self.options.model:
            claude_opts.model = self.options.model
        if self.options.max_turns:
            claude_opts.max_turns = self.options.max_turns
        if self.options.system_prompt:
            claude_opts.system_prompt = self.options.system_prompt
        # yolo mode -> Claude's bypassPermissions
        if self.common_options.yolo:
            claude_opts.permission_mode = "bypassPermissions"
            
        return claude_opts

    def run(self, prompt: str) -> str:
        """Run Claude Code with the given prompt in blocking mode.
        
        Returns:
            The final result from the agent.
        """
        result_parts: list[str] = []
        
        async def _run():
            async for block in self.stream_blocks(prompt):
                if block.content:
                    result_parts.append(block.content)
        
        anyio.run(_run)
        return "\n".join(result_parts)

    async def stream_blocks(self, prompt: str) -> AsyncGenerator[MessageBlock, None]:
        """Stream response blocks from Claude Code"""
        async with ClaudeSDKClient(options=self._claude_options) as client:
            await client.query(prompt=prompt)

            async for message in client.receive_response():
                blocks = to_sdk_message_blocks(message)
                for block in blocks:
                    yield block
    
    def get_setup_instructions(self) -> str:
        """Return setup instructions for Claude Code."""
        return """Claude Code Setup:

1. Install Claude Code CLI:
   npm install -g @anthropic-ai/claude-code

2. Authenticate:
   claude login

3. Verify installation:
   claude --version

For more info: https://docs.anthropic.com/claude-code"""

