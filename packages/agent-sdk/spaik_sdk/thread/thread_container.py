import json
import time
import uuid
from typing import TYPE_CHECKING, Any

from ag_ui.core import AssistantMessage, Message, ToolMessage, UserMessage
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, messages_from_dict
from langchain_core.messages import ToolMessage as LCToolMessage

from spaik_sdk.llm.consumption.token_usage import TokenUsage
from spaik_sdk.llm.cost.cost_estimate import CostSummary
from spaik_sdk.thread.models import Invocation, ThreadEnvelope, ToolCallHistory

if TYPE_CHECKING:
    from spaik_sdk.tools.tool_provider import ToolProvider


def message_text(message: Message) -> str:
    content = getattr(message, "content", "") or ""
    if isinstance(content, str):
        return content
    return "\n".join(getattr(part, "text", "") for part in content if part.type == "text")


class ThreadContainer:
    def __init__(self, system_prompt: str | None = None, thread_id: str | None = None, owner_id: str = "user"):
        now = int(time.time() * 1000)
        self.envelope = ThreadEnvelope(
            id=thread_id or str(uuid.uuid4()), owner_id=owner_id, system_prompt=system_prompt, created_at=now, last_activity_time=now
        )
        self._tool_providers: dict[str, ToolProvider] = {}

    @property
    def thread_id(self) -> str:
        return self.envelope.id

    @property
    def owner_id(self) -> str:
        return self.envelope.owner_id

    @property
    def messages(self) -> list[Message]:
        return self.envelope.messages

    @messages.setter
    def messages(self, messages: list[Message]) -> None:
        self.envelope.messages = messages

    @property
    def system_prompt(self) -> str | None:
        return self.envelope.system_prompt

    @system_prompt.setter
    def system_prompt(self, prompt: str | None) -> None:
        self.envelope.system_prompt = prompt

    def add_message(self, message: Message, metadata: dict[str, Any] | None = None) -> None:
        if any(existing.id == message.id for existing in self.messages):
            raise ValueError(f"Duplicate message ID: {message.id}")
        details = {"timestamp": int(time.time() * 1000), "author_name": getattr(message, "name", None) or message.role, **(metadata or {})}
        message.metadata = {**(message.metadata or {}), "spaik": details}
        self.messages.append(message)
        self.envelope.message_metadata[message.id] = details
        self.touch()

    def touch(self) -> None:
        self.envelope.last_activity_time = int(time.time() * 1000)

    def get_last_activity_time(self) -> int:
        return self.envelope.last_activity_time

    def bind_tool_providers(self, providers: list["ToolProvider"]) -> None:
        self._tool_providers = {provider.get_provider_id(): provider for provider in providers}

    def get_latest_ai_message(self) -> AssistantMessage | None:
        return next((m for m in reversed(self.messages) if isinstance(m, AssistantMessage)), None)

    def get_total_consumption(self) -> TokenUsage:
        usages = [TokenUsage.from_langchain(i.usage) for i in self.envelope.invocations if i.usage]
        return TokenUsage(**{key: sum(getattr(u, key) for u in usages) for key in TokenUsage.__dataclass_fields__})

    def get_cost_summary(self, latest_only: bool = False) -> CostSummary | None:
        invocations = self.envelope.invocations[-1:] if latest_only else self.envelope.invocations
        if not invocations:
            return None
        totals: dict[str, float] = {}
        for invocation in invocations:
            if invocation.cost is not None:
                currency = invocation.cost.currency
                totals[currency] = totals.get(currency, 0) + invocation.cost.cost
        if not totals:
            return None
        missing = sum(i.cost is None for i in invocations)
        return CostSummary(totals=totals, complete=missing == 0, unavailable_invocations=missing)

    def add_invocation(self, invocation: Invocation) -> None:
        if not any(i.id == invocation.id for i in self.envelope.invocations):
            self.envelope.invocations.append(invocation)

    def get_langchain_messages(self) -> list[Any]:
        from spaik_sdk.llm.converters import message_content

        result: list[Any] = [SystemMessage(content=self.system_prompt)] if self.system_prompt else []
        hidden_tools: set[str] = set()
        tool_results = {m.tool_call_id: m for m in self.messages if isinstance(m, ToolMessage)}
        for message in self.messages:
            if isinstance(message, UserMessage):
                result.append(HumanMessage(content=message_content(message.content), id=message.id))
            elif isinstance(message, AssistantMessage):
                raw = self.envelope.replay.get(message.id, {}).get("langchain")
                ai = (
                    messages_from_dict([raw])[0]
                    if raw
                    else AIMessage(
                        content=message.content or "",
                        id=message.id,
                        tool_calls=[
                            {"id": t.id, "name": t.function.name, "args": json.loads(t.function.arguments or "{}")}
                            for t in message.tool_calls or []
                            if t.id in tool_results
                        ],
                    )
                )
                if not isinstance(ai, AIMessage):
                    raise ValueError("Assistant replay data must contain an AIMessage")
                ai = ai.model_copy(deep=True)
                provider_ids = self.envelope.replay.get(message.id, {}).get("tool_providers", {})
                summaries = []
                kept_calls = []
                for call in ai.tool_calls:
                    call_id = call["id"]
                    if call_id is None:
                        continue
                    provider = self._tool_providers.get(provider_ids.get(call_id, ""))
                    custom = provider is not None and (
                        not getattr(provider, "persist_tool_block_history", True)
                        or type(provider).render_tool_block_for_history is not self._default_history_renderer()
                    )
                    if not custom and call_id in tool_results:
                        kept_calls.append(call)
                        continue
                    hidden_tools.add(call_id)
                    tool_result = tool_results.get(call_id)
                    summaries.append(
                        (provider.render_tool_block_for_history if provider else self._incomplete_tool_marker)(
                            ToolCallHistory(
                                tool_name=call["name"],
                                tool_call_id=call_id,
                                tool_call_args=call["args"],
                                tool_call_response=message_text(tool_result) if tool_result else None,
                                tool_call_error=tool_result.error if tool_result else None,
                            )
                        )
                    )
                ai.tool_calls = kept_calls
                if summaries:
                    if isinstance(ai.content, str):
                        ai.content += "\n" + "\n".join(summaries)
                    else:
                        # Drop provider-native tool-use blocks for suppressed calls, keeping signed reasoning intact.
                        ai.content = [
                            b for b in ai.content if not isinstance(b, dict) or (b.get("id", b.get("call_id")) not in hidden_tools)
                        ]
                        ai.content.append({"type": "text", "text": "\n".join(summaries)})
                result.append(ai)
            elif isinstance(message, ToolMessage) and message.tool_call_id not in hidden_tools:
                result.append(
                    LCToolMessage(
                        content=message_text(message),
                        tool_call_id=message.tool_call_id,
                        id=message.id,
                        status="error" if message.error else "success",
                    )
                )
            elif message.role in {"system", "developer"}:
                result.append(SystemMessage(content=message_text(message), id=message.id))
        return result

    @staticmethod
    def _incomplete_tool_marker(history: ToolCallHistory) -> str:
        return f"<incomplete_tool_call tool={json.dumps(history.tool_name)}/>"

    @staticmethod
    def _default_history_renderer():
        from spaik_sdk.tools.tool_provider import ToolProvider

        return ToolProvider.render_tool_block_for_history

    async def get_langchain_messages_multimodal(self, file_storage) -> list[Any]:
        from spaik_sdk.attachments.models import Attachment
        from spaik_sdk.llm.converters import attachment_content

        messages = self.get_langchain_messages()
        for message in messages:
            if not isinstance(message, HumanMessage):
                continue
            attachments = self.envelope.message_metadata.get(message.id, {}).get("attachments", [])
            if attachments:
                parts = [{"type": "text", "text": message.content}] if isinstance(message.content, str) else list(message.content)
                for data in attachments:
                    part = await attachment_content(Attachment.from_dict(data), file_storage)
                    if part:
                        parts.append(part)
                message.content = parts
        return messages

    def to_dict(self) -> dict[str, Any]:
        return self.envelope.model_dump(mode="json", by_alias=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ThreadContainer":
        envelope = ThreadEnvelope.model_validate(data)
        if envelope.schema_version != 1:
            raise ValueError(f"Unsupported thread schema: {envelope.schema_version}")
        thread = cls()
        thread.envelope = envelope
        return thread

    def public_dict(self) -> dict[str, Any]:
        return self.envelope.model_dump(mode="json", by_alias=True, exclude={"replay", "system_prompt"})
