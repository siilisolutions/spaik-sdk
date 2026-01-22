from typing import Any, Dict

from pydantic import BaseModel


class NegotiateStreamingResponse(BaseModel):
    mode: str
    config: Dict[str, Any]
