from collections.abc import Awaitable, Callable

from fastapi import HTTPException, status
from psycopg_pool import ConnectionPool

from app.core.rate_limit import enforce, generation_limiter
from app.models.user import User
from app.services.ai_errors import AIProviderError
from app.services.generations import (
    GenerationLimitError,
    GenerationOutput,
    GenerationPersistenceError,
    InsufficientCreditsError,
    SavedGeneration,
    run_generation,
)


async def run_generation_or_http_error(
    pool: ConnectionPool,
    user: User,
    generation_type: str,
    prompt: str,
    settings: dict[str, object],
    cost: int,
    produce: Callable[[], Awaitable[GenerationOutput]],
) -> SavedGeneration:
    enforce(
        generation_limiter,
        f"user:{user.id}",
        "Bạn đã gửi quá nhiều yêu cầu tạo nội dung. Vui lòng thử lại sau ít phút.",
    )
    try:
        return await run_generation(
            pool,
            user.id,
            generation_type,
            prompt,
            settings,
            cost,
            produce,
        )
    except InsufficientCreditsError as error:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Bạn cần {error.required} credit cho yêu cầu này "
                f"nhưng chỉ còn {error.balance} credit."
            ),
        ) from error
    except GenerationLimitError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error.detail,
        ) from error
    except AIProviderError as error:
        # Provider auth/billing problems are server configuration issues. Never
        # forward 401/402/403: the browser treats those as the user's own state.
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if error.status_code in {401, 402, 403}
            else error.status_code
        )
        raise HTTPException(
            status_code=status_code,
            detail=f"{error.detail} Credit của bạn không bị trừ cho yêu cầu này.",
        ) from error
    except GenerationPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Không thể lưu kết quả vào hệ thống. "
                "Credit của bạn không bị trừ cho yêu cầu này, vui lòng thử lại."
            ),
        ) from error
