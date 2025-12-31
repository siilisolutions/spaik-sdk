import httpx

from siili_ai_sdk.audio.options import AudioFormat, TTSOptions

OPENAI_TTS_ENDPOINT = "https://api.openai.com/v1/audio/speech"


async def synthesize(
    text: str,
    model: str,
    api_key: str,
    options: TTSOptions,
    endpoint: str | None = None,
    headers: dict[str, str] | None = None,
) -> bytes:
    """
    Synthesize speech using OpenAI's TTS API.

    Args:
        text: The text to convert to speech
        model: The model to use (e.g., "tts-1", "tts-1-hd", "gpt-4o-mini-tts")
        api_key: OpenAI API key
        options: TTS options
        endpoint: Optional custom endpoint
        headers: Optional additional headers

    Returns:
        Audio bytes in the specified format
    """
    url = endpoint or OPENAI_TTS_ENDPOINT

    request_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if headers:
        request_headers.update(headers)

    # Map format enum to OpenAI format string
    format_map = {
        AudioFormat.MP3: "mp3",
        AudioFormat.OPUS: "opus",
        AudioFormat.AAC: "aac",
        AudioFormat.FLAC: "flac",
        AudioFormat.WAV: "wav",
        AudioFormat.PCM: "pcm",
    }

    payload: dict = {
        "model": model,
        "input": text,
        "voice": options.voice,
        "response_format": format_map.get(options.output_format, "mp3"),
        "speed": options.speed,
    }
    payload.update(options.vendor)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=request_headers, json=payload)
        if response.status_code != 200:
            raise ValueError(f"OpenAI TTS API error {response.status_code}: {response.text}")
        return response.content
