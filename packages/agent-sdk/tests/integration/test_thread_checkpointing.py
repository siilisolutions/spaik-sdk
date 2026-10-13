"""Tool results checkpoint the canonical transcript before the run completes."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from spaik_sdk import BaseAgent
from spaik_sdk.server.api.routers.api_builder import ApiBuilder


@pytest.mark.integration
def test_tool_results_are_checkpointed():
    class Model(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    @tool
    def greeting() -> str:
        """Return a greeting."""
        return "hello"

    agent = BaseAgent(
        system_prompt="test",
        tools=[greeting],
        chat_model=Model(
            responses=[AIMessage(content="", tool_calls=[{"id": "call", "name": "greeting", "args": {}}]), AIMessage(content="done")]
        ),
    )
    builder = ApiBuilder.local(agent=agent, in_memory=True)
    checkpoints = []
    original = builder.repository.save_thread

    async def save(thread):
        checkpoints.append([m.role for m in thread.messages])
        await original(thread)

    builder.repository.save_thread = AsyncMock(side_effect=save)
    app = FastAPI()
    app.include_router(builder.build_thread_router())
    client = TestClient(app)
    id = client.post("/threads", json={}).json()["id"]
    response = client.post(
        f"/threads/{id}/runs", json={"threadId": id, "runId": "run", "messages": [{"id": "u", "role": "user", "content": "test"}]}
    )
    assert response.status_code == 200
    assert ["user", "assistant", "tool"] in checkpoints
    assert checkpoints[-1] == ["user", "assistant", "tool", "assistant"]
