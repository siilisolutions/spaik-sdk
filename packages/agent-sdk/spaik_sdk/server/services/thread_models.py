from typing import Any

from ag_ui.core import Message
from pydantic import BaseModel, Field


class CreateThreadRequest(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)


class ThreadResponse(BaseModel):
    id: str
    owner_id: str
    created_at: int
    last_activity_time: int
    messages: list[Message]
    message_metadata: dict[str, dict[str, Any]] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
