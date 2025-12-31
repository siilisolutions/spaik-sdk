"""Speech-to-text plugin with interactive recording.

Records audio from microphone until user presses Enter, then transcribes.

with:
  language: <str>        # optional - Language code (e.g., 'en', 'fi', 'de')
  output_var: <str>      # optional - Variable name to store transcription (default: 'speech_input')
  prompt_hint: <str>     # optional - Context hint for better transcription
"""

import asyncio
import io
import threading
from typing import Any, Dict

# Audio recording imports - these are optional dependencies
try:
    import numpy as np  # type: ignore[import-untyped]
    import sounddevice as sd  # type: ignore[import-untyped]

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    sd = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]

try:
    from scipy.io import wavfile  # type: ignore[import-untyped]

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    wavfile = None  # type: ignore[assignment]


class AudioRecorder:
    """Records audio from microphone with Enter key to stop."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_data: list = []

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream."""
        if self.recording:
            self.audio_data.append(indata.copy())

    async def record_until_enter(self, logger) -> bytes:
        """Record audio until user presses Enter.

        Returns:
            WAV audio bytes
        """
        if not AUDIO_AVAILABLE:
            raise RuntimeError(
                "Audio recording requires 'sounddevice' and 'numpy'. "
                "Install with: pip install sounddevice numpy"
            )
        if not SCIPY_AVAILABLE:
            raise RuntimeError(
                "Audio saving requires 'scipy'. Install with: pip install scipy"
            )

        self.audio_data = []
        self.recording = True
        stop_event = threading.Event()

        logger("🎤 Recording... Press ENTER to stop")

        # Start recording in a stream
        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            callback=self._audio_callback,
        )

        def wait_for_enter():
            input()  # Blocking wait for Enter
            stop_event.set()

        # Run input waiting in a thread
        input_thread = threading.Thread(target=wait_for_enter, daemon=True)
        input_thread.start()

        with stream:
            # Poll for stop event
            while not stop_event.is_set():
                await asyncio.sleep(0.1)

        self.recording = False
        logger("⏹️  Recording stopped")

        if not self.audio_data:
            raise RuntimeError("No audio recorded")

        # Combine all audio chunks
        audio_array = np.concatenate(self.audio_data, axis=0)

        # Convert to WAV bytes
        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, self.sample_rate, audio_array)
        wav_buffer.seek(0)

        return wav_buffer.read()


async def execute(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Record audio and transcribe to text.

    Returns:
        Dict with transcription in 'text' and the specified output_var.
    """
    logger = ctx["logger"]
    step_with: Dict[str, Any] = ctx.get("with", {})

    language = step_with.get("language")
    output_var = step_with.get("output_var", "speech_input")
    prompt_hint = step_with.get("prompt_hint")

    # Record audio
    recorder = AudioRecorder()
    audio_bytes = await recorder.record_until_enter(logger)

    logger(f"📊 Recorded {len(audio_bytes)} bytes of audio")

    # Transcribe using SDK
    from siili_ai_sdk.audio.options import STTOptions
    from siili_ai_sdk.audio.stt import SpeechToText

    stt = SpeechToText()
    options = STTOptions(
        language=language,
        prompt=prompt_hint,
    )

    logger("🔄 Transcribing...")
    transcription = await stt.transcribe(
        audio_bytes=audio_bytes,
        options=options,
        filename="recording.wav",
    )

    # Print transcription prominently
    logger("")
    logger("─" * 50)
    logger("📝 TRANSCRIPTION:")
    logger("")
    logger(f"   {transcription}")
    logger("")
    logger("─" * 50)
    logger("")

    return {
        "text": transcription,
        output_var: transcription,
    }
