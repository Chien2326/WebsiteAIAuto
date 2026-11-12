from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.dependencies import require_admin
from app.database.connection import get_connection_pool
from app.models.user import User
from app.services.auth import count_users, list_users


router = APIRouter(prefix="/api/admin", tags=["admin"])
CurrentAdmin = Annotated[User, Depends(require_admin)]


@router.get("/summary")
async def dashboard(
    request: Request,
    current_user: CurrentAdmin,
) -> dict[str, int]:
    return {"user_count": await count_users(get_connection_pool(request))}


@router.get("/users")
async def users(
    request: Request,
    current_user: CurrentAdmin,
) -> list[dict[str, str | bool | int | None]]:
    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "credits_balance": user.credits_balance,
        }
        for user in await list_users(get_connection_pool(request))
    ]
