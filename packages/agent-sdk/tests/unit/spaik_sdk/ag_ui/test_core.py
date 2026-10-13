import json
from typing import Any
from unittest.mock import patch

import pytest
from ag_ui import core as ui
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, message_to_dict

from spaik_sdk import BaseAgent, LLMConfig, ThreadContainer
from spaik_sdk.llm.cancellation_handle import CancellationHandle
from spaik_sdk.llm.cost.cost_estimate import CostEstimate
from spaik_sdk.llm.cost.cost_provider import CostContext, CostProvider
from spaik_sdk.server.api.routers.api_builder import ApiBuilder
from spaik_sdk.server.authorization.base_authorizer import BaseAuthorizer
from spaik_sdk.server.authorization.base_user import BaseUser
from spaik_sdk.server.storage.impl.local_file_thread_repository import LocalFileThreadRepository
from spaik_sdk.thread.models import Invocation

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_stream_and_injected_model():
    model = FakeListChatModel(responses=["hello", "again"])
    agent = BaseAgent(system_prompt="test", chat_model=model)
    assert agent.get_langchain_model() is model
    events = [event async for event in agent.get_event_stream("hi")]
    assert isinstance(events[0], ui.RunStartedEvent)
    assert isinstance(events[-1], ui.RunFinishedEvent)
    assert "".join(e.delta for e in events if isinstance(e, ui.TextMessageContentEvent)) == "hello"
    assert agent.thread_container.messages[-1].content == "hello"
    assert await agent.get_response_text_async("second") == "again"
    assert len(agent.thread_container.envelope.invocations) == 2
    assert agent.get_cost() is None


def test_arbitrary_model_does_not_use_presets():
    with patch("spaik_sdk.models.llm_config.init_chat_model") as initialize:
        config = LLMConfig(model="never-in-a-registry", provider_type="custom", provider_kwargs={"temperature": 0.7})
        config.get_model_wrapper()
        initialize.assert_called_once_with("never-in-a-registry", model_provider="custom", temperature=0.7)


@pytest.mark.asyncio
async def test_cost_zero_and_missing(caplog):
    provider = CostProvider()
    zero = await provider.resolve(CostContext(provider="custom", metadata={"cost": 0, "currency": "EUR"}))
    assert zero is not None
    assert zero.cost == 0
    assert zero.currency == "EUR"
    for _ in range(3):
        assert await provider.resolve(CostContext(provider="custom")) is None
    assert sum("Cost unavailable" in r.message for r in caplog.records) == 1


@pytest.mark.asyncio
async def test_openrouter_metadata_avoids_lookup():
    provider = CostProvider(base_url="https://openrouter.ai/api/v1", api_key="test")
    with patch("httpx.AsyncClient.get") as lookup:
        cost = await provider.resolve(CostContext(provider="openai", response_id="gen", metadata={"usage": {"cost": 0.1}}))
        assert cost is not None
        assert cost.cost == 0.1
        await provider.resolve(CostContext(provider="openai", response_id="gen"))
        lookup.assert_not_called()


@pytest.mark.asyncio
async def test_lookup_failure_is_cached():
    provider = CostProvider(base_url="https://openrouter.ai/api/v1", api_key="test")
    with patch("httpx.AsyncClient.get", side_effect=RuntimeError("failed")) as lookup:
        context = CostContext(provider="openrouter", response_id="gen")
        assert await provider.resolve(context) is None
        assert await provider.resolve(context) is None
        assert lookup.call_count == 1


def test_cost_aggregation_is_not_a_false_total():
    thread = ThreadContainer()
    for index, cost in enumerate([{"cost": 1, "currency": "USD"}, None, {"cost": 2, "currency": "EUR"}]):
        thread.add_invocation(
            Invocation(
                id=str(index), message_id="m", provider="p", model="m", cost=CostEstimate.model_validate(cost) if cost is not None else None
            )
        )
    summary = thread.get_cost_summary()
    assert summary is not None
    assert summary.totals == {"USD": 1, "EUR": 2}
    assert not summary.complete
    assert summary.unavailable_invocations == 1


