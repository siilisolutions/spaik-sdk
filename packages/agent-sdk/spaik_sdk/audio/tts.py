from collections.abc import AsyncIterator

from spaik_sdk.audio.options import TTSOptions
from spaik_sdk.audio.providers import google_tts, openai_tts
from spaik_sdk.config.env import env_config
from spaik_sdk.config.get_credentials_provider import credentials_provider


class TextToSpeech:
    """
    Text-to-speech synthesizer supporting multiple providers.

    Automatically detects the provider based on the model name.
    Supports OpenAI (tts-1, tts-1-hd, gpt-4o-mini-tts) and
    Google Gemini (gemini-2.5-flash-tts, gemini-2.5-pro-tts).
    """

    def __init__(
        self,
        model: str | None = None,
        endpoint: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        """
        Initialize the TextToSpeech synthesizer.

        Args:
            model: TTS model name. If None, uses TTS_MODEL env var.
            endpoint: Optional custom API endpoint.
            headers: Optional additional HTTP headers.
        """
        self.model = model or env_config.get_key("TTS_MODEL", "tts-1", required=False)
        self.endpoint = endpoint
        self.headers = headers

    def _get_provider(self) -> str:
        """Determine the provider based on model name."""
        model_lower = self.model.lower()
        if model_lower.startswith("tts-") or model_lower.startswith("gpt-"):
            return "openai"
        elif model_lower.startswith("gemini"):
            return "google"
        else:
            raise ValueError(f"Unknown TTS model provider for: {self.model}")

    async def synthesize(
        self,
        text: str,
        options: TTSOptions | None = None,
    ) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: The text to convert to speech.
            options: TTS options (voice, speed, format, etc.)

        Returns:
            Audio bytes in the specified format.
        """
        opts = options or TTSOptions()
        provider = self._get_provider()

        if provider == "openai":
            api_key = credentials_provider.get_provider_key("openai")
            return await openai_tts.synthesize(
                text=text,
                model=self.model,
                api_key=api_key,
                options=opts,
                endpoint=self.endpoint,
                headers=self.headers,
            )
        elif provider == "google":
            api_key = credentials_provider.get_provider_key("google")
            return await google_tts.synthesize(
                text=text,
                model=self.model,
                api_key=api_key,
                options=opts,
                endpoint=self.endpoint,
                headers=self.headers,
            )
        else:
            raise ValueError(f"Unsupported TTS provider: {provider}")

    async def synthesize_stream(
        self,
        text: str,
        options: TTSOptions | None = None,
    ) -> AsyncIterator[bytes]:
        """
        Stream synthesized speech from text.

        Yields audio chunks as they arrive, allowing playback to start immediately.
        Currently only supported for OpenAI models.

        Args:
            text: The text to convert to speech.
            options: TTS options (voice, speed, format, etc.)

        Yields:
            Audio bytes chunks.
        """
        opts = options or TTSOptions()
        provider = self._get_provider()

        if provider == "openai":
            api_key = credentials_provider.get_provider_key("openai")
            async for chunk in openai_tts.synthesize_stream(
                text=text,
                model=self.model,
                api_key=api_key,
                options=opts,
                endpoint=self.endpoint,
                headers=self.headers,
            ):
                yield chunk
        elif provider == "google":
            # Google doesn't support streaming, fall back to full synthesis
            audio_bytes = await self.synthesize(text, options)
            yield audio_bytes
        else:
            raise ValueError(f"Unsupported TTS provider: {provider}")
