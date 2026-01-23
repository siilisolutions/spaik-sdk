from enum import Enum


class PromptLoaderMode(Enum):
    LOCAL = "local"

    @classmethod
    def from_name(cls, name: str) -> "PromptLoaderMode":
        for mode in cls:
            if mode.value == name:
                return mode

        available_modes = [mode.value for mode in cls]
        raise ValueError(f"Unknown PromptLoaderMode '{name}'. Available: {', '.join(available_modes)}")