@pytest.mark.asyncio
async def test_json_round_trip_private_reasoning(tmp_path):
    thread = ThreadContainer(system_prompt="secret", owner_id="alice")
    thread.add_message(ui.AssistantMessage(id="a", content="answer"))
    signed = AIMessage(content=[{"type": "thinking", "thinking": "private", "signature": "signed"}, {"type": "text", "text": "answer"}])
    thread.envelope.replay["a"] = {"langchain": message_to_dict(signed)}
    repository = LocalFileThreadRepository(str(tmp_path))
    await repository.save_thread(thread)
    loaded = await repository.load_thread(thread.thread_id)
    assert loaded is not None
    assert loaded.owner_id == "alice"
    assert loaded.get_langchain_messages()[-1].content[0]["signature"] == "signed"
    assert "replay" not in loaded.public_dict()
    assert "system_prompt" not in loaded.public_dict()
    assert list(tmp_path.rglob("*.json"))
    assert not list(tmp_path.rglob("*.pkl"))


class OwnerAuthorizer(BaseAuthorizer):
    async def get_user(self, request):
        return BaseUser(request.headers.get("x-user", "alice"))


def client():
    app = FastAPI()
    builder = ApiBuilder.local(BaseAgent(system_prompt="test", chat_model=FakeListChatModel(responses=["hello"])), in_memory=True)
    builder._thread_router.authorizer = OwnerAuthorizer()
    app.include_router(builder.build_thread_router())
    return TestClient(app)


def test_authoritative_history_and_sse():
    c = client()
    thread_id = c.post("/threads", json={}).json()["id"]
    assert c.get(f"/threads/{thread_id}", headers={"x-user": "bob"}).status_code == 403
    assert len(c.get("/threads").json()["threads"]) == 1
    body: dict[str, Any] = {"threadId": thread_id, "runId": "run", "messages": [{"id": "u", "role": "user", "content": "hi"}]}
    response = c.post(f"/threads/{thread_id}/runs", json=body)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    assert events[0]["type"] == "RUN_STARTED"
    assert events[-1]["type"] == "RUN_FINISHED"
    assert c.post(f"/threads/{thread_id}/runs", json=body).status_code == 409
    body["runId"] = "next"
    body["messages"][0]["content"] = "overwrite"
    assert c.post(f"/threads/{thread_id}/runs", json=body).status_code == 409
    body["threadId"] = "wrong"
    assert c.post(f"/threads/{thread_id}/runs", json=body).status_code == 400
    assert c.delete(f"/threads/{thread_id}").status_code == 200


