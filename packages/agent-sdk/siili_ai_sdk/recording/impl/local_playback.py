import json
from pathlib import Path
from typing import Any, Dict, Iterator

from siili_ai_sdk.recording.base_playback import BasePlayback


class LocalPlayback(BasePlayback):
    """Local file implementation of BasePlayback."""

    def __init__(self, recording_name: str = "default", recordings_dir: str = "recordings", delay: float = 0.001):
        super().__init__(recording_name, delay)
        self.base_recordings_dir = Path(recordings_dir)
        self.recordings_dir = self.base_recordings_dir / self.recording_name

    def _get_streaming_file_path(self, session: int) -> Path:
        """Get path for streaming tokens file."""
        return self.recordings_dir / f"{session}.jsonl"

    def _get_structured_file_path(self, session: int) -> Path:
        """Get path for structured response file."""
        return self.recordings_dir / f"{session}.json"

    def _session_exists(self, session_num: int) -> bool:
        """Check if either streaming or structured file exists for session."""
        streaming_path = self._get_streaming_file_path(session_num)
        structured_path = self._get_structured_file_path(session_num)
        return streaming_path.exists() or structured_path.exists()

    def is_available(self) -> bool:
        """Check if playback data is available."""
        return self.recordings_dir.exists() and any(self.recordings_dir.iterdir())

    def _load_session_data_impl(self, session_num: int) -> Iterator[Dict[str, Any]]:
        """Load raw data for a specific session number."""
        streaming_path = self._get_streaming_file_path(session_num)
        structured_path = self._get_structured_file_path(session_num)

        # Check for structured response first (single response)
        if structured_path.exists():
            with open(structured_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                yield data
            return

        # Check for streaming tokens (.jsonl)
        if streaming_path.exists():
            with open(streaming_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        try:
                            token_data = json.loads(line)
                            yield token_data
                        except json.JSONDecodeError:
                            # Skip malformed lines
                            continue
            return

        # No files found for this session
        raise StopIteration(f"No data found for session {session_num}")

    def peek_next_session_type(self) -> str:
        """Peek at what type the next session will be without consuming it."""
        if not self._session_exists(self.current_session):
            return "none"

        structured_path = self._get_structured_file_path(self.current_session)
        if structured_path.exists():
            return "structured"

        streaming_path = self._get_streaming_file_path(self.current_session)
        if streaming_path.exists():
            return "streaming"

        return "none"
