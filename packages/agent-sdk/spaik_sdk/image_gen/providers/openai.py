import base64

import httpx

from spaik_sdk.image_gen.options import ImageFormat, ImageGenOptions

OPENAI_IMAGES_ENDPOINT = "https://api.openai.com/v1/images/generations"


async def generate_image(
    prompt: str,
    model: str,
    api_key: str,
    options: ImageGenOptions,
    endpoint: str | None = None,
    headers: dict[str, str] | None = None,
) -> bytes:
    url = endpoint or OPENAI_IMAGES_ENDPOINT

    request_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if headers:
        request_headers.update(headers)

    size = f"{options.width}x{options.height}"

    response_format_map = {
        ImageFormat.PNG: "png",
        ImageFormat.JPEG: "jpeg",
        ImageFormat.WEBP: "webp",
    }

    payload: dict = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": options.quality.value,
        "output_format": response_format_map[options.output_format],
        "n": 1,
    }
    payload.update(options.vendor)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=request_headers, json=payload)
        if response.status_code != 200:
            raise ValueError(f"OpenAI API error {response.status_code}: {response.text}")
        data = response.json()

    image_data = data["data"][0]
    if "b64_json" in image_data:
        return base64.b64decode(image_data["b64_json"])
    elif "url" in image_data:
        async with httpx.AsyncClient(timeout=120.0) as client:
            img_response = await client.get(image_data["url"])
            img_response.raise_for_status()
            return img_response.content
    else:
        raise ValueError(f"Unexpected response format: {image_data.keys()}")
