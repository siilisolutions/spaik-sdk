from enum import Enum


class TraceSinkMode(Enum):
    LOCAL = "local"

    @classmethod
    def from_name(cls, name: str) -> "TraceSinkMode":
        for mode in cls:
            if mode.value == name:
                return mode

        available_modes = [mode.value for mode in cls]
        raise ValueError(f"Unknown TraceSinkMode '{name}'. Available: {', '.join(available_modes)}")
