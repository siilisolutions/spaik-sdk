from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from siili_ai_sdk.thread.models import MessageBlockType


class MessageBlockRequest(BaseModel):
    type: MessageBlockType
    content: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_call_args: Optional[Dict[str, Any]] = None
    tool_name: Optional[str] = None


class MessageBlockResponse(BaseModel):
    id: str
    streaming: bool
    type: MessageBlockType
    content: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_call_args: Optional[Dict[str, Any]] = None
    tool_name: Optional[str] = None
    tool_call_response: Optional[str] = None
    tool_call_error: Optional[str] = None


class UpdateMessageRequest(BaseModel):
    blocks: Optional[List[MessageBlockRequest]] = None


class MessageResponse(BaseModel):
    id: str
    ai: bool
    author_id: str
    author_name: str
    timestamp: int
    blocks: List[MessageBlockResponse]


class CreateMessageRequest(BaseModel):
    content: str
    # TODO add metadata and whatnot


class CreateThreadRequest(BaseModel):
    job_id: Optional[str] = "unknown"
    # TODO add metadata, remove job_id


class ThreadResponse(BaseModel):
    id: str
    messages: List[MessageResponse]


class ThreadMetadataResponse(BaseModel):
    thread_id: str
    title: str
    message_count: int
    last_activity_time: int
    created_at: int
    author_id: str
    type: str


class ListThreadsRequest(BaseModel):
    author_id: Optional[str] = None
    thread_type: Optional[str] = None
    title_contains: Optional[str] = None
    min_messages: Optional[int] = None
    max_messages: Optional[int] = None
    hours_ago: Optional[int] = None


class ListThreadsResponse(BaseModel):
    threads: List[ThreadMetadataResponse]
    total_count: int
