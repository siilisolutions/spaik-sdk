import uuid
from typing import List

from siili_ai_sdk.server.services.thread_models import (
    MessageBlockRequest,
    MessageBlockResponse,
    MessageResponse,
    ThreadMetadataResponse,
    ThreadResponse,
)
from siili_ai_sdk.server.storage.thread_metadata import ThreadMetadata
from siili_ai_sdk.thread.models import MessageBlock, ThreadMessage
from siili_ai_sdk.thread.thread_container import ThreadContainer


class ThreadConverters:
    """Utility class for converting between internal and API models"""

    @staticmethod
    def block_request_to_model(request: MessageBlockRequest) -> MessageBlock:
        """Convert MessageBlockRequest to MessageBlock"""
        return MessageBlock(
            id=str(uuid.uuid4()),
            streaming=False,
            type=request.type,
            content=request.content,
            tool_call_id=request.tool_call_id,
            tool_call_args=request.tool_call_args,
            tool_name=request.tool_name,
        )

    @staticmethod
    def block_model_to_response(block: MessageBlock) -> MessageBlockResponse:
        """Convert MessageBlock to MessageBlockResponse"""
        return MessageBlockResponse(
            id=block.id,
            streaming=block.streaming,
            type=block.type,
            content=block.content,
            tool_call_id=block.tool_call_id,
            tool_call_args=block.tool_call_args,
            tool_name=block.tool_name,
            tool_call_response=block.tool_call_response,
            tool_call_error=block.tool_call_error,
        )

    @staticmethod
    def message_model_to_response(message: ThreadMessage) -> MessageResponse:
        """Convert ThreadMessage to MessageResponse"""
        return MessageResponse(
            id=message.id,
            ai=message.ai,
            author_id=message.author_id,
            author_name=message.author_name,
            timestamp=message.timestamp,
            blocks=[ThreadConverters.block_model_to_response(block) for block in message.blocks],
        )

    @staticmethod
    def messages_model_to_response(messages: List[ThreadMessage]) -> List[MessageResponse]:
        """Convert list of ThreadMessage to list of MessageResponse"""
        return [ThreadConverters.message_model_to_response(msg) for msg in messages]

    @staticmethod
    def thread_model_to_response(thread: ThreadContainer) -> ThreadResponse:
        """Convert ThreadContainer to ThreadResponse"""
        return ThreadResponse(
            id=thread.thread_id,
            messages=[ThreadConverters.message_model_to_response(msg) for msg in thread.messages],
        )

    @staticmethod
    def metadata_model_to_response(metadata: ThreadMetadata) -> ThreadMetadataResponse:
        """Convert ThreadMetadata to ThreadMetadataResponse"""
        return ThreadMetadataResponse(
            thread_id=metadata.thread_id,
            title=metadata.title,
            message_count=metadata.message_count,
            last_activity_time=metadata.last_activity_time,
            created_at=metadata.created_at,
            author_id=metadata.author_id,
            type=metadata.type,
        )

    @staticmethod
    def metadata_list_to_response(metadata_list: List[ThreadMetadata]) -> List[ThreadMetadataResponse]:
        """Convert list of ThreadMetadata to list of ThreadMetadataResponse"""
        return [ThreadConverters.metadata_model_to_response(metadata) for metadata in metadata_list]