@pytest.mark.asyncio
async def test_tool_error_and_replay_controls():
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.tools import tool

    from spaik_sdk.tools.tool_provider import ToolProvider

    class Model(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    class Tools(ToolProvider):
        def get_tools(self):
            @tool
            def fail() -> str:
                """Fail deliberately."""
                raise ValueError("expected failure")

            return [fail]

    provider = Tools(persist_tool_block_history=False)
    agent = BaseAgent(
        system_prompt="test",
        tool_providers=[provider],
        chat_model=Model(
            responses=[AIMessage(content="", tool_calls=[{"id": "call", "name": "fail", "args": {}}]), AIMessage(content="recovered")]
        ),
    )
    events = [e async for e in agent.get_event_stream("test")]
    assert isinstance(events[-1], ui.RunFinishedEvent)
    assert any(isinstance(e, ui.ToolCallResultEvent) and "expected failure" in e.content for e in events)
    history = agent.thread_container.get_langchain_messages()
    assert not any(getattr(m, "tool_call_id", None) == "call" for m in history)
    assert any('<tool_call tool="fail"/>' in str(m.content) for m in history)
    assert "expected failure" in agent.trace.to_string()


@pytest.mark.asyncio
async def test_cancelled_partial_transcript():
    class Cancellation(CancellationHandle):
        def __init__(self):
            self.calls = 0

        async def is_cancelled(self):
            self.calls += 1
            return self.calls > 3

    agent = BaseAgent(system_prompt="test", chat_model=FakeListChatModel(responses=["long answer"]), cancellation_handle=Cancellation())
    events = [e async for e in agent.get_event_stream("test")]
    assert isinstance(events[-1], ui.RunFinishedEvent)
    assert isinstance(events[-1].outcome, ui.RunFinishedCancelledOutcome)
    assert agent.thread_container.messages[-1].content
    assert not agent._running


@pytest.mark.asyncio
async def test_legacy_import_preserves_metadata_and_refuses_overwrite(tmp_path):
    from spaik_sdk.thread.migration import import_threads

    archive = {
        "format": "spaik-legacy-export-v1",
        "threads": [
            {
                "id": "thread",
                "last_activity_time": 42,
                "system_prompt": "private",
                "messages": [
                    {
                        "id": "user",
                        "ai": False,
                        "author_id": "alice",
                        "author_name": "Alice",
                        "timestamp": 10,
                        "attachments": [{"file_id": "f", "mime_type": "image/png"}],
                        "blocks": [{"id": "b", "type": "plain", "content": "hello"}],
                    },
                    {
                        "id": "assistant",
                        "ai": True,
                        "author_id": "agent",
                        "timestamp": 20,
                        "blocks": [
                            {"id": "r", "type": "reasoning", "content": "summary"},
                            {
                                "id": "t",
                                "type": "tool_use",
                                "tool_call_id": "call",
                                "tool_name": "test",
                                "tool_call_args": {},
                                "tool_call_response": "result",
                                "tool_provider_id": "provider",
                            },
                        ],
                    },
                ],
            }
        ],
    }
    source = tmp_path / "export.json"
    source.write_text(json.dumps(archive))
    destination = tmp_path / "new"
    assert await import_threads(source, destination) == 1
    repository = LocalFileThreadRepository(str(destination))
    thread = await repository.load_thread("thread")
    assert thread is not None
    assert thread.owner_id == "alice"
    assert [m.id for m in thread.messages] == ["user", "r", "assistant", "t:result"]
    assert thread.envelope.message_metadata["user"]["attachments"][0]["file_id"] == "f"
    assert thread.envelope.replay["assistant"]["tool_providers"]["call"] == "provider"
    assert thread.envelope.created_at == 10
    assert thread.envelope.last_activity_time == 42
    with pytest.raises(ValueError, match="already exists"):
        await import_threads(source, destination)
    assert json.loads(source.read_text()) == archive


@pytest.mark.asyncio
async def test_disconnect_saves_partial_output_and_releases_run(tmp_path):
    import asyncio

    import anyio

    from spaik_sdk.server.storage.impl.local_file_thread_repository import LocalFileThreadRepository

    repository = LocalFileThreadRepository(str(tmp_path))
    thread = ThreadContainer(owner_id="user")
    await repository.save_thread(thread)
    agent = BaseAgent(system_prompt="test", chat_model=FakeListChatModel(responses=["long response"], sleep=0.02))
    builder = ApiBuilder(repository=repository, agent=agent)
    app = FastAPI()
    app.include_router(builder.build_thread_router())
    disconnect = asyncio.Event()
    received = False
    chunks = []
    body = json.dumps(
        {"threadId": thread.thread_id, "runId": "disconnect", "messages": [{"id": "u", "role": "user", "content": "test"}]}
    ).encode()

    async def receive():
        nonlocal received
        if not received:
            received = True
            return {"type": "http.request", "body": body, "more_body": False}
        await disconnect.wait()
        return {"type": "http.disconnect"}

    async def send(message):
        chunks.append(message)
        if b"TEXT_MESSAGE_CONTENT" in message.get("body", b""):
            disconnect.set()

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.0"},
        "method": "POST",
        "path": f"/threads/{thread.thread_id}/runs",
        "raw_path": f"/threads/{thread.thread_id}/runs".encode(),
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 1),
        "server": ("test", 80),
        "scheme": "http",
        "http_version": "1.1",
        "root_path": "",
    }
    with anyio.fail_after(5):
        await app(scope, receive, send)
    loaded = await repository.load_thread(thread.thread_id)
    assert loaded is not None
    assert loaded.messages[-1].content
    assert loaded.messages[-1].content != "long response"
    assert not builder._thread_router.active


