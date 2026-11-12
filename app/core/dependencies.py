from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from psycopg_pool import ConnectionPool

from app.core.config import POLLINATIONS_API_KEY
from app.database.connection import get_connection_pool
from app.models.user import User
from app.services.auth import get_user_by_id


async def get_session_user(request: Request) -> User | None:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, str):
        return None

    user = await get_user_by_id(user_id, get_connection_pool(request))
    if user is None or not user.is_active:
        request.session.clear()
        return None
    return user


async def require_user(
    user: Annotated[User | None, Depends(get_session_user)],
) -> User:
    # API clients get a JSON 401; the React app handles navigation to /login.
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
        )
    return user


async def require_admin(
    user: Annotated[User, Depends(require_user)],
) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập khu vực quản trị.",
        )
    return user


def require_db_pool(request: Request) -> ConnectionPool:
    pool = get_connection_pool(request)
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chưa cấu hình kết nối PostgreSQL cho ứng dụng.",
        )
    return pool


def require_ai_api_key() -> str:
    if POLLINATIONS_API_KEY is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Máy chủ chưa cấu hình POLLINATIONS_API_KEY.",
        )
    return POLLINATIONS_API_KEY


CurrentUser = Annotated[User, Depends(require_user)]
DbPool = Annotated[ConnectionPool, Depends(require_db_pool)]
AIApiKey = Annotated[str, Depends(require_ai_api_key)]
