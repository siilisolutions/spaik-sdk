import json
from pathlib import Path
from typing import Any, Dict, Optional, TextIO

from siili_ai_sdk.recording.base_recorder import BaseRecorder
from siili_ai_sdk.recording.conditional_recorder import ConditionalRecorder, ConditionalRecorderMode
from siili_ai_sdk.recording.impl.local_playback import LocalPlayback


class LocalRecorder(BaseRecorder):
    """Local file implementation of BaseRecorder."""

    def __init__(self, recording_name: str = "default", recordings_dir: str = "recordings"):
        super().__init__(recording_name)
        self.base_recordings_dir = Path(recordings_dir)
        self.recordings_dir = self.base_recordings_dir / self.recording_name
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        self._current_file_handle: Optional[TextIO] = None

    def _get_streaming_file_path(self, session: int) -> Path:
        """Get path for streaming tokens file."""
        return self.recordings_dir / f"{session}.jsonl"

    def _get_structured_file_path(self, session: int) -> Path:
        """Get path for structured response file."""
        return self.recordings_dir / f"{session}.json"

    def _ensure_streaming_file_open(self) -> None:
        """Ensure the current streaming file is open for writing."""
        if self._current_file_handle is None:
            file_path = self._get_streaming_file_path(self.current_session)
            self._current_file_handle = open(file_path, "a", encoding="utf-8")

    def _close_current_file(self) -> None:
        """Close the current file handle if open."""
        if self._current_file_handle:
            self._current_file_handle.close()
            self._current_file_handle = None

    def _record_token_impl(self, token_data: Dict[str, Any]) -> None:
        """Record a streaming token to the current .jsonl file."""
        self._ensure_streaming_file_open()
        json_line = json.dumps(token_data, ensure_ascii=False)
        if self._current_file_handle:
            self._current_file_handle.write(json_line + "\n")
            self._current_file_handle.flush()

    def _record_structured_impl(self, data: Dict[str, Any]) -> None:
        """Record structured response to .json file and bump session."""
        # Close any open streaming file
        self._close_current_file()

        # Write structured data to .json file
        file_path = self._get_structured_file_path(self.current_session)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Immediately bump to next session
        self.current_session += 1

    def request_completed(self) -> None:
        """Close current file and bump to next session."""
        self._close_current_file()
        self.current_session += 1

    def get_current_session(self) -> int:
        """Get the current session number."""
        return self.current_session

    def __del__(self):
        """Cleanup: close any open file handles."""
        self._close_current_file()

    @classmethod
    def create_conditional_recorder(
        cls,
        recording_name: str = "default",
        recordings_dir: str = "recordings",
        mode: ConditionalRecorderMode = ConditionalRecorderMode.AUTO,
        delay: float = 0.001,
    ) -> ConditionalRecorder:
        """Create a conditional recorder with a local recorder and playback."""
        recorder = cls(recording_name, recordings_dir)
        playback = LocalPlayback(recording_name, recordings_dir, delay)
        return ConditionalRecorder(recorder, playback, mode)
