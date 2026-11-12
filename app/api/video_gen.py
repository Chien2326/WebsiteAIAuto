from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.api.generation_common import run_generation_or_http_error
from app.core.config import POLLINATIONS_VIDEO_MODEL
from app.core.credits import video_cost
from app.core.dependencies import AIApiKey, CurrentUser, DbPool
from app.services.ai_video import generate_video
from app.services.generations import GenerationAsset, GenerationOutput, asset_url


router = APIRouter(prefix="/api/video", tags=["video generation"])


class VideoGenerationPayload(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    style: Literal["Điện ảnh", "Tả thực", "Hoạt hình", "3D"] = "Điện ảnh"
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9"
    duration: Literal[5, 10] = 5

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, prompt: str) -> str:
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Vui lòng nhập nội dung mô tả video.")
        return prompt


@router.post("/generate")
async def create_video(
    payload: VideoGenerationPayload,
    user: CurrentUser,
    pool: DbPool,
    api_key: AIApiKey,
) -> dict[str, object]:
    async def produce() -> GenerationOutput:
        video = await generate_video(
            payload.prompt,
            payload.style,
            payload.aspect_ratio,
            payload.duration,
            api_key,
        )
        return GenerationOutput(
            assets=(GenerationAsset("video.mp4", "video/mp4", video),),
        )

    saved = await run_generation_or_http_error(
        pool,
        user,
        "video",
        payload.prompt,
        {
            "provider": "pollinations",
            "model": POLLINATIONS_VIDEO_MODEL,
            "style": payload.style,
            "aspect_ratio": payload.aspect_ratio,
            "duration": payload.duration,
        },
        video_cost(payload.duration),
        produce,
    )

    return {
        "model": POLLINATIONS_VIDEO_MODEL,
        "generation_id": saved.id,
        "asset_url": asset_url(saved.id, saved.asset_ids[0]),
        "cost_credits": saved.cost_credits,
        "credits_balance": saved.credits_balance,
    }
