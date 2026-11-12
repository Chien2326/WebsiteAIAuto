"""AI generation lifecycle: reserve credits, run the provider, then complete or refund.

1. reserve: lock the user row, check balance and concurrency, debit credits,
   insert the generation as 'processing' and the spend ledger row (one transaction).
2. The provider call runs outside any database transaction.
3. complete: write files, insert assets, mark 'completed', refund unused credits.
   fail: mark 'failed' and refund the whole cost (each at most once per generation).
"""

import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import anyio
from psycopg import Connection
from psycopg import Error as PsycopgError
from psycopg_pool import ConnectionPool, PoolTimeout


logger = logging.getLogger(__name__)
STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage"

# A generation still 'processing' after this long was interrupted (for example
# by a server restart) and is failed and refunded by recover_stale_generations.
STALE_AFTER_MINUTES = 15
MAX_CONCURRENT_GENERATIONS = 3
MAX_CONCURRENT_VIDEO_GENERATIONS = 1
SPEND_TYPES = {
    "image": "spend_image",
    "video": "spend_video",
    "website": "spend_website",
}


@dataclass(frozen=True)
class GenerationAsset:
    filename: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class GenerationOutput:
    assets: tuple[GenerationAsset, ...]
    # Credits to return because only part of the request was produced.
    refund_credits: int = 0


@dataclass(frozen=True)
class ReservedGeneration:
    id: str
    user_id: str
    cost: int


@dataclass(frozen=True)
class SavedGeneration:
    id: str
    asset_ids: tuple[str, ...]
    cost_credits: int
    credits_balance: int


class GenerationPersistenceError(Exception):
    pass


class InsufficientCreditsError(Exception):
    def __init__(self, required: int, balance: int) -> None:
        super().__init__(f"Required {required} credits, balance is {balance}.")
        self.required = required
        self.balance = balance


class GenerationLimitError(Exception):
    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def _validate_assets(assets: tuple[GenerationAsset, ...]) -> None:
    if not assets:
        raise ValueError("A completed generation must contain at least one asset.")
    if any(
        not asset.filename
        or asset.filename in {".", ".."}
        or "/" in asset.filename
        or "\\" in asset.filename
        for asset in assets
    ):
        raise ValueError("Generation asset filenames must be plain filenames.")
    if len({asset.filename for asset in assets}) != len(assets):
        raise ValueError("Generation asset filenames must be unique.")


def _refund(
    connection: Connection,
    user_id: str,
    generation_id: str,
    amount: int,
    description: str,
) -> None:
    connection.execute(
        "UPDATE users SET credits_balance = credits_balance + %s WHERE id = %s::uuid",
        (amount, user_id),
    )
    connection.execute(
        """
        INSERT INTO credit_transactions (
            user_id, amount, type, description, generation_id, idempotency_key
        )
        VALUES (%s::uuid, %s, 'generation_refund', %s, %s::uuid, %s)
        """,
        (user_id, amount, description, generation_id, f"refund:{generation_id}"),
    )


def _reserve_generation(
    pool: ConnectionPool,
    user_id: str,
    generation_type: str,
    prompt: str,
    settings: dict[str, object],
    cost: int,
) -> ReservedGeneration:
    generation_id = str(uuid4())
    # pool.connection() commits on success and rolls back on any exception.
    with pool.connection() as connection:
        row = connection.execute(
            """
            SELECT credits_balance FROM users
            WHERE id = %s::uuid AND deleted_at IS NULL AND is_active
            FOR UPDATE
            """,
            (user_id,),
        ).fetchone()
        if row is None:
            raise GenerationPersistenceError("The user account is not available.")
        balance = row[0]
        if balance < cost:
            raise InsufficientCreditsError(cost, balance)

        # The user row lock above serializes this check per user.
        running = connection.execute(
            """
            SELECT count(*), count(*) FILTER (WHERE type = 'video')
            FROM ai_generations
            WHERE user_id = %s::uuid
              AND status = 'processing'
              AND started_at > CURRENT_TIMESTAMP - make_interval(mins => %s)
            """,
            (user_id, STALE_AFTER_MINUTES),
        ).fetchone()
        running_total, running_videos = running if running else (0, 0)
        if generation_type == "video" and running_videos >= MAX_CONCURRENT_VIDEO_GENERATIONS:
            raise GenerationLimitError(
                "Bạn đang có một video đang được tạo. Vui lòng đợi video đó hoàn tất."
            )
        if running_total >= MAX_CONCURRENT_GENERATIONS:
            raise GenerationLimitError(
                "Bạn đang có quá nhiều yêu cầu đang xử lý. Vui lòng đợi rồi thử lại."
            )

        connection.execute(
            "UPDATE users SET credits_balance = credits_balance - %s WHERE id = %s::uuid",
            (cost, user_id),
        )
        connection.execute(
            """
            INSERT INTO ai_generations (
                id, user_id, type, prompt, status, cost_credits, settings, started_at
            )
            VALUES (
                %s::uuid, %s::uuid, %s, %s, 'processing', %s, %s::jsonb, CURRENT_TIMESTAMP
            )
            """,
            (
                generation_id,
                user_id,
                generation_type,
                prompt,
                cost,
                json.dumps(settings, ensure_ascii=False),
            ),
        )
        connection.execute(
            """
            INSERT INTO credit_transactions (
                user_id, amount, type, description, generation_id, idempotency_key
            )
            VALUES (%s::uuid, %s, %s, %s, %s::uuid, %s)
            """,
            (
                user_id,
                -cost,
                SPEND_TYPES[generation_type],
                f"AI {generation_type} generation",
                generation_id,
                f"spend:{generation_id}",
            ),
        )
    return ReservedGeneration(id=generation_id, user_id=user_id, cost=cost)


