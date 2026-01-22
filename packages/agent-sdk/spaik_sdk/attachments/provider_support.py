from spaik_sdk.attachments.mime_types import (
    AUDIO_TYPES,
    DOCUMENT_TYPES,
    IMAGE_TYPES,
    VIDEO_TYPES,
    MimeTypes,
)

OPENAI_SUPPORTED = frozenset(
    {
        MimeTypes.PNG,
        MimeTypes.JPEG,
        MimeTypes.GIF,
        MimeTypes.WEBP,
        MimeTypes.PDF,
    }
)

ANTHROPIC_SUPPORTED = frozenset(
    {
        MimeTypes.PNG,
        MimeTypes.JPEG,
        MimeTypes.GIF,
        MimeTypes.WEBP,
        MimeTypes.PDF,
    }
)

GOOGLE_SUPPORTED = frozenset(
    {
        *IMAGE_TYPES,
        *DOCUMENT_TYPES,
        *AUDIO_TYPES,
        *VIDEO_TYPES,
    }
)

PROVIDER_FAMILY_SUPPORT: dict[str, frozenset[str]] = {
    "openai": OPENAI_SUPPORTED,
    "anthropic": ANTHROPIC_SUPPORTED,
    "google": GOOGLE_SUPPORTED,
    "azure": OPENAI_SUPPORTED,
    "ollama": IMAGE_TYPES,
}


def get_supported_types(provider_family: str) -> frozenset[str]:
    return PROVIDER_FAMILY_SUPPORT.get(provider_family.lower(), IMAGE_TYPES)


def is_supported_by_provider(mime_type: str, provider_family: str) -> bool:
    supported = get_supported_types(provider_family)
    return mime_type in supported
