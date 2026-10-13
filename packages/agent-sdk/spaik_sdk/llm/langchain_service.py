"""LangChain execution translated directly into canonical AG-UI messages/events."""

import asyncio
import json
import uuid
from typing import Any

from ag_ui import core as ui
from langchain_core.messages import AIMessage, AIMessageChunk, message_to_dict
from langgraph.prebuilt import ToolNode, create_react_agent

from spaik_sdk.attachments.file_storage_provider import get_file_storage
from spaik_sdk.llm.cost.cost_provider import CostContext, CostProvider
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.thread.models import Invocation
from spaik_sdk.thread.thread_container import ThreadContainer


def reasoning_text(block: dict[str, Any]) -> str:
    value = block.get("thinking") or block.get("reasoning") or block.get("text")
    if isinstance(value, str):
        return value
    return "".join(item.get("text", "") for item in block.get("summary", []) if isinstance(item, dict))


class LangChainService:
    def __init__(
        self,
        llm_config: LLMConfig,
        thread_container: ThreadContainer,
        cost_provider: CostProvider,
        tools: list,
        recorder=None,
        playback=None,
        cancellation_handle=None,
    ):
        self.config = llm_config
        self.thread = thread_container
        self.cost_provider = cost_provider
        self.tools = tools
        self.recorder = recorder
        self.playback = playback
        self.cancellation_handle = cancellation_handle

    def create_executor(self):
        return create_react_agent(self.config.get_model_wrapper().get_langchain_model(), ToolNode(self.tools, handle_tool_errors=True))

    async def stream(self):
        storage = get_file_storage()
        messages = (
            await self.thread.get_langchain_messages_multimodal(storage, self.config.provider_name)
            if storage
            else self.thread.get_langchain_messages()
        )
        executor = None if self.playback is not None else self.create_executor()
        source = (
            self.playback
            if self.playback is not None
            else executor.astream_events({"messages": messages}, version="v2", config={"recursion_limit": self.config.max_agent_steps})
        )
        models: dict[str, dict[str, Any]] = {}
        tool_ids: set[str] = set()
        try:
            async for event in source:
                if self.cancellation_handle and await self.cancellation_handle.is_cancelled():
                    raise asyncio.CancelledError
                if self.recorder is not None:
                    self.recorder.record_token(event)
                kind = event.get("event")
                data = event.get("data", {})
                invocation_id = event.get("run_id") or "model"
                if kind in {"on_chat_model_stream", "on_chat_model_end"}:
                    state = models.setdefault(
                        invocation_id,
                        {
                            "id": str(uuid.uuid4()),
                            "text": "",
                            "reasoning": "",
                            "started": False,
                            "reasoning_id": str(uuid.uuid4()),
                            "reasoning_started": False,
                            "chunk": None,
                            "tools": {},
                            "ended": False,
                        },
                    )
                    if state["ended"]:
                        continue
                    if kind == "on_chat_model_stream":
                        chunk = data.get("chunk")
                        if not isinstance(chunk, AIMessageChunk):
                            continue
                        state["chunk"] = chunk if state["chunk"] is None else state["chunk"] + chunk
                        text = (
                            chunk.content
                            if isinstance(chunk.content, str)
                            else "".join(
                                b.get("text", "") if isinstance(b, dict) and b.get("type") == "text" else b if isinstance(b, str) else ""
                                for b in chunk.content
                            )
                        )
                        reasoning = (
                            "".join(
                                reasoning_text(b)
                                for b in chunk.content
                                if isinstance(b, dict) and b.get("type") in {"thinking", "reasoning", "reasoning_summary"}
                            )
                            if isinstance(chunk.content, list)
                            else ""
                        )
                    else:
                        chunk = data.get("output")
                        if not isinstance(chunk, (AIMessage, AIMessageChunk)):
                            continue
                        # If a provider does not stream, emit its final content once.
                        text = (
                            (
                                chunk.content
                                if isinstance(chunk.content, str)
                                else "".join(b.get("text", "") for b in chunk.content if isinstance(b, dict) and b.get("type") == "text")
                            )
                            if not state["text"]
                            else ""
                        )
                        reasoning = (
                            "".join(
                                reasoning_text(b)
                                for b in chunk.content
                                if isinstance(b, dict) and b.get("type") in {"thinking", "reasoning", "reasoning_summary"}
                            )
                            if isinstance(chunk.content, list) and not state["reasoning"]
                            else ""
                        )
                    if reasoning:
                        if not state["reasoning_started"]:
                            state["reasoning_started"] = True
                            self.thread.add_message(ui.ReasoningMessage(id=state["reasoning_id"], content=""))
                            yield ui.ReasoningStartEvent(message_id=state["reasoning_id"])
                            yield ui.ReasoningMessageStartEvent(message_id=state["reasoning_id"])
                        state["reasoning"] += reasoning
                        next(m for m in self.thread.messages if m.id == state["reasoning_id"]).content = state["reasoning"]
                        yield ui.ReasoningMessageContentEvent(message_id=state["reasoning_id"], delta=reasoning)
                    if not state["started"] and (
                        text
                        or getattr(chunk, "tool_calls", None)
                        or getattr(chunk, "tool_call_chunks", None)
                        or kind == "on_chat_model_end"
                    ):
                        state["started"] = True
                        self.thread.add_message(ui.AssistantMessage(id=state["id"], content="", tool_calls=[]))
                        yield ui.TextMessageStartEvent(message_id=state["id"], role="assistant")
                    if text:
                        state["text"] += text
                        next(m for m in self.thread.messages if m.id == state["id"]).content = state["text"]
                        yield ui.TextMessageContentEvent(message_id=state["id"], delta=text)
                    if kind == "on_chat_model_stream":
                        for call in chunk.tool_call_chunks:
                            index = call.get("index", 0)
                            tracked = state["tools"].setdefault(
                                index, {"id": call.get("id"), "name": call.get("name"), "args": "", "started": False}
                            )
                            tracked["id"] = tracked["id"] or call.get("id")
                            tracked["name"] = tracked["name"] or call.get("name")
                            args = call.get("args") or ""
                            tracked["args"] += args
                            if tracked["id"] and tracked["name"]:
                                if not tracked["started"]:
                                    tracked["started"] = True
                                    tool_ids.add(tracked["id"])
                                    yield ui.ToolCallStartEvent(
                                        tool_call_id=tracked["id"], tool_call_name=tracked["name"], parent_message_id=state["id"]
                                    )
                                    if tracked["args"]:
                                        yield ui.ToolCallArgsEvent(tool_call_id=tracked["id"], delta=tracked["args"])
                                elif args:
                                    yield ui.ToolCallArgsEvent(tool_call_id=tracked["id"], delta=args)
                        # Keep the partial transcript usable if execution is cancelled.
                        if state["started"]:
                            assistant = next(m for m in self.thread.messages if m.id == state["id"])
                            assistant.tool_calls = [
                                ui.ToolCall(id=c["id"], type="function", function=ui.FunctionCall(name=c["name"], arguments=c["args"]))
                                for c in state["tools"].values()
                                if c["started"]
                            ]
                        continue
                    state["ended"] = True
                    assistant = next(m for m in self.thread.messages if m.id == state["id"])
                    final = (
                        chunk
                        if isinstance(chunk, AIMessage)
                        else AIMessage(
                            **{k: v for k, v in chunk.model_dump().items() if k not in {"type", "tool_call_chunks", "chunk_position"}}
                        )
                    )
                    calls = final.tool_calls or []
                    assistant.tool_calls = [
                        ui.ToolCall(id=c["id"], type="function", function=ui.FunctionCall(name=c["name"], arguments=json.dumps(c["args"])))
                        for c in calls
                    ]
                    providers = {tool.name: getattr(tool, "_spaik_tool_provider_id", None) for tool in self.tools}
                    self.thread.envelope.replay[state["id"]] = {
                        "langchain": message_to_dict(final),
                        "tool_providers": {c["id"]: providers.get(c["name"]) for c in calls},
                    }
                    for call in calls:
                        if call["id"] not in tool_ids:
                            yield ui.ToolCallStartEvent(tool_call_id=call["id"], tool_call_name=call["name"], parent_message_id=state["id"])
                            yield ui.ToolCallArgsEvent(tool_call_id=call["id"], delta=json.dumps(call["args"]))
                        yield ui.ToolCallEndEvent(tool_call_id=call["id"])
                    if state["reasoning_started"]:
                        yield ui.ReasoningMessageEndEvent(message_id=state["reasoning_id"])
                        yield ui.ReasoningEndEvent(message_id=state["reasoning_id"])
                    metadata = dict(final.response_metadata or {})
                    cost = await self.cost_provider.resolve(
                        CostContext(provider=self.config.provider_name, response_id=metadata.get("id") or final.id, metadata=metadata)
                    )
                    self.thread.add_invocation(
                        Invocation(
                            id=invocation_id,
                            message_id=state["id"],
                            provider=self.config.provider_name,
                            model=self.config.model_name,
                            usage=final.usage_metadata,
                            cost=cost,
                        )
                    )
                    yield ui.TextMessageEndEvent(message_id=state["id"])
                elif kind == "on_tool_end":
                    output = data.get("output")
                    tool_call_id = getattr(output, "tool_call_id", None)
                    if tool_call_id:
                        content = output.content if isinstance(output.content, str) else json.dumps(output.content)
                        tool_message = ui.ToolMessage(
                            id=str(uuid.uuid4()),
                            tool_call_id=tool_call_id,
                            content=content,
                            error=content if getattr(output, "status", None) == "error" else None,
                        )
                        self.thread.add_message(tool_message)
                        yield ui.ToolCallResultEvent(message_id=tool_message.id, tool_call_id=tool_call_id, content=content, role="tool")
        finally:
            self.thread.touch()
            if hasattr(source, "aclose"):
                await source.aclose()
            if self.recorder is not None:
                self.recorder.request_completed()
