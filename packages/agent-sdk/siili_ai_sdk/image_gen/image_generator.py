import re
from pathlib import Path
from time import time

from siili_ai_sdk.config.env import env_config
from siili_ai_sdk.config.get_credentials_provider import credentials_provider
from siili_ai_sdk.image_gen.options import ImageFormat, ImageGenOptions
from siili_ai_sdk.image_gen.providers import google as google_provider
from siili_ai_sdk.image_gen.providers import openai as openai_provider


def _slugify(text: str, max_length: int = 50) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower())
    slug = slug.strip("_")
    return slug[:max_length]


def _generate_filename(prompt: str, output_format: ImageFormat) -> str:
    slug = _slugify(prompt)
    timestamp = int(time())
    extension = output_format.value
    return f"{slug}_{timestamp}.{extension}"


class ImageGenerator:
    def __init__(
        self,
        model: str | None = None,
        output_dir: str = ".",
        endpoint: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.model = model or env_config.get_image_model()
        self.output_dir = Path(output_dir)
        self.endpoint = endpoint
        self.headers = headers

    def _get_provider(self) -> str:
        if self.model.startswith("gpt-image"):
            return "openai"
        elif self.model.startswith("gemini"):
            return "google"
        else:
            raise ValueError(f"Unknown image model provider for: {self.model}")

    async def generate_image(
        self,
        prompt: str,
        options: ImageGenOptions | None = None,
        output_filename: str | None = None,
    ) -> Path:
        opts = options or ImageGenOptions()
        provider = self._get_provider()

        if provider == "openai":
            api_key = credentials_provider.get_provider_key("openai")
            image_bytes = await openai_provider.generate_image(
                prompt=prompt,
                model=self.model,
                api_key=api_key,
                options=opts,
                endpoint=self.endpoint,
                headers=self.headers,
            )
        elif provider == "google":
            api_key = credentials_provider.get_provider_key("google")
            image_bytes = await google_provider.generate_image(
                prompt=prompt,
                model=self.model,
                api_key=api_key,
                options=opts,
                endpoint=self.endpoint,
                headers=self.headers,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        filename = output_filename or _generate_filename(prompt, opts.output_format)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / filename

        output_path.write_bytes(image_bytes)
        return output_path
