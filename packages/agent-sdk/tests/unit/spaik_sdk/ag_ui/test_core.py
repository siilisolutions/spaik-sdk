import json
from unittest.mock import patch

import pytest
from ag_ui import core as ui
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, message_to_dict

from spaik_sdk import BaseAgent, LLMConfig, ThreadContainer
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
        thread.add_invocation(Invocation(id=str(index), message_id="m", provider="p", model="m", cost=cost))
    summary = thread.get_cost_summary()
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
    body = {"threadId": thread_id, "runId": "run", "messages": [{"id": "u", "role": "user", "content": "hi"}]}
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
