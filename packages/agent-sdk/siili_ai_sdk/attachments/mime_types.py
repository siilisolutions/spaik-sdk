from pathlib import Path
from typing import Optional


class MimeTypes:
    # Images
    PNG = "image/png"
    JPEG = "image/jpeg"
    GIF = "image/gif"
    WEBP = "image/webp"
    SVG = "image/svg+xml"

    # Documents
    PDF = "application/pdf"

    # Audio
    MP3 = "audio/mpeg"
    WAV = "audio/wav"
    OGG = "audio/ogg"
    WEBM_AUDIO = "audio/webm"

    # Video
    MP4 = "video/mp4"
    WEBM_VIDEO = "video/webm"
    MOV = "video/quicktime"

    # Text
    PLAIN = "text/plain"
    HTML = "text/html"
    CSV = "text/csv"


IMAGE_TYPES = frozenset(
    {
        MimeTypes.PNG,
        MimeTypes.JPEG,
        MimeTypes.GIF,
        MimeTypes.WEBP,
        MimeTypes.SVG,
    }
)

DOCUMENT_TYPES = frozenset(
    {
        MimeTypes.PDF,
    }
)

AUDIO_TYPES = frozenset(
    {
        MimeTypes.MP3,
        MimeTypes.WAV,
        MimeTypes.OGG,
        MimeTypes.WEBM_AUDIO,
    }
)

VIDEO_TYPES = frozenset(
    {
        MimeTypes.MP4,
        MimeTypes.WEBM_VIDEO,
        MimeTypes.MOV,
    }
)

TEXT_TYPES = frozenset(
    {
        MimeTypes.PLAIN,
        MimeTypes.HTML,
        MimeTypes.CSV,
    }
)

ALL_SUPPORTED_TYPES = IMAGE_TYPES | DOCUMENT_TYPES | AUDIO_TYPES | VIDEO_TYPES | TEXT_TYPES

EXTENSION_TO_MIME: dict[str, str] = {
    ".png": MimeTypes.PNG,
    ".jpg": MimeTypes.JPEG,
    ".jpeg": MimeTypes.JPEG,
    ".gif": MimeTypes.GIF,
    ".webp": MimeTypes.WEBP,
    ".svg": MimeTypes.SVG,
    ".pdf": MimeTypes.PDF,
    ".mp3": MimeTypes.MP3,
    ".wav": MimeTypes.WAV,
    ".ogg": MimeTypes.OGG,
    ".mp4": MimeTypes.MP4,
    ".webm": MimeTypes.WEBM_VIDEO,
    ".mov": MimeTypes.MOV,
    ".txt": MimeTypes.PLAIN,
    ".html": MimeTypes.HTML,
    ".csv": MimeTypes.CSV,
}


def guess_mime_type(path: str | Path) -> Optional[str]:
    suffix = Path(path).suffix.lower()
    return EXTENSION_TO_MIME.get(suffix)


def is_image(mime_type: str) -> bool:
    return mime_type in IMAGE_TYPES


def is_document(mime_type: str) -> bool:
    return mime_type in DOCUMENT_TYPES


def is_audio(mime_type: str) -> bool:
    return mime_type in AUDIO_TYPES


def is_video(mime_type: str) -> bool:
    return mime_type in VIDEO_TYPES


def is_supported(mime_type: str) -> bool:
    return mime_type in ALL_SUPPORTED_TYPES
