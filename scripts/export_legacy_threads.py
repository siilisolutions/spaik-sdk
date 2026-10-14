"""Run with spaik-sdk==0.11.1 against your own trusted legacy store.

Usage: python export_legacy_threads.py OLD_DATA_DIR export.json
This reads trusted local pickle files and never modifies the old store.
Pickles stored in a database: import export_thread from this file in a 0.11
job, call it on each unpickled ThreadContainer and store the resulting JSON.
"""

import argparse
import json
import pickle
from dataclasses import asdict, is_dataclass
from pathlib import Path


def export_thread(thread) -> dict:
    """Convert an unpickled 0.11 ThreadContainer to the export shape that Spaik 1.0 loads."""
    messages = []
    for message in thread.messages:
        data = message.to_dict()
        usage = data.get("consumption_metadata")
        if is_dataclass(usage):
            data["consumption_metadata"] = asdict(usage)
        # Preserve streaming content and tool results not yet copied into blocks.
        for block in data["blocks"]:
            block["content"] = thread.streaming_content.get(block["id"], block.get("content"))
            response = thread.tool_call_responses.get(block.get("tool_call_id"))
            if response:
                block["tool_call_response"] = response.response
                block["tool_call_error"] = response.error
        messages.append(data)
    return {
        "id": thread.thread_id,
        "system_prompt": thread.system_prompt,
        "last_activity_time": thread.get_last_activity_time(),
        "messages": messages,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; choose a new file")
    threads = []
    for path in sorted((args.data_dir / "threads").glob("*.pkl")):
        with path.open("rb") as source:
            threads.append(export_thread(pickle.load(source)))
    args.output.write_text(
        json.dumps({"format": "spaik-legacy-export-v1", "threads": threads}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Exported {len(threads)} threads to {args.output}")


if __name__ == "__main__":
    main()
