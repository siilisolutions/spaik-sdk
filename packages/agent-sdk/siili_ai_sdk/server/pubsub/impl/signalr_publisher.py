import json
from typing import Any, Dict

from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


# TODO turn into proper events, consider taking it to a different azure lib
class SignalRPublisher:
    """Azure SignalR publisher"""

    def __init__(self, config, signalr_out):
        """
        Args:
            signalr_out: Azure Functions SignalR output binding (func.Out[str])
        """
        # super().__init__(config)
        self.signalr_out = signalr_out

    def publish_event(self, event: Dict[str, Any], job_id: str) -> None:
        """Publish event to Azure SignalR"""

        # SignalR message format
        signalr_message = {
            "target": "agentEvent",  # Client-side method name
            "arguments": [event],
        }

        # Send to SignalR
        message_json = json.dumps(signalr_message)
        self.signalr_out.set(message_json)

        job_id = event.get("job_id", "unknown")
        event_type = event.get("event_type", "unknown")
        logger.debug(f"Published {event_type} to SignalR for job {job_id}")
