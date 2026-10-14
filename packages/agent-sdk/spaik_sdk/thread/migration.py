"""Read legacy 0.x thread data: load it from any store, or import an export into a new JSON store."""

import argparse
import asyncio
import json
from pathlib import Path

from ag_ui.core import AssistantMessage, FunctionCall, ReasoningMessage, ToolCall, ToolMessage, UserMessage

from spaik_sdk.thread.models import Invocation
from spaik_sdk.thread.thread_container import ThreadContainer


def is_legacy_thread(data: dict) -> bool:
    return "schema_version" not in data


def load_thread_data(data: dict, fallback_owner: str | None = None) -> ThreadContainer:
    """Load a stored thread in either format. Legacy data is converted in memory, never written back."""
    return convert_legacy_thread(data, fallback_owner) if is_legacy_thread(data) else ThreadContainer.from_dict(data)


def convert_legacy_thread(data: dict, fallback_owner: str | None = None) -> ThreadContainer:
    messages = data["messages"]
    owner = next((m["author_id"] for m in messages if not m["ai"]), fallback_owner)
    if not owner:
        raise ValueError(f"Thread {data['id']} has no user message; supply a fallback owner")
    thread = ThreadContainer(system_prompt=data.get("system_prompt"), thread_id=data["id"], owner_id=owner)
    for old in messages:
        blocks = old["blocks"]
        metadata = {key: old[key] for key in ["author_id", "author_name", "timestamp", "attachments"] if key in old}
        metadata["legacy_block_ids"] = [b["id"] for b in blocks]
        text = "\n".join(b.get("content") or "" for b in blocks if b["type"] in {"plain", "error"})
        if not old["ai"]:
            thread.add_message(UserMessage(id=old["id"], content=text), metadata)
            continue
        for block in blocks:
            if block["type"] == "reasoning":
                thread.add_message(ReasoningMessage(id=block["id"], content=block.get("content") or ""), metadata)
        calls = [
            ToolCall(
                id=b["tool_call_id"],
                type="function",
                function=FunctionCall(name=b.get("tool_name") or "unknown", arguments=json.dumps(b.get("tool_call_args") or {})),
            )
            for b in blocks
            if b["type"] == "tool_use" and b.get("tool_call_id")
        ]
        thread.add_message(AssistantMessage(id=old["id"], content=text, tool_calls=calls), metadata)
        thread.envelope.replay[old["id"]] = {
            "tool_providers": {
                b["tool_call_id"]: b.get("tool_provider_id") for b in blocks if b["type"] == "tool_use" and b.get("tool_call_id")
            }
        }
        for block in blocks:
            if block["type"] == "tool_use" and block.get("tool_call_id") and block.get("tool_call_response") is not None:
                thread.add_message(
                    ToolMessage(
                        id=f"{block['id']}:result",
                        tool_call_id=block["tool_call_id"],
                        content=block["tool_call_response"],
                        error=block.get("tool_call_error"),
                    ),
                    metadata,
                )
        # Legacy records contain token counts, not trustworthy provider-reported charges.
        usage = old.get("consumption_metadata")
        if usage:
            thread.add_invocation(
                Invocation(id=f"legacy:{old['id']}", message_id=old["id"], provider="legacy", model="unknown", usage=usage)
            )
    if messages:
        thread.envelope.created_at = messages[0]["timestamp"]
    thread.envelope.last_activity_time = data.get("last_activity_time", thread.envelope.created_at)
    return thread


async def import_threads(source: Path, destination: Path, fallback_owner: str | None = None) -> int:
    from spaik_sdk.server.storage.impl.local_file_thread_repository import LocalFileThreadRepository

    archive = json.loads(source.read_text(encoding="utf-8"))
    if archive.get("format") != "spaik-legacy-export-v1":
        raise ValueError("Unsupported legacy export format")
    threads = [convert_legacy_thread(data, fallback_owner) for data in archive["threads"]]
    if len({t.thread_id for t in threads}) != len(threads):
        raise ValueError("Duplicate thread IDs in export")
    repository = LocalFileThreadRepository(str(destination))
    for thread in threads:
        if await repository.thread_exists(thread.thread_id):
            raise ValueError(f"Thread already exists: {thread.thread_id}; use a new destination")
    for thread in threads:
        await repository.save_thread(thread)
    return len(threads)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--empty-owner")
    args = parser.parse_args()
    count = asyncio.run(import_threads(args.source, args.destination, args.empty_owner))
    print(f"Imported {count} threads to {args.destination}")


if __name__ == "__main__":
    main()
