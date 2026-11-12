import asyncio
import base64
import json
import random
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from app.core.config import POLLINATIONS_IMAGE_MODEL
from app.services.ai_errors import AIProviderError

MODEL = POLLINATIONS_IMAGE_MODEL
IMAGE_URL = "https://gen.pollinations.ai/image"
MAX_IMAGE_BYTES = 20 * 1024 * 1024
STYLE_DESCRIPTIONS = {
    "Điện ảnh": "cinematic composition and lighting",
    "Minh họa": "artistic illustration",
    "Tả thực": "photorealistic",
    "3D": "a detailed 3D render",
}
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


class ImageGenerationError(AIProviderError):
    pass


def _generate_one(prompt: str, style: str, aspect_ratio: str, api_key: str) -> dict[str, str]:
    request_prompt = (
        f"{prompt}\n\nStyle: {STYLE_DESCRIPTIONS[style]}. "
        "Generate one image."
    )
    query = urlencode({
        "model": MODEL,
        "aspectRatio": aspect_ratio,
        "seed": random.SystemRandom().randint(0, 2**31 - 1),
    })
    request = Request(
        f"{IMAGE_URL}/{quote(request_prompt, safe='')}?{query}",
        headers={
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urlopen(request, timeout=120) as response:
            content_type = response.headers.get_content_type()
            image_data = response.read(MAX_IMAGE_BYTES + 1)
    except HTTPError as error:
        try:
            provider_error = json.loads(error.read(65536))
        except (json.JSONDecodeError, UnicodeDecodeError):
            provider_error = None
        message = provider_error.get("detail") if isinstance(provider_error, dict) else None
        if not isinstance(message, str):
            message = provider_error.get("message") if isinstance(provider_error, dict) else None
        if error.code == 401:
            detail = "Pollinations từ chối API key. Hãy kiểm tra POLLINATIONS_API_KEY."
        elif error.code == 402:
            detail = "Tài khoản Pollinations không đủ Pollen hoặc API key đã hết ngân sách."
        elif error.code == 403:
            detail = "API key Pollinations không có quyền truy cập model đã chọn."
        elif error.code == 429:
            detail = "Pollinations đang giới hạn yêu cầu. Vui lòng thử lại sau."
        elif error.code == 400:
            detail = "Pollinations không chấp nhận yêu cầu tạo ảnh này."
        else:
            detail = "Không thể tạo ảnh với Pollinations lúc này."
        if isinstance(message, str) and message.strip():
            detail = f"{detail} Chi tiết: {message.strip()[:500]}"
        raise ImageGenerationError(
            error.code if error.code in {400, 401, 402, 403, 429} else 502,
            detail,
        ) from error
    except TimeoutError as error:
        raise ImageGenerationError(
            504,
            "Pollinations phản hồi quá lâu. Vui lòng thử lại.",
        ) from error
    except URLError as error:
        raise ImageGenerationError(
            502,
            "Không thể kết nối Pollinations. Vui lòng thử lại sau.",
        ) from error

    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ImageGenerationError(
            502,
            "Pollinations không trả về định dạng ảnh được hỗ trợ.",
        )
    if len(image_data) > MAX_IMAGE_BYTES:
        raise ImageGenerationError(502, "Ảnh Pollinations trả về vượt quá giới hạn kích thước.")
    if not image_data:
        raise ImageGenerationError(502, "Pollinations trả về ảnh rỗng.")
    return {
        "mime_type": content_type,
        "data": base64.b64encode(image_data).decode("ascii"),
    }


async def generate_images(
    prompt: str,
    style: str,
    aspect_ratio: str,
    quantity: int,
    api_key: str,
) -> tuple[list[dict[str, str]], list[ImageGenerationError]]:
    """Generate images concurrently. Returns (successful images, provider errors).

    Unexpected exceptions are re-raised; provider failures for individual images
    are returned so the caller can keep partial results and refund the rest.
    """
    results = await asyncio.gather(
        *(
            asyncio.to_thread(_generate_one, prompt, style, aspect_ratio, api_key)
            for _ in range(quantity)
        ),
        return_exceptions=True,
    )
    images: list[dict[str, str]] = []
    errors: list[ImageGenerationError] = []
    for result in results:
        if isinstance(result, ImageGenerationError):
            errors.append(result)
        elif isinstance(result, BaseException):
            raise result
        else:
            images.append(result)
    return images, errors