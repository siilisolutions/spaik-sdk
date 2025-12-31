"""Text-to-speech plugin.

Converts text to speech audio, optionally playing it and/or saving to file.

with:
  text: <str>            # required - Text to synthesize (or use 'text_var' for variable)
  text_var: <str>        # optional - Variable name containing text to synthesize
  voice: <str>           # optional - Voice name (default: 'alloy')
  speed: <float>         # optional - Speed multiplier (default: 1.0)
  language: <str>        # optional - Language hint
  output: <str>          # optional - File path to save audio
  play: <bool>           # optional - Play audio (default: true if no output)
  model: <str>           # optional - TTS model (default: 'tts-1')
"""

from pathlib import Path
from typing import Any, Dict

# Audio playback is optional
try:
    import numpy as np  # type: ignore[import-untyped]
    import sounddevice as sd  # type: ignore[import-untyped]

    PLAYBACK_AVAILABLE = True
except ImportError:
    PLAYBACK_AVAILABLE = False
    sd = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]

try:
    import io

    from pydub import AudioSegment  # type: ignore[import-untyped]

    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None  # type: ignore[assignment]


async def execute(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesize speech from text.

    Returns:
        Dict with 'audio_bytes' and 'output_path' (if saved).
    """
    logger = ctx["logger"]
    step_with: Dict[str, Any] = ctx.get("with", {})

    # Get text from direct param or from a variable
    text = step_with.get("text")
    text_var = step_with.get("text_var")

    if text_var and not text:
        # Try to get from context variables
        text = ctx.get("vars", {}).get(text_var)

    if not text:
        raise ValueError("'with.text' or 'with.text_var' is required")

    voice = step_with.get("voice", "alloy")
    speed = float(step_with.get("speed", 1.0))
    language = step_with.get("language")
    output_path = step_with.get("output")
    model = step_with.get("model", "tts-1")

    # Default to play if no output file specified
    should_play = step_with.get("play")
    if should_play is None:
        should_play = output_path is None

    logger(f"🔊 TTS: '{text[:50]}{'...' if len(text) > 50 else ''}'")
    logger(f"   Voice: {voice}, Speed: {speed}, Model: {model}")

    # Synthesize
    from siili_ai_sdk.audio.options import TTSOptions
    from siili_ai_sdk.audio.tts import TextToSpeech

    tts = TextToSpeech(model=model)
    options = TTSOptions(
        voice=voice,
        speed=speed,
        language=language,
    )

    audio_bytes = await tts.synthesize(text, options)
    logger(f"📊 Generated {len(audio_bytes)} bytes of audio")

    result: Dict[str, Any] = {
        "audio_bytes": audio_bytes,
    }

    # Save to file if requested
    if output_path:
        workspace: Path = ctx.get("workspace", Path.cwd())
        full_path = (workspace / output_path).resolve()
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(audio_bytes)
        logger(f"💾 Saved to: {full_path}")
        result["output_path"] = str(full_path)

    # Play audio if requested
    if should_play:
        if not PLAYBACK_AVAILABLE:
            logger("⚠️  Audio playback requires 'sounddevice' and 'numpy'")
        elif not PYDUB_AVAILABLE:
            logger("⚠️  Audio playback requires 'pydub'")
        else:
            logger("▶️  Playing audio...")
            try:
                # Convert MP3 to raw audio for playback
                audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
                samples = np.array(audio.get_array_of_samples())

                # Handle stereo
                if audio.channels == 2:
                    samples = samples.reshape((-1, 2))

                # Normalize to float32 for sounddevice
                samples = samples.astype(np.float32) / 32768.0

                sd.play(samples, audio.frame_rate)
                sd.wait()
                logger("✅ Playback complete")
            except Exception as e:
                logger(f"⚠️  Playback failed: {e}")

    return result
