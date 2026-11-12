import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import cast
from unittest.mock import patch

from psycopg import OperationalError
from psycopg_pool import ConnectionPool

from app.services.ai_errors import AIProviderError
from app.services.generations import (
    GenerationAsset,
    GenerationLimitError,
    GenerationOutput,
    GenerationPersistenceError,
    InsufficientCreditsError,
    get_generation_asset,
    run_generation,
)

USER_ID = "fbd5f168-4d86-4f2e-b6e8-179151706530"


class FakeDatabase:
    """Just enough of the users / ai_generations / ledger tables for the service."""

    def __init__(self, balance: int = 10) -> None:
        self.balance = balance
        self.generations: dict[str, dict[str, object]] = {}
        self.ledger: list[tuple[str, int, str | None]] = []
        self.assets: list[tuple[object, ...]] = []
        self.running = (0, 0)
        self.fail_asset_insert = False
        self.fetch_result: tuple[object, ...] | None = None
        self.calls: list[tuple[str, tuple[object, ...] | None]] = []


class FakeConnection:
    def __init__(self, db: FakeDatabase) -> None:
        self.db = db
        self._result: list[tuple[object, ...]] = []
        # Changes are staged and applied only on commit, like a transaction.
        self._pending: list = []
        self._balance_delta = 0  # this transaction's own, uncommitted changes

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> "FakeConnection":
        db = self.db
        db.calls.append((query, params))
        sql = " ".join(query.split())
        self._result = []
        if sql.startswith("SELECT credits_balance FROM users"):
            self._result = [(db.balance + self._balance_delta,)]
        elif sql.startswith("SELECT count(*)"):
            self._result = [db.running]
        elif sql.startswith("UPDATE users SET credits_balance = credits_balance -"):
            self._balance_delta -= params[0]
            self._pending.append(lambda amount=params[0]: setattr(db, "balance", db.balance - amount))
        elif sql.startswith("UPDATE users SET credits_balance = credits_balance +"):
            self._balance_delta += params[0]
            self._pending.append(lambda amount=params[0]: setattr(db, "balance", db.balance + amount))
        elif sql.startswith("INSERT INTO ai_generations"):
            generation_id, _, _, _, cost, _ = params
            self._pending.append(
                lambda: db.generations.__setitem__(
                    generation_id, {"status": "processing", "cost": cost}
                )
            )
        elif sql.startswith("INSERT INTO credit_transactions"):
            if "'generation_refund'" in sql:
                self._pending.append(lambda p=params: db.ledger.append(("generation_refund", p[1], p[3])))
            else:
                self._pending.append(lambda p=params: db.ledger.append((p[2], p[1], p[4])))
        elif sql.startswith("INSERT INTO generation_assets"):
            if db.fail_asset_insert:
                raise OperationalError("database unavailable")
            self._pending.append(lambda p=params: db.assets.append(p))
        elif sql.startswith("UPDATE ai_generations SET status = 'completed'"):
            cost, generation_id = params
            generation = db.generations.get(generation_id)
            if generation and generation["status"] == "processing":
                self._result = [(generation_id,)]
                self._pending.append(lambda: generation.update(status="completed", cost=cost))
        elif sql.startswith("UPDATE ai_generations SET status = 'failed'"):
            message, generation_id = params
            generation = db.generations.get(generation_id)
            if generation and generation["status"] == "processing":
                self._result = [(generation["cost"],)]
                self._pending.append(lambda: generation.update(status="failed", error=message))
        elif sql.startswith("SELECT asset.storage_url"):
            self._result = [db.fetch_result] if db.fetch_result else []
        return self

    def fetchone(self) -> tuple[object, ...] | None:
        return self._result[0] if self._result else None

    def fetchall(self) -> list[tuple[object, ...]]:
        return self._result

    def commit(self) -> None:
        for change in self._pending:
            change()
        self._pending.clear()


class FakePool:
    def __init__(self, db: FakeDatabase) -> None:
        self.db = db

    @contextmanager
    def connection(self):
        connection = FakeConnection(self.db)
        yield connection  # an exception here skips commit, i.e. rolls back
        connection.commit()


def output(*assets: GenerationAsset, refund: int = 0):
    async def produce() -> GenerationOutput:
        return GenerationOutput(assets=assets, refund_credits=refund)

    return produce


class GenerationLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.temp_dir.name)
        self.storage_patch = patch("app.services.generations.STORAGE_DIR", self.storage_dir)
        self.storage_patch.start()
        self.db = FakeDatabase(balance=10)
        self.pool = cast(ConnectionPool, FakePool(self.db))

    async def asyncTearDown(self) -> None:
        self.storage_patch.stop()
        self.temp_dir.cleanup()

    async def generate(self, cost: int, produce, generation_type: str = "image"):
        return await run_generation(
            self.pool, USER_ID, generation_type, "A quiet lake", {"style": "x"}, cost, produce
        )

    async def test_charges_credits_and_persists_assets(self) -> None:
        saved = await self.generate(
            2,
            output(
                GenerationAsset("image-1.png", "image/png", b"first"),
                GenerationAsset("image-2.png", "image/png", b"second"),
            ),
        )

        self.assertEqual(self.db.balance, 8)
        self.assertEqual(saved.credits_balance, 8)
        self.assertEqual(saved.cost_credits, 2)
        self.assertEqual(self.db.generations[saved.id]["status"], "completed")
        self.assertEqual(self.db.ledger, [("spend_image", -2, saved.id)])
        self.assertEqual([asset[0] for asset in self.db.assets], list(saved.asset_ids))
        generation_dir = self.storage_dir / "generations" / saved.id
        self.assertEqual((generation_dir / "image-1.png").read_bytes(), b"first")
        self.assertEqual((generation_dir / "image-2.png").read_bytes(), b"second")

    async def test_rejects_when_balance_is_too_low(self) -> None:
        self.db.balance = 5
        produced = False

        async def produce() -> GenerationOutput:
            nonlocal produced
            produced = True
            return GenerationOutput(assets=(GenerationAsset("v.mp4", "video/mp4", b"v"),))

        with self.assertRaises(InsufficientCreditsError) as caught:
            await self.generate(10, produce, "video")

        self.assertEqual((caught.exception.required, caught.exception.balance), (10, 5))
        self.assertFalse(produced, "the provider must not be called without credits")
        self.assertEqual(self.db.balance, 5)
        self.assertEqual(self.db.generations, {})
        self.assertEqual(self.db.ledger, [])

    async def test_allows_only_one_running_video_per_user(self) -> None:
        self.db.running = (1, 1)
        with self.assertRaises(GenerationLimitError):
            await self.generate(10, output(GenerationAsset("v.mp4", "video/mp4", b"v")), "video")
        self.assertEqual(self.db.balance, 10)

    async def test_refunds_when_provider_fails(self) -> None:
        async def produce() -> GenerationOutput:
            raise AIProviderError(504, "Provider timed out.")

        with self.assertRaises(AIProviderError):
            await self.generate(10, produce, "video")

        self.assertEqual(self.db.balance, 10)
        (generation_id, generation), = self.db.generations.items()
        self.assertEqual(generation["status"], "failed")
        self.assertEqual(generation["error"], "Provider timed out.")
        self.assertEqual(
            self.db.ledger,
            [("spend_video", -10, generation_id), ("generation_refund", 10, generation_id)],
        )

    async def test_refunds_unused_credits_for_partial_results(self) -> None:
        saved = await self.generate(
            4,
            output(GenerationAsset("image-1.png", "image/png", b"only one"), refund=3),
        )

        self.assertEqual(self.db.balance, 9)
        self.assertEqual(saved.cost_credits, 1)
        self.assertEqual(saved.credits_balance, 9)
        self.assertEqual(self.db.generations[saved.id]["cost"], 1)
        self.assertEqual(
            self.db.ledger,
            [("spend_image", -4, saved.id), ("generation_refund", 3, saved.id)],
        )

    async def test_removes_files_and_refunds_when_saving_fails(self) -> None:
        self.db.fail_asset_insert = True

        with self.assertRaises(GenerationPersistenceError):
            await self.generate(10, output(GenerationAsset("video.mp4", "video/mp4", b"v")), "video")

        self.assertEqual(self.db.balance, 10)
        self.assertEqual(list((self.storage_dir / "generations").iterdir()), [])
        (generation,) = self.db.generations.values()
        self.assertEqual(generation["status"], "failed")

    async def test_rejects_unsafe_asset_filenames_and_refunds(self) -> None:
        with self.assertRaises(ValueError):
            await self.generate(1, output(GenerationAsset("../evil.png", "image/png", b"x")))
        self.assertEqual(self.db.balance, 10)

    def test_asset_lookup_is_scoped_to_owning_user(self) -> None:
        asset_file = self.storage_dir / "generations" / "generation-id" / "website.json"
        asset_file.parent.mkdir(parents=True)
        asset_file.write_text('{"title":"Site"}', encoding="utf-8")
        self.db.fetch_result = ("generations/generation-id/website.json", "application/json")

        asset = get_generation_asset(
            self.pool,
            USER_ID,
            "5f202bb9-11e7-48f5-914b-1e287e09509e",
            "e8532246-6902-4551-87e8-6b3f8074d345",
        )

        self.assertEqual(asset, (asset_file, "application/json"))
        query, params = self.db.calls[0]
        self.assertIn("generation.user_id = %s::uuid", query)
        self.assertEqual(
            params,
            (
                "5f202bb9-11e7-48f5-914b-1e287e09509e",
                "e8532246-6902-4551-87e8-6b3f8074d345",
                USER_ID,
            ),
        )

    def test_asset_lookup_rejects_paths_outside_storage(self) -> None:
        self.db.fetch_result = ("../../etc/passwd", "text/plain")
        self.assertIsNone(get_generation_asset(self.pool, USER_ID, "a", "b"))


if __name__ == "__main__":
    unittest.main()