@pytest.mark.asyncio
async def test_overlapping_runs_are_rejected_and_cancellation_releases_reservation():
    import asyncio

    import httpx

    app = FastAPI()
    builder = ApiBuilder.local(
        BaseAgent(system_prompt="test", chat_model=FakeListChatModel(responses=["long answer"], sleep=0.05)), in_memory=True
    )
    app.include_router(builder.build_thread_router())
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        thread_id = (await c.post("/threads", json={})).json()["id"]
        body = {"threadId": thread_id, "runId": "first", "messages": [{"id": "u", "role": "user", "content": "test"}]}
        running = asyncio.create_task(c.post(f"/threads/{thread_id}/runs", json=body))
        for _ in range(100):
            active = builder._thread_router.active.get(thread_id)
            if active and active.task:
                break
            await asyncio.sleep(0.001)
        assert active and active.task
        conflict = await c.post(f"/threads/{thread_id}/runs", json={**body, "runId": "overlap"})
        assert conflict.status_code == 409
        assert (await c.post(f"/threads/{thread_id}/cancel")).status_code == 200
        response = await running
        assert response.status_code == 200
        assert "cancelled" in response.text
        assert not builder._thread_router.active


def test_native_multimodal_parts_reach_the_model():
    thread = ThreadContainer()
    thread.add_message(
        ui.UserMessage(
            id="multimodal",
            content=[
                ui.TextPart(type="text", text="Describe this"),
                ui.ImagePart(type="image", source=ui.UrlSource(type="url", value="https://example.test/image.png")),
                ui.DocumentPart(type="document", source=ui.DataSource(type="data", value="cGRm", mime_type="application/pdf")),
            ],
        )
    )
    content = thread.get_langchain_messages()[0].content
    assert content[1] == {"type": "image", "url": "https://example.test/image.png"}
    assert content[2]["type"] == "file"
    assert content[2]["base64"] == "cGRm"
    assert content[2]["filename"] == "attachment.pdf"


def test_azure_deployment_configuration_needs_no_environment_or_registry(monkeypatch):
    for key in ["AZURE_API_KEY", "AZURE_ENDPOINT", "AZURE_API_VERSION"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("LLM_AUTH_MODE", raising=False)
    from spaik_sdk.models.providers.azure_provider import AzureProvider

    config = LLMConfig(
        model="unregistered-deployment",
        provider_type="azure_openai",
        provider_kwargs={"api_key": "test", "azure_endpoint": "https://example.openai.azure.com", "api_version": "2025-03-01-preview"},
    )
    assert AzureProvider().get_model_config(config)["api_key"] == "test"
    with patch("langchain_openai.AzureChatOpenAI") as initialize:
        config.get_model_wrapper()
        assert initialize.call_args.kwargs["azure_deployment"] == "unregistered-deployment"


@pytest.mark.asyncio
async def test_cost_lookup_is_coalesced_and_reports_zero():
    import asyncio
    from unittest.mock import AsyncMock

    import httpx

    provider = CostProvider(base_url="https://openrouter.ai/api/v1", api_key="test")
    response = httpx.Response(
        200, json={"data": {"total_cost": 0}}, request=httpx.Request("GET", "https://openrouter.ai/api/v1/generation")
    )
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=response) as lookup:
        context = CostContext(provider="openrouter", response_id="zero-generation")
        results = await asyncio.gather(*(provider.resolve(context) for _ in range(3)))
        assert lookup.call_count == 1
        assert all(result is not None and result.cost == 0 for result in results)


