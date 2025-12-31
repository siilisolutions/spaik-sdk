import httpx

from siili_ai_sdk.audio.options import STTOptions

OPENAI_STT_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"


async def transcribe(
    audio_bytes: bytes,
    model: str,
    api_key: str,
    options: STTOptions,
    filename: str = "audio.webm",
    endpoint: str | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    """
    Transcribe audio using OpenAI's Whisper API.

    Args:
        audio_bytes: The audio data to transcribe
        model: The model to use (e.g., "whisper-1", "gpt-4o-transcribe")
        api_key: OpenAI API key
        options: STT options
        filename: Filename hint for the audio format
        endpoint: Optional custom endpoint
        headers: Optional additional headers

    Returns:
        Transcribed text
    """
    url = endpoint or OPENAI_STT_ENDPOINT

    request_headers = {
        "Authorization": f"Bearer {api_key}",
    }
    if headers:
        request_headers.update(headers)

    # Determine content type from filename
    content_type = "audio/webm"
    if filename.endswith(".mp3"):
        content_type = "audio/mpeg"
    elif filename.endswith(".wav"):
        content_type = "audio/wav"
    elif filename.endswith(".m4a"):
        content_type = "audio/mp4"
    elif filename.endswith(".ogg"):
        content_type = "audio/ogg"

    # Build multipart form data
    files = {
        "file": (filename, audio_bytes, content_type),
    }
    data: dict[str, str] = {
        "model": model,
        "response_format": "text",
    }

    if options.language:
        data["language"] = options.language
    if options.prompt:
        data["prompt"] = options.prompt
    if options.temperature > 0:
        data["temperature"] = str(options.temperature)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=request_headers, files=files, data=data)
        if response.status_code != 200:
            raise ValueError(f"OpenAI STT API error {response.status_code}: {response.text}")
        return response.text.strip()
