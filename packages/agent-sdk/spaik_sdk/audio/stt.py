from spaik_sdk.audio.options import STTOptions
from spaik_sdk.audio.providers import openai_stt
from spaik_sdk.config.env import env_config
from spaik_sdk.config.get_credentials_provider import credentials_provider


class SpeechToText:
    """
    Speech-to-text transcriber using OpenAI Whisper.

    Note: Only OpenAI is supported for STT as Gemini doesn't have
    a dedicated speech-to-text API endpoint.
    """

    def __init__(
        self,
        model: str | None = None,
        endpoint: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        """
        Initialize the SpeechToText transcriber.

        Args:
            model: STT model name. If None, uses STT_MODEL env var or defaults to whisper-1.
            endpoint: Optional custom API endpoint.
            headers: Optional additional HTTP headers.
        """
        self.model = model or env_config.get_key("STT_MODEL", "whisper-1", required=False)
        self.endpoint = endpoint
        self.headers = headers

    async def transcribe(
        self,
        audio_bytes: bytes,
        options: STTOptions | None = None,
        filename: str = "audio.webm",
    ) -> str:
        """
        Transcribe audio to text.

        Args:
            audio_bytes: The audio data to transcribe.
            options: STT options (language, prompt hint, etc.)
            filename: Filename hint for audio format detection.

        Returns:
            Transcribed text string.
        """
        opts = options or STTOptions()
        api_key = credentials_provider.get_provider_key("openai")

        return await openai_stt.transcribe(
            audio_bytes=audio_bytes,
            model=self.model,
            api_key=api_key,
            options=opts,
            filename=filename,
            endpoint=self.endpoint,
            headers=self.headers,
        )
