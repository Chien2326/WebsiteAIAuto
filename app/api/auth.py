import logging

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from psycopg import Error as PsycopgError
from psycopg_pool import PoolTimeout

from app.core.config import DATABASE_URL, DEMO_AUTH_ENABLED
from app.core.credits import public_credit_prices
from app.core.dependencies import get_session_user
from app.core.rate_limit import (
    client_ip,
    enforce,
    login_failure_limiter,
    login_ip_limiter,
    register_limiter,
    too_many_requests,
)
from app.database.connection import get_connection_pool
from app.models.user import User
from app.services.auth import authenticate_user, create_user


router = APIRouter(prefix="/api", tags=["authentication"])
logger = logging.getLogger(__name__)


class LoginPayload(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=128)


class RegisterPayload(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    password_confirm: str = Field(min_length=8, max_length=128)
    terms: bool


def _serialize_user(user: User) -> dict[str, str | bool | int | None]:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "credits_balance": user.credits_balance,
    }


@router.get("/config")
async def public_config() -> dict[str, object]:
    return {
        "registration_enabled": DATABASE_URL is not None,
        "show_demo_accounts": DEMO_AUTH_ENABLED and DATABASE_URL is None,
        "credit_prices": public_credit_prices(),
    }


@router.get("/auth/me")
async def current_session_user(request: Request) -> dict[str, str | bool | int | None]:
    user = await get_session_user(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chưa đăng nhập.")
    return _serialize_user(user)


@router.post("/auth/login")
async def login(payload: LoginPayload, request: Request) -> dict[str, str | bool | int | None]:
    too_many_attempts = "Bạn đã thử đăng nhập quá nhiều lần. Vui lòng thử lại sau ít phút."
    enforce(login_ip_limiter, f"ip:{client_ip(request)}", too_many_attempts)
    email_key = f"email:{payload.email.strip().casefold()}"
    retry_after = login_failure_limiter.retry_after(email_key)
    if retry_after is not None:
        raise too_many_requests(retry_after, too_many_attempts)

    user = await authenticate_user(
        payload.email,
        payload.password,
        get_connection_pool(request),
    )
    if user is None:
        login_failure_limiter.record(email_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng.",
        )

    request.session.clear()
    request.session["user_id"] = user.id
    return _serialize_user(user)


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterPayload, request: Request) -> dict[str, str | bool | int | None]:
    enforce(
        register_limiter,
        f"ip:{client_ip(request)}",
        "Bạn đã tạo quá nhiều tài khoản. Vui lòng thử lại sau.",
    )
    pool = get_connection_pool(request)
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chưa cấu hình kết nối PostgreSQL cho ứng dụng.",
        )
    if not payload.terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng đồng ý với điều khoản sử dụng.",
        )
    if payload.password != payload.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu xác nhận không khớp.",
        )
    full_name = payload.full_name.strip()
    if not full_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Họ tên không được để trống.",
        )

    try:
        email = validate_email(
            payload.email.strip(),
            check_deliverability=False,
            allow_display_name=False,
        ).normalized.lower()
    except EmailNotValidError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng nhập địa chỉ email hợp lệ.",
        ) from error

    if len(email) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Địa chỉ email không được vượt quá 255 ký tự.",
        )

    try:
        user = await create_user(
            email,
            full_name,
            payload.password,
            pool,
        )
    except (PsycopgError, PoolTimeout) as error:
        logger.exception("Could not create a user in PostgreSQL")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể lưu tài khoản lúc này. Vui lòng thử lại sau.",
        ) from error

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email này đã được đăng ký. Vui lòng đăng nhập hoặc dùng email khác.",
        )

    request.session.clear()
    request.session["user_id"] = user.id
    return _serialize_user(user)


@router.post("/auth/logout")
async def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"success": True}
