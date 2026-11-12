import base64
import binascii
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.api.generation_common import run_generation_or_http_error
from app.core.credits import IMAGE_CREDITS_PER_IMAGE, image_cost
from app.core.dependencies import AIApiKey, CurrentUser, DbPool
from app.services.ai_image import ImageGenerationError, MODEL, generate_images
from app.services.generations import GenerationAsset, GenerationOutput, asset_url


router = APIRouter(prefix="/api/image", tags=["image generation"])
EXTENSION_BY_TYPE = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}


class ImageGenerationPayload(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    style: Literal["Điện ảnh", "Minh họa", "Tả thực", "3D"] = "Điện ảnh"
    aspect_ratio: Literal["1:1", "16:9", "9:16"] = "1:1"
    quantity: int = Field(default=1, ge=1, le=4)

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, prompt: str) -> str:
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Vui lòng nhập nội dung mô tả hình ảnh.")
        return prompt


def _to_asset(position: int, image: dict[str, str]) -> GenerationAsset:
    extension = EXTENSION_BY_TYPE.get(image.get("mime_type", ""))
    if extension is None:
        raise ImageGenerationError(502, "Pollinations trả về định dạng ảnh không được hỗ trợ.")
    try:
        content = base64.b64decode(image["data"], validate=True)
    except (binascii.Error, KeyError) as error:
        raise ImageGenerationError(
            502,
            "Không thể đọc dữ liệu ảnh do Pollinations trả về.",
        ) from error
    return GenerationAsset(
        filename=f"image-{position + 1}.{extension}",
        content_type=image["mime_type"],
        content=content,
    )


@router.post("/generate")
async def create_image(
    payload: ImageGenerationPayload,
    user: CurrentUser,
    pool: DbPool,
    api_key: AIApiKey,
) -> dict[str, object]:
    produced: list[GenerationAsset] = []

    async def produce() -> GenerationOutput:
        images, errors = await generate_images(
            payload.prompt,
            payload.style,
            payload.aspect_ratio,
            payload.quantity,
            api_key,
        )
        if not images:
            raise errors[0]
        produced.extend(_to_asset(position, image) for position, image in enumerate(images))
        return GenerationOutput(
            assets=tuple(produced),
            refund_credits=(payload.quantity - len(images)) * IMAGE_CREDITS_PER_IMAGE,
        )

    saved = await run_generation_or_http_error(
        pool,
        user,
        "image",
        payload.prompt,
        {
            "provider": "pollinations",
            "model": MODEL,
            "style": payload.style,
            "aspect_ratio": payload.aspect_ratio,
            "quantity": payload.quantity,
        },
        image_cost(payload.quantity),
        produce,
    )

    return {
        "model": MODEL,
        "generation_id": saved.id,
        "requested": payload.quantity,
        "cost_credits": saved.cost_credits,
        "credits_balance": saved.credits_balance,
        "images": [
            {"asset_url": asset_url(saved.id, asset_id), "mime_type": asset.content_type}
            for asset_id, asset in zip(saved.asset_ids, produced, strict=True)
        ],
    }
