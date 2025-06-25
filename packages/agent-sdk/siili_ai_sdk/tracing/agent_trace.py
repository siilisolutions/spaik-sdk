import json
import os
import time
from typing import Optional, Type

from pydantic import BaseModel

from siili_ai_sdk.thread.models import MessageBlock, MessageBlockType


class AgentTrace:
    def __init__(self, system_prompt: str, save_name: Optional[str] = None):
        self.system_prompt: str = system_prompt
        self._start_time_monotonic: float = time.monotonic()
        self._steps: list[tuple[float, str]] = []
        self.save_name: Optional[str] = save_name

    def add_step(self, step_content: str) -> None:
        current_time_monotonic: float = time.monotonic()
        elapsed_time: float = current_time_monotonic - self._start_time_monotonic
        self._steps.append((elapsed_time, step_content))
        if self.save_name is not None:
            self.save(self.save_name)

    def add_structured_response_input(self, input: str, model: Type[BaseModel]) -> None:
        self.add_step(f"📄: {input} \n {json.dumps(model.model_json_schema(), indent=2)}")

    def add_structured_response_output(self, output: BaseModel) -> None:
        self.add_step(f"```json\n{json.dumps(output.model_dump(), indent=2)}\n```")

    def add_input(self, input: Optional[str] = None) -> None:
        if input is None:
            return
        self.add_step(f"👤: {input}")

    def add_block(self, block: MessageBlock) -> None:
        if block.type == MessageBlockType.PLAIN:
            self.add_step(f"🤖: {block.content}")
        elif block.type == MessageBlockType.REASONING:
            self.add_step(f"🧠: {block.content}")
        elif block.type == MessageBlockType.TOOL_USE:
            self.add_step(f"🔧: {block.tool_name} {json.dumps(block.tool_call_args, indent=2)}")
        elif block.type == MessageBlockType.ERROR:
            self.add_step(f"🚨: {block.content}")
        else:
            self.add_step(f"❓: {block.content}")

    def to_string(self, include_system_prompt: bool = True) -> str:
        lines: list[str] = []
        if include_system_prompt:
            lines.append("[system prompt]")
            lines.append("")
            lines.append(self.system_prompt)

        for elapsed_seconds, content in self._steps:
            lines.append("")
            lines.append(f"[{elapsed_seconds:.1f}s]")
            lines.append("")
            lines.append(content)

        return "\n".join(lines)

    def save(self, name: str) -> None:
        file_path: str = f"traces/{name}.txt"
        system_prompt_path: str = f"traces/{name}_system_prompt.txt"

        self.save_to_file(file_path)
        with open(system_prompt_path, "w", encoding="utf-8") as f:
            f.write(self.system_prompt)

    def save_to_file(self, file_path: str) -> None:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        trace_content = self.to_string(include_system_prompt=False)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(trace_content)
