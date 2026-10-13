from typing import Any

from pydantic import BaseModel, Field


class CreateThreadRequest(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)
