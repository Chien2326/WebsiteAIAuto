import json
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.api.generation_common import run_generation_or_http_error
from app.core.config import POLLINATIONS_TEXT_MODEL
from app.core.credits import website_cost
from app.core.dependencies import AIApiKey, CurrentUser, DbPool
from app.services.ai_website import generate_website
from app.services.generations import GenerationAsset, GenerationOutput, asset_url


router = APIRouter(prefix="/api/website", tags=["website generation"])


class WebsiteGenerationPayload(BaseModel):
    prompt: str = Field(min_length=1, max_length=600)
    website_type: Literal["coffee", "portfolio", "agency", "restaurant"] = "coffee"
    palette: Literal["sage", "blue", "rose", "amber"] = "sage"
    language: Literal["Tiếng Việt", "English"] = "Tiếng Việt"

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, prompt: str) -> str:
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Vui lòng nhập nội dung mô tả website.")
        return prompt


@router.post("/generate")
async def create_website(
    payload: WebsiteGenerationPayload,
    user: CurrentUser,
    pool: DbPool,
    api_key: AIApiKey,
) -> dict[str, object]:
    website: dict[str, object] = {}

    async def produce() -> GenerationOutput:
        website.update(
            await generate_website(
                payload.prompt,
                payload.website_type,
                payload.palette,
                payload.language,
                api_key,
            )
        )
        return GenerationOutput(
            assets=(
                GenerationAsset(
                    "website.json",
                    "application/json",
                    json.dumps(website, ensure_ascii=False).encode("utf-8"),
                ),
            ),
        )

    saved = await run_generation_or_http_error(
        pool,
        user,
        "website",
        payload.prompt,
        {
            "provider": "pollinations",
            "model": POLLINATIONS_TEXT_MODEL,
            "website_type": payload.website_type,
            "palette": payload.palette,
            "language": payload.language,
        },
        website_cost(),
        produce,
    )

    return {
        "generation_id": saved.id,
        "asset_url": asset_url(saved.id, saved.asset_ids[0]),
        "cost_credits": saved.cost_credits,
        "credits_balance": saved.credits_balance,
        "website": website,
    }