def test_spawn_isolates_callback_context_and_child_transcript():
    import contextvars

    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.tools import tool

    marker = contextvars.ContextVar("parent_marker", default="isolated")
    marker.set("parent")

    class Model(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    @tool
    def echo() -> str:
        """Return the child context marker."""
        return marker.get()

    child = BaseAgent(
        system_prompt="child",
        tools=[echo],
        chat_model=Model(
            responses=[AIMessage(content="", tool_calls=[{"id": "child-call", "name": "echo", "args": {}}]), AIMessage(content="isolated")]
        ),
    )

    @tool
    def spawn_child() -> str:
        """Run the child agent."""
        return child.spawn("test").content or ""

    parent = BaseAgent(
        system_prompt="parent",
        tools=[spawn_child],
        chat_model=Model(
            responses=[
                AIMessage(content="", tool_calls=[{"id": "parent-call", "name": "spawn_child", "args": {}}]),
                AIMessage(content="done"),
            ]
        ),
    )
    assert parent.get_response_text("test") == "done"
    calls = [
        call.function.name
        for message in parent.thread_container.messages
        if isinstance(message, ui.AssistantMessage)
        for call in message.tool_calls or []
    ]
    assert calls == ["spawn_child"]
    assert any(message.role == "tool" and message.content == "isolated" for message in child.thread_container.messages)
    assert marker.get() == "parent"


@pytest.mark.parametrize(
    "alias,canonical", [("azure", "azure_openai"), ("foundry", "azure_ai_foundry"), ("google_genai", "google"), ("mistralai", "mistral")]
)
def test_provider_aliases_are_normalized_for_model_construction(alias, canonical):
    assert LLMConfig(model="arbitrary-model", provider_type=alias).provider_name == canonical


@pytest.mark.asyncio
async def test_structured_output_records_cost_and_advances_recording_once(tmp_path):
    from langchain_core.runnables import RunnableLambda
    from pydantic import BaseModel

    from spaik_sdk.recording.conditional_recorder import ConditionalRecorderMode
    from spaik_sdk.recording.impl.local_recorder import LocalRecorder

    class Output(BaseModel):
        word: str

    class Model(FakeListChatModel):
        def with_structured_output(self, schema, **kwargs):
            assert kwargs["include_raw"]
            return RunnableLambda(
                lambda prompt: {
                    "parsed": Output(word="OK"),
                    "raw": AIMessage(
                        content='{"word":"OK"}',
                        id="structured",
                        response_metadata={"cost": 0.1, "currency": "USD"},
                        usage_metadata={"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
                    ),
                    "parsing_error": None,
                }
            )

    recording = LocalRecorder.create_conditional_recorder("structured", str(tmp_path), mode=ConditionalRecorderMode.ALWAYS_RECORD)
    agent = BaseAgent(system_prompt="test", chat_model=Model(responses=["unused"]), recorder=recording)
    assert (await agent.get_structured_response_async("test", Output)).word == "OK"
    cost = agent.get_cost()
    assert cost is not None and cost.totals == {"USD": 0.1}
    assert recording.recorder.current_session == 2
    assert (tmp_path / "structured" / "1.json").exists()


@pytest.mark.parametrize("attachments", [[], {"u": "file"}, {"u": [{"file_id": "only"}]}])
def test_invalid_attachment_metadata_is_a_client_error(attachments):
    c = client()
    thread_id = c.post("/threads", json={}).json()["id"]
    body = {
        "threadId": thread_id,
        "runId": "invalid-attachment",
        "messages": [{"id": "u", "role": "user", "content": "hi"}],
        "forwardedProps": {"attachments": attachments},
    }
    assert c.post(f"/threads/{thread_id}/runs", json=body).status_code == 422
    assert c.get(f"/threads/{thread_id}").json()["messages"] == []
