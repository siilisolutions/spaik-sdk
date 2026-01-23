import os
from typing import Optional

from spaik_sdk.tracing.trace_sink import TraceSink


class LocalTraceSink(TraceSink):
    """TraceSink implementation that writes traces to the local filesystem."""

    def __init__(self, traces_dir: Optional[str] = None):
        self.traces_dir = traces_dir or "traces"

    def save_trace(self, name: str, trace_content: str, system_prompt: str) -> None:
        os.makedirs(self.traces_dir, exist_ok=True)

        trace_path = os.path.join(self.traces_dir, f"{name}.txt")
        system_prompt_path = os.path.join(self.traces_dir, f"{name}_system_prompt.txt")

        with open(trace_path, "w", encoding="utf-8") as f:
            f.write(trace_content)

        with open(system_prompt_path, "w", encoding="utf-8") as f:
            f.write(system_prompt)
