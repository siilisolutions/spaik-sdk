"""Provider usage is recorded independently of charges, once per model invocation."""

import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

from spaik_sdk import BaseAgent


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reported_usage_and_cost_are_persisted(tmp_path):
    from spaik_sdk.server.storage.impl.local_file_thread_repository import LocalFileThreadRepository

    model = FakeMessagesListChatModel(
        responses=[
            AIMessage(
                content="hello",
                usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
                response_metadata={"cost": 0.01, "currency": "USD", "id": "request"},
            )
        ]
    )
    agent = BaseAgent(system_prompt="test", chat_model=model)
    assert await agent.get_response_text_async("hello") == "hello"
    assert agent.thread_container.get_total_consumption().total_tokens == 15
    cost = agent.get_cost()
    assert cost is not None
    assert cost.totals == {"USD": 0.01}
    repository = LocalFileThreadRepository(str(tmp_path))
    await repository.save_thread(agent.thread_container)
    loaded = await repository.load_thread(agent.thread_container.thread_id)
    assert loaded is not None
    summary = loaded.get_cost_summary()
    assert summary is not None
    assert summary.complete
    assert loaded.get_total_consumption().total_tokens == 15
