import asyncio
import copy
from collections.abc import Callable
from dataclasses import asdict

from ag_ui.core import MessagesSnapshotEvent, RunAgentInput, RunFinishedEvent, UserMessage
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.attachments.file_storage_provider import get_file_storage
from spaik_sdk.server.authorization.dummy_authorizer import DummyAuthorizer
from spaik_sdk.server.services.thread_models import CreateThreadRequest
from spaik_sdk.server.services.thread_service import ThreadService
from spaik_sdk.server.storage.thread_filter import ThreadFilter
from spaik_sdk.thread.thread_container import ThreadContainer
from spaik_sdk.tracing.agent_trace import AgentTrace


class ThreadRouterFactory:
    """Single-process run coordination. Deploy one worker per repository.

    Distributed coordination belongs to an application integration, not this local runner.
    """

    def __init__(
        self,
        service: ThreadService,
        agent: BaseAgent | None = None,
        authorizer=None,
        agent_factory: Callable[[ThreadContainer], BaseAgent] | None = None,
    ):
        self.service = service
        self.agent = agent
        self.agent_factory = agent_factory
        self.authorizer = authorizer or DummyAuthorizer()
        self.active: dict[str, asyncio.Task | None] = {}

    def create_router(self, prefix: str = "/threads") -> APIRouter:
        router = APIRouter(prefix=prefix, tags=["threads"])

        async def user(request: Request):
            current = await self.authorizer.get_user(request)
            if current is None:
                raise HTTPException(401, "Unauthorized")
            return current

        async def owned(thread_id: str, current, permission: str):
            thread = await self.service.get_thread(thread_id)
            if thread is None:
                raise HTTPException(404, "Thread not found")
            if not await getattr(self.authorizer, permission)(current, thread):
                raise HTTPException(403, "Access denied")
            return thread

        @router.post("")
        async def create(request: CreateThreadRequest, current=Depends(user)):
            if not await self.authorizer.can_create_thread(current):
                raise HTTPException(403, "Access denied")
            thread = ThreadContainer(owner_id=current.get_id())
            thread.envelope.metadata = request.metadata
            await self.service.create_thread(thread)
            return thread.public_dict()

        @router.get("")
        async def list_threads(
            current=Depends(user),
            thread_type: str | None = None,
            title_contains: str | None = None,
            min_messages: int | None = None,
            max_messages: int | None = None,
            hours_ago: int | None = None,
        ):
            import time

            builder = ThreadFilter.builder().with_author_id(current.get_id())
            if thread_type:
                builder.with_type(thread_type)
            if title_contains:
                builder.with_title_containing(title_contains)
            if min_messages is not None:
                builder.with_min_messages(min_messages)
            if max_messages is not None:
                builder.with_max_messages(max_messages)
            if hours_ago is not None:
                builder.with_activity_after(int((time.time() - hours_ago * 3600) * 1000))
            summaries = await self.service.list_threads(builder.build())
            return {"threads": [asdict(m) for m in summaries], "total_count": len(summaries)}

        @router.get("/{thread_id}")
        async def get_thread(thread_id: str, current=Depends(user)):
            return (await owned(thread_id, current, "can_read_thread")).public_dict()

        @router.delete("/{thread_id}")
        async def delete_thread(thread_id: str, current=Depends(user)):
            await owned(thread_id, current, "can_delete_thread")
            if thread_id in self.active:
                raise HTTPException(409, "Cancel the active run before deleting the thread")
            await self.service.delete_thread(thread_id)
            return {"message": "Thread deleted"}

        @router.post("/{thread_id}/cancel")
        async def cancel(thread_id: str, current=Depends(user)):
            await owned(thread_id, current, "can_post_message")
            task = self.active.get(thread_id)
            if task:
                task.cancel()
            return {"success": True, "message": "Cancellation requested"}

        @router.post("/{thread_id}/runs")
        async def run(thread_id: str, input: RunAgentInput, request: Request, current=Depends(user)):
            if input.thread_id != thread_id:
                raise HTTPException(400, "threadId does not match the route")
            # Reserve before awaiting the repository: no two requests can both pass this check.
            if thread_id in self.active:
                raise HTTPException(409, "Thread already has an active run")
            self.active[thread_id] = None
            try:
                thread = await owned(thread_id, current, "can_post_message")
                if input.tools or input.resume:
                    raise HTTPException(422, "Client tool execution and interrupt resume are not supported by this runner")
                if input.run_id in thread.envelope.metadata.get("run_ids", []):
                    raise HTTPException(409, "runId has already been used")
                existing = {m.id: m for m in thread.messages}
                submitted = {}
                new = []
                for message in input.messages:
                    normalized = message.model_dump(mode="json", by_alias=True, exclude_none=True)
                    if message.id in submitted:
                        if submitted[message.id] != normalized:
                            raise HTTPException(409, "Conflicting duplicate message ID")
                        continue
                    submitted[message.id] = normalized
                    if message.id in existing:
                        if existing[message.id].model_dump(mode="json", by_alias=True, exclude_none=True) != normalized:
                            raise HTTPException(409, "Stored messages cannot be overwritten")
                    elif not isinstance(message, UserMessage):
                        raise HTTPException(422, "Only new user messages may be submitted")
                    else:
                        new.append(message)
                if not new:
                    raise HTTPException(400, "Submit a new user message")
                # Attachments use a small Spaik forwardedProps extension; validate ownership before inference.
                props = input.forwarded_props or {}
                attachment_map = props.get("attachments", {}) if isinstance(props, dict) else {}
                storage = get_file_storage()
                for message in new:
                    attachments = attachment_map.get(message.id, [])
                    for attachment in attachments:
                        if storage is None:
                            raise HTTPException(422, "File storage is not configured")
                        try:
                            _, metadata = await storage.retrieve(attachment["file_id"])
                        except (FileNotFoundError, KeyError):
                            raise HTTPException(404, "Attachment not found")
                        if not await self.authorizer.can_read_file(current, metadata):
                            raise HTTPException(403, "Attachment access denied")
                        if attachment.get("mime_type") != metadata.mime_type:
                            raise HTTPException(422, "Attachment MIME type does not match storage")
                if self.agent_factory:
                    agent = self.agent_factory(thread)
                elif self.agent:
                    agent = copy.copy(self.agent)
                    agent.trace = AgentTrace(agent.system_prompt, trace_sink=self.agent.trace._trace_sink)
                else:
                    raise HTTPException(501, "Agent is not configured")
                agent.set_thread_container(thread)
                for message in new:
                    thread.add_message(message, {"author_id": current.get_id(), "attachments": attachment_map.get(message.id, [])})
                thread.envelope.metadata.setdefault("run_ids", []).append(input.run_id)
                await self.service.update_thread(thread)
            except BaseException:
                self.active.pop(thread_id, None)
                raise

            async def events():
                self.active[thread_id] = asyncio.current_task()
                encoder = EventEncoder(accept=request.headers.get("accept", "text/event-stream"))
                try:
                    async for event in agent.get_event_stream(run_id=input.run_id):
                        yield encoder.encode(event)
                except asyncio.CancelledError:
                    if not await request.is_disconnected():
                        yield encoder.encode(MessagesSnapshotEvent(messages=thread.messages))
                        yield encoder.encode(RunFinishedEvent(thread_id=thread_id, run_id=input.run_id, outcome={"type": "cancelled"}))
                finally:
                    try:
                        await asyncio.shield(self.service.update_thread(thread))
                    finally:
                        self.active.pop(thread_id, None)

            return StreamingResponse(
                events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
            )

        return router
