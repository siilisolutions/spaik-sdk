import asyncio
import sys
from typing import List

from rich.console import Console
from rich.prompt import Prompt

from siili_ai_sdk.thread.adapters.cli.block_display import BlockDisplayType
from siili_ai_sdk.thread.adapters.cli.display_manager import DisplayManager
from siili_ai_sdk.thread.models import (
    BlockAddedEvent,
    MessageBlockType,
    StreamingEndedEvent,
    StreamingUpdatedEvent,
    ThreadEvent,
    ToolResponseReceivedEvent,
)
from siili_ai_sdk.thread.thread_container import ThreadContainer

SHOULD_INITIALIZE_DISPLAY = False


class LiveCLI:
    """Simple event-driven CLI that listens to ThreadContainer events"""

    def __init__(self, container: ThreadContainer):
        self.container = container
        self.display_manager = DisplayManager()
        self._running = False
        self.console = Console()
        self.events: List[ThreadEvent] = []

    async def run(self, response_stream) -> "LiveCLI":
        """Run the CLI with an async generator stream - handles everything internally"""
        self.start()

        try:
            # Consume the response stream
            async for token_data in response_stream:
                # Stream processing happens automatically via events
                pass

            # Wait for streaming to complete
            await self._wait_for_completion()

        finally:
            self.stop()

        return self

    async def run_interactive(self, agent) -> "LiveCLI":
        """Run the CLI in interactive mode with a BaseAgent"""
        from siili_ai_sdk.agent.base_agent import BaseAgent

        if not isinstance(agent, BaseAgent):
            raise ValueError("Agent must be an instance of BaseAgent")

        # Use simple print statements for cleaner display
        print("\n🤖 Interactive Agent Mode")
        print("Type 'quit', 'exit', or 'q' to stop")
        print("-" * 40)

        while True:
            try:
                # Ensure clean state before input
                sys.stdout.flush()
                sys.stderr.flush()

                # Get user input using Rich's prompt (blocking but clean)
                user_input = await self._get_input_safe()

                # Check for exit commands
                if user_input.lower().strip() in ["quit", "exit", "q"]:
                    print("\n👋 Goodbye!")
                    break

                if not user_input.strip():
                    continue

                # Start live display for response processing
                if self._running:
                    self.stop()
                self.start()

                try:
                    # Get response stream from agent
                    response_stream = agent.get_response_stream(user_input)

                    # Consume the response stream
                    async for token_data in response_stream:
                        # Stream processing happens automatically via events
                        pass

                    # Wait for streaming to complete
                    await self._wait_for_completion()

                finally:
                    # Always stop live display after response with proper cleanup
                    await self._safe_stop()

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Try again...")

        return self

    async def _get_input_safe(self) -> str:
        """Get user input safely without blocking issues"""
        loop = asyncio.get_event_loop()
        try:
            # Use Rich's prompt in executor to avoid blocking
            return await loop.run_in_executor(None, Prompt.ask, "\n💬 You")
        except (EOFError, KeyboardInterrupt):
            return "quit"

    async def _safe_stop(self):
        """Safely stop the display with proper error handling"""
        try:
            # Small delay to let display finish
            await asyncio.sleep(0.2)
            # Flush before stopping
            sys.stdout.flush()
            sys.stderr.flush()
            self.stop()
        except (BlockingIOError, OSError, Exception):
            # If stopping fails, force reset the display state
            self._running = False
            if hasattr(self.display_manager, "live") and self.display_manager.live:
                try:
                    self.display_manager.live = None
                except Exception:
                    pass

    async def _wait_for_completion(self):
        """Wait for streaming to complete"""
        # Wait for streaming to actually start
        await asyncio.sleep(1.0)

        # Wait for completion
        while self.container.is_streaming_active():
            await asyncio.sleep(0.1)

        # Give it a moment to finalize
        await asyncio.sleep(1.0)

    def start(self):
        """Start live display"""
        if self._running:
            return

        self._running = True

        self.display_manager.start()

        # Subscribe to events BEFORE display manager is ready
        self.container.subscribe(self._handle_event)
        # Initialize display with existing blocks
        if SHOULD_INITIALIZE_DISPLAY:
            self._initialize_display()

    def stop(self):
        """Stop live display"""
        if not self._running:
            return

        # Unsubscribe from events FIRST
        self.container.unsubscribe(self._handle_event)

        self._running = False
        self.display_manager.stop()

    def _initialize_display(self):
        """Initialize display with existing blocks from ThreadContainer state"""
        for message in self.container.messages:
            for block in message.blocks:
                display_type = self._get_display_type(block)
                content = self.container.get_block_content(block)
                self.display_manager.add_block(
                    block.id, display_type, content=content, streaming=block.streaming, tool_name=block.tool_name
                )

    def _handle_event(self, event: ThreadEvent):
        """Handle all ThreadContainer events with targeted updates"""
        self.events.append(event)

        if isinstance(event, StreamingUpdatedEvent):
            self.display_manager.update_block_content(event.block_id, event.total_content, streaming=True)

        elif isinstance(event, ToolResponseReceivedEvent):
            if event.block_id:
                self.display_manager.update_tool_result(event.block_id, event.response if not event.error else "", error=event.error)

        elif isinstance(event, BlockAddedEvent):
            # Add the new block to display
            display_type = self._get_display_type(event.block)
            content = self.container.get_block_content(event.block)
            self.display_manager.add_block(
                event.block_id, display_type, content=content, streaming=event.block.streaming, tool_name=event.block.tool_name
            )

        elif isinstance(event, StreamingEndedEvent):
            for block_id in event.completed_blocks:
                self.display_manager.update_block_content(block_id, streaming=False)

    def _find_block_by_id(self, block_id: str):
        """Find a block by its ID"""
        for message in self.container.messages:
            for block in message.blocks:
                if block.id == block_id:
                    return block
        return None

    def _find_tool_block_by_call_id(self, tool_call_id: str):
        """Find a tool block by its call ID"""
        for message in self.container.messages:
            for block in message.blocks:
                if block.type == MessageBlockType.TOOL_USE and block.tool_call_id == tool_call_id:
                    return block
        return None

    def _get_display_type(self, block) -> BlockDisplayType:
        """Convert MessageBlockType to BlockDisplayType"""
        if block.type == MessageBlockType.REASONING:
            return BlockDisplayType.REASONING
        elif block.type == MessageBlockType.PLAIN:
            return BlockDisplayType.RESPONSE
        elif block.type == MessageBlockType.TOOL_USE:
            return BlockDisplayType.TOOL_CALL
        elif block.type == MessageBlockType.ERROR:
            return BlockDisplayType.ERROR
        else:
            return BlockDisplayType.RESPONSE  # fallback
