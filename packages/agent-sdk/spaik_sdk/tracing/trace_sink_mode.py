from enum import Enum
from typing import Optional


class TraceSinkMode(Enum):
    LOCAL = "local"
    NOOP = "noop"

    @classmethod
    def from_name(cls, name: Optional[str]) -> Optional["TraceSinkMode"]:
        """Convert a string name to a TraceSinkMode.

        Args:
            name: The mode name ("local", "noop") or None/empty string.

        Returns:
            The corresponding TraceSinkMode, or None if name is empty/None.
            Returns None for unrecognized values (silent fallthrough to default behavior).
        """
        if not name:
            return None

        for mode in cls:
            if mode.value == name.lower():
                return mode

        # Unknown values fall through to None (let get_trace_sink handle default)
        return None
