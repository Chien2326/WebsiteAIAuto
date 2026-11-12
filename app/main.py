import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from pathlib import Path

import anyio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from psycopg import Error as PsycopgError
from psycopg_pool import ConnectionPool, PoolTimeout
from starlette.middleware.sessions import SessionMiddleware

from app.api.auth import router as auth_api_router
from app.api.contact import router as contact_api_router
from app.api.generation_assets import router as generation_assets_router
from app.api.image_gen import router as image_gen_router
from app.api.video_gen import router as video_gen_router
from app.api.website_gen import router as website_gen_router
from app.core.config import SESSION_HTTPS_ONLY, SESSION_SECRET
from app.database.connection import create_connection_pool
from app.routers.admin import router as admin_router
from app.routers.pages import router as pages_router
from app.services.generations import recover_stale_generations

FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
STALE_RECOVERY_INTERVAL_SECONDS = 5 * 60
SESSION_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
logger = logging.getLogger(__name__)


async def _recover_stale_generations_forever(pool: ConnectionPool) -> None:
    """Fail and refund generations left 'processing' by a crash or lost request."""
    while True:
        try:
            recovered = await recover_stale_generations(pool)
            if recovered:
                logger.warning("Refunded %s interrupted AI generations", recovered)
        except (PsycopgError, PoolTimeout):
            logger.exception("Could not recover interrupted AI generations")
        await asyncio.sleep(STALE_RECOVERY_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = create_connection_pool()
    app.state.db_pool = pool

    if pool is None:
        yield
        return

    await anyio.to_thread.run_sync(lambda: pool.open(wait=True, timeout=30))
    recovery_task = asyncio.create_task(_recover_stale_generations_forever(pool))
    try:
        yield
    finally:
        recovery_task.cancel()
        with suppress(asyncio.CancelledError):
            await recovery_task
        await anyio.to_thread.run_sync(pool.close)


app = FastAPI(
    title="WebAiAuto",
    description="Nền tảng AI tạo hình ảnh, video và website",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=SESSION_HTTPS_ONLY,
    max_age=SESSION_MAX_AGE_SECONDS,
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


app.mount(
    "/assets",
    StaticFiles(directory=str(FRONTEND_DIST / "assets"), check_dir=False),
    name="frontend-assets",
)

app.include_router(auth_api_router)
app.include_router(contact_api_router)
app.include_router(generation_assets_router)
app.include_router(image_gen_router)
app.include_router(video_gen_router)
app.include_router(website_gen_router)
app.include_router(admin_router)
# Must stay last: it contains the /api 404 fallback and the SPA catch-all.
app.include_router(pages_router)
