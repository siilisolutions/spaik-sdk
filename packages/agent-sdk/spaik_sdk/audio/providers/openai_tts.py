from collections.abc import AsyncIterator

import httpx

from spaik_sdk.audio.options import AudioFormat, TTSOptions

OPENAI_TTS_ENDPOINT = "https://api.openai.com/v1/audio/speech"


def _get_format_map() -> dict[AudioFormat, str]:
    return {
        AudioFormat.MP3: "mp3",
        AudioFormat.OPUS: "opus",
        AudioFormat.AAC: "aac",
        AudioFormat.FLAC: "flac",
        AudioFormat.WAV: "wav",
        AudioFormat.PCM: "pcm",
    }


def _build_payload(text: str, model: str, options: TTSOptions) -> dict:
    format_map = _get_format_map()
    payload: dict = {
        "model": model,
        "input": text,
        "voice": options.voice,
        "response_format": format_map.get(options.output_format, "mp3"),
        "speed": options.speed,
    }
    payload.update(options.vendor)
    return payload


def _build_headers(api_key: str, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    return headers


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
    request_headers = _build_headers(api_key, headers)
    payload = _build_payload(text, model, options)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=request_headers, json=payload)
        if response.status_code != 200:
            raise ValueError(f"OpenAI TTS API error {response.status_code}: {response.text}")
        return response.content


async def synthesize_stream(
    text: str,
    model: str,
    api_key: str,
    options: TTSOptions,
    endpoint: str | None = None,
    headers: dict[str, str] | None = None,
) -> AsyncIterator[bytes]:
    """
    Stream synthesized speech using OpenAI's TTS API.

    Yields audio chunks as they arrive, allowing playback to start immediately.

    Args:
        text: The text to convert to speech
        model: The model to use (e.g., "tts-1", "tts-1-hd", "gpt-4o-mini-tts")
        api_key: OpenAI API key
        options: TTS options
        endpoint: Optional custom endpoint
        headers: Optional additional headers

    Yields:
        Audio bytes chunks
    """
    url = endpoint or OPENAI_TTS_ENDPOINT
    request_headers = _build_headers(api_key, headers)
    payload = _build_payload(text, model, options)

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, headers=request_headers, json=payload) as response:
            if response.status_code != 200:
                content = await response.aread()
                raise ValueError(f"OpenAI TTS API error {response.status_code}: {content.decode()}")
            async for chunk in response.aiter_bytes(chunk_size=4096):
                yield chunk
