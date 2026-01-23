from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AudioFormat(Enum):
    MP3 = "mp3"
    OPUS = "opus"
    AAC = "aac"
    FLAC = "flac"
    WAV = "wav"
    PCM = "pcm"


class TTSVoice(Enum):
    """Common TTS voices across providers."""

    # OpenAI voices
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"

    # Gemini voices (subset)
    ZEPHYR = "Zephyr"
    PUCK = "Puck"
    CHARON = "Charon"
    KORE = "Kore"
    FENRIR = "Fenrir"
    AOEDE = "Aoede"


@dataclass
class TTSOptions:
    """Options for text-to-speech synthesis."""

    voice: str = "alloy"
    speed: float = 1.0
    output_format: AudioFormat = AudioFormat.MP3
    language: str | None = None
    vendor: dict[str, Any] = field(default_factory=dict)


@dataclass
class STTOptions:
    """Options for speech-to-text transcription."""

    language: str | None = None
    prompt: str | None = None
    temperature: float = 0.0
    vendor: dict[str, Any] = field(default_factory=dict)
