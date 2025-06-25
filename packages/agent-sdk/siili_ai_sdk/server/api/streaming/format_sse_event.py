import json
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel

from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class EventStreamResponse(BaseModel):
    event: Optional[str] = None
    payload: Union[str, dict[str, Any]]


def format_sse_event(event_response: Dict[str, Any]) -> str:
    """Format EventStreamResponse as SSE data"""

    # Build SSE message
    sse_lines: list[str] = []

    # Add event type if present
    if event_response.get("event_type"):
        sse_lines.append(f"event: {event_response['event_type']}")

    payload_obj = event_response.get("data")

    # Serialize payload to JSON-safe string
    try:
        if isinstance(payload_obj, str):
            data_content = payload_obj
        else:
            data_content = json.dumps(payload_obj)
    except Exception as err:
        logger.warning(f"Failed to JSON serialize payload ({err}), using repr")
        data_content = repr(payload_obj)

    sse_lines.append(f"data: {data_content}")

    # SSE format requires double newline at end
    return "\n".join(sse_lines) + "\n\n"
