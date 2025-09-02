import json
import time
import uuid
from collections.abc import Callable
from typing import Awaitable, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from siili_ai_sdk.server.api.streaming.streaming_negotiator import StreamingNegotiator
from siili_ai_sdk.server.authorization.base_authorizer import BaseAuthorizer
from siili_ai_sdk.server.authorization.base_user import BaseUser
from siili_ai_sdk.server.authorization.dummy_authorizer import DummyAuthorizer
from siili_ai_sdk.server.job_processor.thread_job_processor import ThreadJobProcessor
from siili_ai_sdk.server.pubsub.cancellation_publisher import CancellationPublisher
from siili_ai_sdk.server.pubsub.cancellation_subscriber import CancellationSubscriber
from siili_ai_sdk.server.queue.agent_job_queue import AgentJob, AgentJobQueue, JobType
from siili_ai_sdk.server.services.thread_converters import ThreadConverters
from siili_ai_sdk.server.services.thread_models import (
    CreateMessageRequest,
    CreateThreadRequest,
    ListThreadsResponse,
    MessageResponse,
    ThreadResponse,
)
from siili_ai_sdk.server.services.thread_service import ThreadService
from siili_ai_sdk.server.storage.thread_filter import ThreadFilter
from siili_ai_sdk.thread.models import MessageAddedEvent, MessageBlock, MessageBlockType, ThreadMessage
from siili_ai_sdk.thread.thread_container import ThreadContainer
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class ThreadRouterFactory:
    def __init__(
        self,
        service: ThreadService,
        authorizer: Optional[BaseAuthorizer[BaseUser]] = None,
        streaming_negotiator: Optional[StreamingNegotiator] = None,
        job_queue: Optional[AgentJobQueue] = None,
        thread_job_processor: Optional[ThreadJobProcessor] = None,
        cancellation_subscriber_provider: Optional[Callable[[str], Awaitable[CancellationSubscriber]]] = None,
        cancellation_publisher: Optional[CancellationPublisher] = None,
    ):
        self.authorizer = authorizer or DummyAuthorizer()
        self.service = service
        self.streaming_negotiator = streaming_negotiator
        self.job_queue = job_queue
        self.thread_job_processor = thread_job_processor
        self.cancellation_subscriber_provider = cancellation_subscriber_provider
        self.cancellation_publisher = cancellation_publisher

    def create_router(self, prefix: str = "/threads") -> APIRouter:
        router = APIRouter(prefix=prefix, tags=["threads"])

        async def get_current_user(request: Request) -> BaseUser:
            user = await self.authorizer.get_user(request)
            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")
            return user

        @router.post("", response_model=ThreadResponse)
        async def create_thread(request: CreateThreadRequest, user: BaseUser = Depends(get_current_user)):
            """Create a new thread"""
            if not await self.authorizer.can_create_thread(user):
                raise HTTPException(status_code=403, detail="Access denied")
            thread_container = ThreadContainer()  # TODO giving no args (eg system prompt) might cause issues
            created_thread = await self.service.create_thread(thread_container)
            return ThreadConverters.thread_model_to_response(created_thread)

        @router.get("/{thread_id}", response_model=ThreadResponse)
        async def get_thread(thread_id: str, user: BaseUser = Depends(get_current_user)):
            """Get thread by ID"""

            thread = await self.service.get_thread(thread_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            if not await self.authorizer.can_read_thread(user, thread):
                raise HTTPException(status_code=403, detail="Access denied")

            return ThreadConverters.thread_model_to_response(thread)

        @router.delete("/{thread_id}")
        async def delete_thread(thread_id: str, user: BaseUser = Depends(get_current_user)):
            """Delete thread"""
            thread = await self.service.get_thread(thread_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            if not await self.authorizer.can_delete_thread(user, thread):
                raise HTTPException(status_code=403, detail="Access denied")

            await self.service.delete_thread(thread_id)
            return {"message": "Thread deleted successfully"}

        @router.get("", response_model=ListThreadsResponse)
        async def list_threads(
            thread_type: Optional[str] = Query(None),
            title_contains: Optional[str] = Query(None),
            min_messages: Optional[int] = Query(None),
            max_messages: Optional[int] = Query(None),
            hours_ago: Optional[int] = Query(None),
            user: BaseUser = Depends(get_current_user),
        ):
            """List threads with filtering"""
            filter_builder = ThreadFilter.builder()

            filter_builder.with_author_id(user.get_id())
            if thread_type:
                filter_builder.with_type(thread_type)
            if title_contains:
                filter_builder.with_title_containing(title_contains)
            if min_messages:
                filter_builder.with_min_messages(min_messages)
            if max_messages:
                filter_builder.with_max_messages(max_messages)
            if hours_ago:
                cutoff = int((time.time() - hours_ago * 3600) * 1000)
                filter_builder.with_activity_after(cutoff)

            filter = filter_builder.build()
            threads = await self.service.list_threads(filter)

            return ListThreadsResponse(threads=ThreadConverters.metadata_list_to_response(threads), total_count=len(threads))

        @router.get("/{thread_id}/messages", response_model=List[MessageResponse])
        async def get_thread_messages(thread_id: str, user: BaseUser = Depends(get_current_user)):
            """Get all messages for a thread"""
            thread = await self.service.get_thread(thread_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            if not await self.authorizer.can_read_thread(user, thread):
                raise HTTPException(status_code=403, detail="Access denied")

            messages = await self.service.get_thread_messages(thread_id)
            return ThreadConverters.messages_model_to_response(messages)

        @router.get("/{thread_id}/messages/{message_id}", response_model=MessageResponse)
        async def get_message(thread_id: str, message_id: str, user: BaseUser = Depends(get_current_user)):
            """Get specific message by ID"""
            thread = await self.service.get_thread(thread_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            if not await self.authorizer.can_read_thread(user, thread):
                raise HTTPException(status_code=403, detail="Access denied")

            message = await self.service.get_message(thread_id, message_id)
            if not message:
                raise HTTPException(status_code=404, detail="Message not found")
            return ThreadConverters.message_model_to_response(message)

        @router.delete("/{thread_id}/messages/{message_id}")
        async def delete_message(thread_id: str, message_id: str, user: BaseUser = Depends(get_current_user)):
            """Delete message from thread"""
            thread = await self.service.get_thread(thread_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            if not await self.authorizer.can_post_message(user, thread):
                raise HTTPException(status_code=403, detail="Access denied")

            success = await self.service.delete_message(thread_id, message_id)
            if not success:
                raise HTTPException(status_code=404, detail="Message not found")
            return {"message": "Message deleted successfully"}

        @router.get("/{thread_id}/negotiate-streaming", response_model=ThreadResponse)
        async def negotiate_streaming(thread_id: str, user: BaseUser = Depends(get_current_user)):
            """Negotiate streaming"""
            if not self.streaming_negotiator:
                raise HTTPException(status_code=501, detail="Streaming negotiation not supported")

            thread = await self.service.get_thread(thread_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            if not await self.authorizer.can_read_thread(user, thread):
                raise HTTPException(status_code=403, detail="Access denied")

            return self.streaming_negotiator.negotiate_thread_streaming(thread_id, user)

        async def _create_message(thread_id: str, request: CreateMessageRequest, user: BaseUser) -> ThreadMessage:
            """Create a new message"""

            thread = await self.service.get_thread(thread_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")

            if not await self.authorizer.can_post_message(user, thread):
                raise HTTPException(status_code=403, detail="Access denied")

            message = ThreadMessage(
                id=str(uuid.uuid4()),
                author_id=user.get_id(),
                author_name=user.get_name(),
                timestamp=int(time.time() * 1000),
                ai=False,
                blocks=[MessageBlock(content=request.content, type=MessageBlockType.PLAIN, id=str(uuid.uuid4()), streaming=False)],
            )
            thread.add_message(message)
            await self.service.update_thread(thread)
            return message

        @router.post("/{thread_id}/messages/stream")
        async def create_message_stream(thread_id: str, request: CreateMessageRequest, user: BaseUser = Depends(get_current_user)):
            """Create a new message and stream the response immediately"""

            if not self.thread_job_processor:
                raise HTTPException(status_code=501, detail="Thread job processor not supported")
            message = await _create_message(thread_id, request, user)

            job = AgentJob(job_type=JobType.THREAD_MESSAGE, id=thread_id)
            cancellation_subscriber = (
                await self.cancellation_subscriber_provider(thread_id) if self.cancellation_subscriber_provider else None
            )
            cancellation_handle = cancellation_subscriber.get_cancellation_handle() if cancellation_subscriber else None

            def on_complete():
                if cancellation_subscriber:
                    cancellation_subscriber.stop()

            logger.debug(f"Starting processing for thread {thread_id}")

            async def generate_stream():
                try:
                    logger.debug(f"Starting streaming stream for thread {thread_id}")
                    yield MessageAddedEvent(message=message).dump_json(thread_id) + "\n\n"

                    async for event_response in self.thread_job_processor.process_job(
                        job=job, cancellation_handle=cancellation_handle, on_complete=on_complete
                    ):
                        logger.debug(f"Received event response: {event_response}")
                        yield json.dumps(event_response) + "\n\n"

                except Exception as e:
                    logger.error(f"Error in SSE stream: {e}")
                    yield f'data: {{"error": "{str(e)}"}}\n\n'

            logger.info(f"StreamingResponse for job {thread_id}")
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain; charset=utf-8",  # devtools are not happy with the proper mime type
                headers={
                    "Cache-Control": "no-cache",
                    # "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control",
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
                },
            )

        @router.post("/{thread_id}/messages", response_model=MessageResponse)
        async def create_message(thread_id: str, request: CreateMessageRequest, user: BaseUser = Depends(get_current_user)):
            """Create a new message"""
            if not self.job_queue:
                raise HTTPException(status_code=501, detail="Job queue not supported")

            message = await _create_message(thread_id, request, user)

            job = AgentJob(job_type=JobType.THREAD_MESSAGE, id=thread_id)
            await self.job_queue.push(job)
            return ThreadConverters.message_model_to_response(message)

        return router
