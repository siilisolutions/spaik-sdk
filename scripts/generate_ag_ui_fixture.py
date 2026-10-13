"""Generate contract fixtures from the real Python endpoint, without provider keys."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from spaik_sdk import BaseAgent
from spaik_sdk.server.api.routers.api_builder import ApiBuilder


class Model(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


@tool
def weather(city: str) -> str:
    """Return deterministic weather."""
    return f"{city}: sunny"


app = FastAPI()
agent = BaseAgent(
    system_prompt="test",
    tools=[weather],
    chat_model=Model(
        responses=[
            AIMessage(
                content=[
                    {
                        "type": "thinking",
                        "thinking": "A public summary",
                        "signature": "private-signature",
                    }
                ],
                tool_calls=[
                    {
                        "id": "weather-call",
                        "name": "weather",
                        "args": {"city": "Helsinki"},
                    }
                ],
            ),
            AIMessage(content="Hyvää päivää!"),
        ]
    ),
)
builder = ApiBuilder.local(agent=agent, in_memory=True)
app.include_router(builder.build_thread_router())
client = TestClient(app)
thread = client.post("/threads", json={}).json()["id"]
response = client.post(
    f"/threads/{thread}/runs",
    json={
        "threadId": thread,
        "runId": "contract-run",
        "messages": [{"id": "contract-user", "role": "user", "content": "weather"}],
    },
)
response.raise_for_status()
# Random IDs are valid protocol identifiers; the TS test asserts semantics, not a hand-written implementation copy.
Path("tests/fixtures/python-ag-ui.sse").write_text(response.text, encoding="utf-8")
print("Wrote Python AG-UI contract fixture")