def _cleanup_generation_files(directory: Path, paths: list[Path]) -> None:
    for path in reversed(paths):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Could not remove incomplete generation asset %s", path)
    try:
        directory.rmdir()
    except FileNotFoundError:
        pass
    except OSError:
        logger.exception("Could not remove incomplete generation directory %s", directory)


def _complete_generation(
    pool: ConnectionPool,
    reserved: ReservedGeneration,
    output: GenerationOutput,
) -> SavedGeneration:
    refund = min(max(output.refund_credits, 0), reserved.cost)
    asset_ids = tuple(str(uuid4()) for _ in output.assets)
    generation_dir = STORAGE_DIR / "generations" / reserved.id
    written_paths: list[Path] = []
    records: list[tuple[str, str, str, int, int]] = []
    directory_created = False

    try:
        generation_dir.mkdir(parents=True, exist_ok=False)
        directory_created = True
        for position, (asset, asset_id) in enumerate(
            zip(output.assets, asset_ids, strict=True)
        ):
            path = generation_dir / asset.filename
            written_paths.append(path)
            path.write_bytes(asset.content)
            storage_url = Path("generations", reserved.id, asset.filename).as_posix()
            records.append(
                (asset_id, storage_url, asset.content_type, len(asset.content), position)
            )

        with pool.connection() as connection:
            for asset_id, storage_url, content_type, file_size, position in records:
                connection.execute(
                    """
                    INSERT INTO generation_assets (
                        id, generation_id, asset_type, storage_url, content_type,
                        file_size_bytes, position
                    )
                    VALUES (%s::uuid, %s::uuid, 'output', %s, %s, %s, %s)
                    """,
                    (
                        asset_id,
                        reserved.id,
                        storage_url,
                        content_type,
                        file_size,
                        position,
                    ),
                )
            updated = connection.execute(
                """
                UPDATE ai_generations
                SET status = 'completed', cost_credits = %s,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = %s::uuid AND status = 'processing'
                RETURNING id
                """,
                (reserved.cost - refund, reserved.id),
            ).fetchone()
            if updated is None:
                # Already failed (and refunded) by stale recovery; do not keep it.
                raise GenerationPersistenceError("The generation is no longer processing.")
            if refund > 0:
                _refund(
                    connection,
                    reserved.user_id,
                    reserved.id,
                    refund,
                    "Unused credits for a partially completed generation",
                )
            balance_row = connection.execute(
                "SELECT credits_balance FROM users WHERE id = %s::uuid",
                (reserved.user_id,),
            ).fetchone()
    except (OSError, PsycopgError, PoolTimeout, GenerationPersistenceError) as error:
        if directory_created:
            _cleanup_generation_files(generation_dir, written_paths)
        logger.exception("Could not persist AI generation %s", reserved.id)
        raise GenerationPersistenceError(
            "Không thể lưu kết quả tạo AI vào hệ thống."
        ) from error

    return SavedGeneration(
        id=reserved.id,
        asset_ids=asset_ids,
        cost_credits=reserved.cost - refund,
        credits_balance=balance_row[0] if balance_row else 0,
    )


