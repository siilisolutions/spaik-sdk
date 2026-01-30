import json
import time
import uuid
from typing import Optional, Type

from pydantic import BaseModel

from spaik_sdk.thread.models import MessageBlock, MessageBlockType
from spaik_sdk.tracing.get_trace_sink import get_trace_sink
from spaik_sdk.tracing.trace_sink import TraceSink


class AgentTrace:
    def __init__(
        self,
        system_prompt: str,
        save_name: Optional[str] = None,
        trace_sink: Optional[TraceSink] = None,
        agent_instance_id: Optional[str] = None,
    ):
        self.system_prompt: str = system_prompt
        self._start_time_monotonic: float = time.monotonic()
        self._steps: list[tuple[float, str]] = []
        self.save_name: Optional[str] = save_name
        self._trace_sink: TraceSink = trace_sink or get_trace_sink()
        # Generate UUID if not provided (backward compatibility)
        self.agent_instance_id: str = agent_instance_id or str(uuid.uuid4())

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
        trace_content = self.to_string(include_system_prompt=False)
        self._trace_sink.save_trace(name, trace_content, self.system_prompt, self.agent_instance_id)
