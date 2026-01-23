from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ImageQuality(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ImageFormat(Enum):
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


@dataclass
class ImageGenOptions:
    width: int = 1024
    height: int = 1024
    quality: ImageQuality = ImageQuality.MEDIUM
    output_format: ImageFormat = ImageFormat.PNG
    vendor: dict[str, Any] = field(default_factory=dict)