def _fail_generation(
    pool: ConnectionPool,
    reserved: ReservedGeneration,
    error_message: str,
) -> None:
    with pool.connection() as connection:
        row = connection.execute(
            """
            UPDATE ai_generations
            SET status = 'failed', error_message = %s, completed_at = CURRENT_TIMESTAMP
            WHERE id = %s::uuid AND status = 'processing'
            RETURNING cost_credits
            """,
            (error_message[:2000] or "Generation failed.", reserved.id),
        ).fetchone()
        if row is not None and row[0] > 0:
            _refund(
                connection,
                reserved.user_id,
                reserved.id,
                row[0],
                "Refund for a failed generation",
            )


def _recover_stale_generations(pool: ConnectionPool) -> int:
    with pool.connection() as connection:
        rows = connection.execute(
            """
            UPDATE ai_generations
            SET status = 'failed',
                error_message = 'Generation was interrupted before completion.',
                completed_at = CURRENT_TIMESTAMP
            WHERE status = 'processing'
              AND started_at <= CURRENT_TIMESTAMP - make_interval(mins => %s)
            RETURNING id::text, user_id::text, cost_credits
            """,
            (STALE_AFTER_MINUTES,),
        ).fetchall()
        for generation_id, user_id, cost in rows:
            if cost > 0:
                _refund(
                    connection,
                    user_id,
                    generation_id,
                    cost,
                    "Refund for an interrupted generation",
                )
    return len(rows)


async def recover_stale_generations(pool: ConnectionPool) -> int:
    return await anyio.to_thread.run_sync(_recover_stale_generations, pool)


async def _fail_quietly(pool: ConnectionPool, reserved: ReservedGeneration, message: str) -> None:
    try:
        await anyio.to_thread.run_sync(_fail_generation, pool, reserved, message)
    except (PsycopgError, PoolTimeout):
        # The generation stays 'processing' and is refunded by stale recovery.
        logger.exception("Could not mark generation %s as failed", reserved.id)


async def run_generation(
    pool: ConnectionPool,
    user_id: str,
    generation_type: str,
    prompt: str,
    settings: dict[str, object],
    cost: int,
    produce: Callable[[], Awaitable[GenerationOutput]],
) -> SavedGeneration:
    """Charge `cost` credits, run `produce`, and persist its output.

    Raises InsufficientCreditsError, GenerationLimitError, or
    GenerationPersistenceError, or re-raises whatever `produce` raised. On any
    failure after the charge, the credits are refunded.
    """
    if generation_type not in SPEND_TYPES:
        raise ValueError(f"Unknown generation type: {generation_type}")
    if cost <= 0:
        raise ValueError("A generation must cost at least one credit.")

    try:
        reserved = await anyio.to_thread.run_sync(
            _reserve_generation,
            pool,
            user_id,
            generation_type,
            prompt,
            settings,
            cost,
        )
    except (PsycopgError, PoolTimeout) as error:
        logger.exception("Could not reserve credits for a %s generation", generation_type)
        raise GenerationPersistenceError("Không thể giữ credit cho yêu cầu này.") from error

    try:
        output = await produce()
        _validate_assets(output.assets)
    except BaseException as error:
        detail = getattr(error, "detail", None)
        # Shielded so a cancelled request still records the failure and refund.
        with anyio.CancelScope(shield=True):
            await _fail_quietly(
                pool,
                reserved,
                detail if isinstance(detail, str) else f"{type(error).__name__}: {error}",
            )
        raise

    try:
        return await anyio.to_thread.run_sync(_complete_generation, pool, reserved, output)
    except GenerationPersistenceError:
        with anyio.CancelScope(shield=True):
            await _fail_quietly(pool, reserved, "The generated output could not be saved.")
        raise


def get_generation_asset(
    pool: ConnectionPool,
    user_id: str,
    generation_id: str,
    asset_id: str,
) -> tuple[Path, str | None] | None:
    with pool.connection() as connection:
        row = connection.execute(
            """
            SELECT asset.storage_url, asset.content_type
            FROM generation_assets AS asset
            JOIN ai_generations AS generation
                ON generation.id = asset.generation_id
            WHERE generation.id = %s::uuid
              AND asset.id = %s::uuid
              AND generation.user_id = %s::uuid
            """,
            (generation_id, asset_id, user_id),
        ).fetchone()

    if row is None:
        return None

    storage_root = STORAGE_DIR.resolve()
    asset_path = (storage_root / row[0]).resolve()
    try:
        asset_path.relative_to(storage_root)
    except ValueError:
        logger.error("Generation asset path escapes storage root: %s", row[0])
        return None
    if not asset_path.is_file():
        raise FileNotFoundError(f"Stored generation asset is missing: {asset_path}")
    return asset_path, row[1]


def asset_url(generation_id: str, asset_id: str) -> str:
    return f"/api/generations/{generation_id}/assets/{asset_id}"
