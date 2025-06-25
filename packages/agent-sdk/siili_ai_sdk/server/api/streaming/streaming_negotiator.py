from abc import ABC, abstractmethod

from siili_ai_sdk.server.api.streaming.negotiate_streaming_response import NegotiateStreamingResponse
from siili_ai_sdk.server.authorization.base_user import BaseUser


class StreamingNegotiator(ABC):
    @abstractmethod
    def negotiate_thread_streaming(self, thread_id: str, user: BaseUser) -> NegotiateStreamingResponse:
        pass
