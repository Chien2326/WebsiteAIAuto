import logging

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.core.rate_limit import client_ip, contact_limiter, enforce
from app.database.connection import get_connection_pool
from app.services.contacts import ContactPersistenceError, save_contact_message


router = APIRouter(prefix="/api/contact", tags=["contact"])
logger = logging.getLogger(__name__)


class ContactMessagePayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    subject: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=5000)

    @field_validator("name", "subject", "message")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Trường này không được để trống.")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        try:
            email = validate_email(
                value.strip(),
                check_deliverability=False,
                allow_display_name=False,
            ).normalized.lower()
        except EmailNotValidError as error:
            raise ValueError("Vui lòng nhập địa chỉ email hợp lệ.") from error
        if len(email) > 255:
            raise ValueError("Địa chỉ email không được vượt quá 255 ký tự.")
        return email


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_contact_message(
    payload: ContactMessagePayload,
    request: Request,
) -> dict[str, str]:
    enforce(
        contact_limiter,
        f"ip:{client_ip(request)}",
        "Bạn đã gửi quá nhiều tin nhắn. Vui lòng thử lại sau ít phút.",
    )
    pool = get_connection_pool(request)
    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cần cấu hình PostgreSQL để lưu tin nhắn liên hệ.",
        )

    try:
        message_id = await save_contact_message(
            pool,
            payload.name,
            payload.email,
            payload.subject,
            payload.message,
        )
    except ContactPersistenceError as error:
        logger.exception("Could not save a contact message")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể lưu tin nhắn lúc này. Vui lòng thử lại sau.",
        ) from error

    return {"id": message_id, "message": "Tin nhắn của bạn đã được gửi."}
