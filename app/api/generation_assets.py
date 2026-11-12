import logging
from uuid import UUID

import anyio
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from psycopg import Error as PsycopgError
from psycopg_pool import PoolTimeout

from app.core.dependencies import CurrentUser, DbPool
from app.services.generations import get_generation_asset


router = APIRouter(prefix="/api/generations", tags=["generations"])
logger = logging.getLogger(__name__)


@router.get("/{generation_id}/assets/{asset_id}")
async def generation_asset(
    generation_id: UUID,
    asset_id: UUID,
    user: CurrentUser,
    pool: DbPool,
) -> FileResponse:
    try:
        asset = await anyio.to_thread.run_sync(
            get_generation_asset,
            pool,
            user.id,
            str(generation_id),
            str(asset_id),
        )
    except (PsycopgError, PoolTimeout) as error:
        logger.exception("Could not read generation asset metadata")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể truy cập kết quả đã lưu lúc này.",
        ) from error
    except FileNotFoundError as error:
        logger.exception("A generation asset is missing from storage")
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Tệp kết quả không còn trên máy chủ.",
        ) from error

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy kết quả này.",
        )

    asset_path, content_type = asset
    # Saved outputs never change; let the owner's browser cache them.
    return FileResponse(
        asset_path,
        media_type=content_type,
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
    )
