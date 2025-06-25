from collections.abc import Callable
from typing import Awaitable, Optional

from fastapi import APIRouter

from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.server.api.routers.thread_router_factory import ThreadRouterFactory
from siili_ai_sdk.server.api.streaming.streaming_negotiator import StreamingNegotiator
from siili_ai_sdk.server.authorization.base_authorizer import BaseAuthorizer
from siili_ai_sdk.server.authorization.base_user import BaseUser
from siili_ai_sdk.server.authorization.dummy_authorizer import DummyAuthorizer
from siili_ai_sdk.server.job_processor.thread_job_processor import ThreadJobProcessor
from siili_ai_sdk.server.pubsub.cancellation_publisher import CancellationPublisher
from siili_ai_sdk.server.pubsub.cancellation_subscriber import CancellationSubscriber
from siili_ai_sdk.server.pubsub.impl.local_cancellation_pubsub import get_local_cancellation_pubsub
from siili_ai_sdk.server.queue.agent_job_queue import AgentJobQueue
from siili_ai_sdk.server.response.response_generator import ResponseGenerator
from siili_ai_sdk.server.response.simple_agent_response_generator import SimpleAgentResponseGenerator
from siili_ai_sdk.server.services.thread_service import ThreadService
from siili_ai_sdk.server.storage.base_thread_repository import BaseThreadRepository
from siili_ai_sdk.server.storage.impl.in_memory_thread_repository import InMemoryThreadRepository
from siili_ai_sdk.server.storage.impl.local_file_thread_repository import LocalFileThreadRepository


class ApiBuilder:
    def __init__(
        self,
        repository: BaseThreadRepository,
        authorizer: Optional[BaseAuthorizer[BaseUser]] = None,
        streaming_negotiator: Optional[StreamingNegotiator] = None,
        job_queue: Optional[AgentJobQueue] = None,
        cancellation_subscriber_provider: Optional[Callable[[str], Awaitable[CancellationSubscriber]]] = None,
        cancellation_publisher: Optional[CancellationPublisher] = None,
        response_generator: Optional[ResponseGenerator] = None,
        agent: Optional[BaseAgent] = None,
    ):
        self.repository = repository
        self.thread_service = ThreadService(repository)
        self.authorizer = authorizer
        self.streaming_negotiator = streaming_negotiator
        self.job_queue = job_queue
        self.cancellation_subscriber_provider = cancellation_subscriber_provider
        self.cancellation_publisher = cancellation_publisher
        if not response_generator and agent:
            self.response_generator: Optional[ResponseGenerator] = SimpleAgentResponseGenerator(agent)
        else:
            self.response_generator = response_generator

    def build_thread_router(self) -> APIRouter:
        if not self.response_generator:
            raise ValueError("Response generator or agent is required")

        job_processor = ThreadJobProcessor(thread_service=self.thread_service, response_generator=self.response_generator)
        factory = ThreadRouterFactory(
            service=self.thread_service,
            authorizer=self.authorizer,
            streaming_negotiator=self.streaming_negotiator,
            job_queue=self.job_queue,
            thread_job_processor=job_processor,
            cancellation_subscriber_provider=self.cancellation_subscriber_provider,
            cancellation_publisher=self.cancellation_publisher,
        )
        return factory.create_router()

    @classmethod
    def stateful(
        cls,
        repository: BaseThreadRepository,
        authorizer: BaseAuthorizer[BaseUser],
        agent: Optional[BaseAgent] = None,
        response_generator: Optional[ResponseGenerator] = None,
    ) -> "ApiBuilder":
        cancellation_pubsub = get_local_cancellation_pubsub()

        async def cancellation_subscriber_provider(id: str) -> CancellationSubscriber:
            return cancellation_pubsub.create_subscriber(id)

        return ApiBuilder(
            repository=repository,
            authorizer=authorizer,
            cancellation_subscriber_provider=cancellation_subscriber_provider,
            cancellation_publisher=cancellation_pubsub.get_publisher(),
            agent=agent,
            response_generator=response_generator,
        )

    @classmethod
    def local(
        cls, agent: Optional[BaseAgent] = None, response_generator: Optional[ResponseGenerator] = None, in_memory: bool = False
    ) -> "ApiBuilder":
        return cls.stateful(
            repository=InMemoryThreadRepository() if in_memory else LocalFileThreadRepository(),
            authorizer=DummyAuthorizer(),
            agent=agent,
            response_generator=response_generator,
        )
