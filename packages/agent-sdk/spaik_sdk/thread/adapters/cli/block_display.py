import time
from enum import Enum
from typing import Optional

from rich.panel import Panel
from rich.text import Text


class BlockDisplayType(Enum):
    REASONING = "reasoning"
    RESPONSE = "response"
    TOOL_CALL = "tool_call"
    ERROR = "error"


class BlockDisplay:
    """Represents a displayable block with content and styling info"""

    def __init__(
        self,
        block_id: str,
        display_type: BlockDisplayType,
        content: str = "",
        streaming: bool = False,
        tool_name: Optional[str] = None,
        tool_error: Optional[str] = None,
    ):
        self.block_id = block_id
        self.display_type = display_type
        self.content = content
        self.streaming = streaming
        self.tool_name = tool_name
        self.tool_error = tool_error
        self.created_at = time.time()

    def to_panel(self) -> Panel:
        """Convert this block to a Rich Panel"""
        if self.display_type == BlockDisplayType.REASONING:
            text = Text()
            text.append("🧠 ", style="blue bold")
            display_content = self.content[:400] + ("..." if len(self.content) > 400 else "")
            if self.streaming:
                text.append(display_content, style="blue")
            else:
                text.append(display_content)

            title = "AI Thinking" + (" 🌊" if self.streaming else " ✅")
            return Panel(text, title=title, border_style="blue")

        elif self.display_type == BlockDisplayType.RESPONSE:
            text = Text()
            text.append("🤖 ", style="green bold")
            text.append(self.content)

            title = f"Response ({self.block_id[:8]})" + (" 🌊" if self.streaming else " ✅")
            return Panel(text, title=title, border_style="green")

        elif self.display_type == BlockDisplayType.TOOL_CALL:
            text = Text()
            text.append("🔧 ", style="yellow bold")
            text.append(f"{self.tool_name or 'unknown'}", style="yellow")

            if self.streaming:
                text.append(" (running...)", style="bright_black")
            elif self.tool_error:
                text.append(f"\n\n→ Error:\n{self.tool_error}", style="red")
                title = f"Tool: {self.tool_name} ❌"
                border_style = "red"
            elif self.content:
                result = self.content[:200] + ("..." if len(self.content) > 200 else "")
                text.append(f"\n\n→ Result:\n{result}", style="green")
                title = f"Tool: {self.tool_name} ✅"
                border_style = "green"
            else:
                title = f"Tool: {self.tool_name} ⏳"
                border_style = "bright_black"

            if self.streaming:
                title = f"Tool: {self.tool_name} 🌊"
                border_style = "yellow"
            elif not hasattr(locals(), "title"):
                title = f"Tool: {self.tool_name} ⏳"
                border_style = "bright_black"

            return Panel(text, title=title, border_style=border_style)

        elif self.display_type == BlockDisplayType.ERROR:
            text = Text()
            text.append("❌ Error", style="red bold")
            return Panel(text, title="Error", border_style="red")

        return Panel("Unknown block type")
