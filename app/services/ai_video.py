import asyncio
import json
import random
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from app.core.config import POLLINATIONS_VIDEO_MODEL
from app.services.ai_errors import AIProviderError


VIDEO_URL = "https://gen.pollinations.ai/video"
MAX_VIDEO_BYTES = 100 * 1024 * 1024
VIDEO_STYLE_DESCRIPTIONS = {
    "Điện ảnh": "cinematic composition, camera movement, and lighting",
    "Tả thực": "photorealistic imagery and natural motion",
    "Hoạt hình": "colorful animated style and expressive motion",
    "3D": "detailed 3D rendering and smooth motion",
}


class VideoGenerationError(AIProviderError):
    pass


def _generate_video(
    prompt: str,
    style: str,
    aspect_ratio: str,
    duration: int,
    api_key: str,
) -> bytes:
    video_prompt = f"{prompt}\n\nStyle: {VIDEO_STYLE_DESCRIPTIONS[style]}. Generate one video."
    query = urlencode({
        "model": POLLINATIONS_VIDEO_MODEL,
        "aspectRatio": aspect_ratio,
        "duration": duration,
        "seed": random.SystemRandom().randint(0, 2**31 - 1),
    })
    request = Request(
        f"{VIDEO_URL}/{quote(video_prompt, safe='')}?{query}",
        headers={"Authorization": f"Bearer {api_key}"},
    )

    try:
        with urlopen(request, timeout=300) as response:
            content_type = response.headers.get_content_type()
            video = response.read(MAX_VIDEO_BYTES + 1)
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
            detail = "API key Pollinations không có quyền truy cập model video đã chọn."
        elif error.code == 429:
            detail = "Pollinations đang giới hạn yêu cầu video. Vui lòng thử lại sau."
        elif error.code == 400:
            detail = "Pollinations không chấp nhận yêu cầu tạo video này."
        else:
            detail = "Không thể tạo video với Pollinations lúc này."
        if isinstance(message, str) and message.strip():
            detail = f"{detail} Chi tiết: {message.strip()[:500]}"
        raise VideoGenerationError(
            error.code if error.code in {400, 401, 402, 403, 429} else 502,
            detail,
        ) from error
    except TimeoutError as error:
        raise VideoGenerationError(504, "Pollinations tạo video quá lâu. Vui lòng thử lại.") from error
    except URLError as error:
        raise VideoGenerationError(502, "Không thể kết nối Pollinations. Vui lòng thử lại sau.") from error

    if content_type != "video/mp4":
        raise VideoGenerationError(502, "Pollinations không trả về video MP4 hợp lệ.")
    if len(video) > MAX_VIDEO_BYTES:
        raise VideoGenerationError(502, "Video Pollinations trả về vượt quá giới hạn kích thước.")
    if not video:
        raise VideoGenerationError(502, "Pollinations trả về video rỗng.")
    return video


async def generate_video(
    prompt: str,
    style: str,
    aspect_ratio: str,
    duration: int,
    api_key: str,
) -> bytes:
    return await asyncio.to_thread(
        _generate_video,
        prompt,
        style,
        aspect_ratio,
        duration,
        api_key,
    )