import warnings

from .agents.base import AgentConnectionError, BaseCodingAgent, CommonOptions
from .agents.claude.claude_agent import ClaudeAgent, ClaudeAgentOptions
from .agents.cursor.cursor_agent import CursorAgent, CursorAgentOptions
from .git.changes import ChangeType, FileChange, GitChanges, get_changes

warnings.warn(
    "spaik-coding-agents is deprecated and requires spaik-sdk==0.11.1; it does not support Spaik 1.0.", FutureWarning, stacklevel=2
)

__all__ = [
    "AgentConnectionError",
    "BaseCodingAgent",
    "CommonOptions",
    "ClaudeAgent",
    "ClaudeAgentOptions",
    "CursorAgent",
    "CursorAgentOptions",
    "ChangeType",
    "FileChange",
    "GitChanges",
    "get_changes",
]
