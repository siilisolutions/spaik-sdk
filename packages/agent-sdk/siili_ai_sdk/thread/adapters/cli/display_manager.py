from typing import Dict, Optional

from rich.console import Console, Group
from rich.live import Live
from rich.text import Text

from siili_ai_sdk.thread.adapters.cli.block_display import BlockDisplay, BlockDisplayType


class DisplayManager:
    """Manages Rich component mappings and targeted updates"""

    def __init__(self):
        self.console = Console()
        self.live: Optional[Live] = None
        self.blocks: Dict[str, BlockDisplay] = {}  # block_id -> BlockDisplay
        self._running = False

    def start(self):
        """Start live display"""
        if self._running:
            return

        self._running = True

        self.live = Live(self._create_initial_display(), console=self.console, refresh_per_second=10)
        self.live.start()

    def stop(self):
        """Stop live display"""
        if not self._running:
            return

        self._running = False
        self.blocks = {}
        if self.live:
            try:
                self.live.stop()
            except (BlockingIOError, OSError):
                # Rich display cleanup failed, but that's ok
                # This can happen when stdout buffer is full/blocked
                pass

    def _create_initial_display(self):
        """Create the initial display"""
        return Text("Waiting for activity...")

    def update_block_content(self, block_id: str, content: Optional[str] = None, streaming: bool = False):
        """Update a block's content"""
        if block_id in self.blocks:
            if content:
                self.blocks[block_id].content = content
            self.blocks[block_id].streaming = streaming
            self._refresh_display()

    def update_tool_result(self, block_id: str, result: str, error: Optional[str] = None):
        """Update a tool block's result"""
        if block_id in self.blocks:
            if error:
                self.blocks[block_id].tool_error = error
            else:
                self.blocks[block_id].content = result
            self.blocks[block_id].streaming = False
            self._refresh_display()

    def add_block(
        self, block_id: str, display_type: BlockDisplayType, content: str = "", streaming: bool = False, tool_name: Optional[str] = None
    ):
        """Add a new block"""
        self.blocks[block_id] = BlockDisplay(
            block_id=block_id, display_type=display_type, content=content, streaming=streaming, tool_name=tool_name
        )
        self._refresh_display()

    def _refresh_display(self):
        """Refresh the live display with current panels"""
        if not self.live:
            return

        panels = [block.to_panel() for block in self.blocks.values()]
        if panels:
            self.live.update(Group(*panels))
        else:
            self.live.update(Text("Waiting for activity..."))
