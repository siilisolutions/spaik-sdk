from spaik_sdk.attachments.file_storage_provider import set_file_storage
from spaik_sdk.attachments.storage.impl.local_file_storage import LocalFileStorage
from spaik_sdk.server.api.routers.thread_router_factory import ThreadRouterFactory
from spaik_sdk.server.authorization.dummy_authorizer import DummyAuthorizer
from spaik_sdk.server.services.thread_service import ThreadService
from spaik_sdk.server.storage.impl.in_memory_thread_repository import InMemoryThreadRepository
from spaik_sdk.server.storage.impl.local_file_thread_repository import LocalFileThreadRepository


class ApiBuilder:
    def __init__(self, repository, authorizer=None, agent=None, file_storage=None, agent_factory=None):
        self.repository = repository
        self.authorizer = authorizer or DummyAuthorizer()
        self.agent = agent
        self.agent_factory = agent_factory
        self.file_storage = file_storage
        self.thread_service = ThreadService(repository)
        self._thread_router = ThreadRouterFactory(self.thread_service, agent, self.authorizer, agent_factory)
        if file_storage is not None:
            set_file_storage(file_storage)

    def build_thread_router(self):
        return self._thread_router.create_router()

    def build_file_router(self):
        from spaik_sdk.server.api.routers.file_router_factory import FileRouterFactory

        if self.file_storage is None:
            raise ValueError("File storage is required")
        return FileRouterFactory(self.file_storage, self.authorizer).create_router()

    def build_audio_router(self, tts_model=None, stt_model=None):
        from spaik_sdk.server.api.routers.audio_router_factory import AudioRouterFactory

        return AudioRouterFactory(authorizer=self.authorizer, tts_model=tts_model, stt_model=stt_model).create_router()

    @classmethod
    def stateful(cls, repository, authorizer, agent=None, file_storage=None, agent_factory=None):
        return cls(repository, authorizer, agent, file_storage, agent_factory)

    @classmethod
    def local(cls, agent=None, in_memory=False, file_storage=None, agent_factory=None):
        return cls(
            InMemoryThreadRepository() if in_memory else LocalFileThreadRepository(),
            agent=agent,
            file_storage=file_storage or LocalFileStorage(),
            agent_factory=agent_factory,
        )
