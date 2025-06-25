from enum import Enum
from typing import Optional

from siili_ai_sdk.recording.base_playback import BasePlayback
from siili_ai_sdk.recording.base_recorder import BaseRecorder


class ConditionalRecorderMode(Enum):
    """Mode for ConditionalRecorder behavior."""

    ALWAYS_RECORD = "always_record"
    ALWAYS_PLAYBACK = "always_playback"
    AUTO = "auto"


class ConditionalRecorder:
    """Conditional recorder that switches between recording and playback based on mode."""

    def __init__(self, recorder: BaseRecorder, playback: BasePlayback, mode: ConditionalRecorderMode = ConditionalRecorderMode.AUTO):
        self.recorder = recorder
        self.playback = playback
        self.mode = mode

    def get_recorder(self) -> Optional[BaseRecorder]:
        """Returns the recorder if should record, None otherwise."""
        if self.mode == ConditionalRecorderMode.ALWAYS_RECORD:
            return self.recorder
        elif self.mode == ConditionalRecorderMode.AUTO and not self.playback.is_available():
            return self.recorder
        return None

    def get_playback(self) -> Optional[BasePlayback]:
        """Returns the playback if should playback, None otherwise."""
        if self.mode == ConditionalRecorderMode.ALWAYS_PLAYBACK:
            return self.playback
        elif self.mode == ConditionalRecorderMode.AUTO and self.playback.is_available():
            return self.playback
        return None
