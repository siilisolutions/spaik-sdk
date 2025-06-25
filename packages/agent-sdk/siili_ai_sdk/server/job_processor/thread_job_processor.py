from collections.abc import Callable
from typing import Optional

from fastapi import HTTPException

from siili_ai_sdk.llm.cancellation_handle import CancellationHandle
from siili_ai_sdk.server.job_processor.base_job_processor import BaseJobProcessor
from siili_ai_sdk.server.pubsub.thread_event_publisher import ThreadEventPublisher
from siili_ai_sdk.server.queue.agent_job_queue import AgentJob
from siili_ai_sdk.server.response.response_generator import ResponseGenerator
from siili_ai_sdk.server.services.thread_service import ThreadService


class ThreadJobProcessor(BaseJobProcessor):
    def __init__(self, thread_service: ThreadService, response_generator: ResponseGenerator):
        super().__init__()
        self.thread_service = thread_service
        self.response_generator = response_generator

    async def process_job(
        self,
        job: AgentJob,
        thread_event_publisher: ThreadEventPublisher,
        cancellation_handle: Optional[CancellationHandle],
        on_complete: Callable[[], None] = lambda: None,
    ) -> None:
        thread_container = await self.thread_service.get_thread(job.id)
        if thread_container is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        thread_event_publisher.bind_container(thread_container)
        await self.response_generator.trigger_response(thread_container, cancellation_handle)
        await self.thread_service.update_thread(thread_container)
        on_complete()
