"""Spaik persistence metadata around canonical AG-UI messages."""

from dataclasses import dataclass
from typing import Any

from ag_ui.core import Message
from pydantic import BaseModel, Field

from spaik_sdk.llm.cost.cost_estimate import CostEstimate


class Invocation(BaseModel):
    id: str
    message_id: str
    provider: str
    model: str
    usage: dict[str, Any] | None = None
    cost: CostEstimate | None = None


class ThreadEnvelope(BaseModel):
    schema_version: int = 1
    id: str
    owner_id: str = "user"
    created_at: int
    last_activity_time: int
    messages: list[Message] = Field(default_factory=list)
    message_metadata: dict[str, dict[str, Any]] = Field(default_factory=dict)
    invocations: list[Invocation] = Field(default_factory=list)
    # Private provider data is never returned by the public thread API.
    replay: dict[str, dict[str, Any]] = Field(default_factory=dict)
    system_prompt: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass
class ToolCallHistory:
    tool_name: str
    tool_call_id: str
    tool_call_args: dict[str, Any] | None = None
    tool_call_response: str | None = None
    tool_call_error: str | None = None
