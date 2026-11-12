from dataclasses import dataclass

import anyio
from psycopg_pool import ConnectionPool

from app.core.config import DEMO_AUTH_ENABLED
from app.core.security import hash_password, verify_password, verify_stored_password
from app.models.user import User


@dataclass(frozen=True)
class _DemoAccount:
    user: User
    salt: str
    password_hash: str


_DEMO_ACCOUNTS = (
    _DemoAccount(
        user=User(
            id="demo-admin",
            email="admin@webai.test",
            full_name="Quản trị viên demo",
            role="admin",
        ),
        salt="webai-demo-admin-v1",
        password_hash="78072063e1841f38f143d730d9355d30a0b541138ee23e3b4895fb8c3270b853",
    ),
    _DemoAccount(
        user=User(
            id="demo-user",
            email="user@webai.test",
            full_name="Người dùng demo",
            role="user",
        ),
        salt="webai-demo-user-v1",
        password_hash="0e7a74121b65d749808a5a17073711ac99e0600cdd8f7f0a7cfb3bbe1a5641fc",
    ),
)


_TIMING_SALT = "webai-timing-equalizer"
_TIMING_HASH = "0" * 64


def _authenticate_demo_user(email: str, password: str) -> User | None:
    if not DEMO_AUTH_ENABLED:
        return None
    normalized_email = email.strip().casefold()
    for account in _DEMO_ACCOUNTS:
        user = account.user
        if user.email == normalized_email and verify_password(
            password,
            account.salt,
            account.password_hash,
        ):
            return user
    return None


async def authenticate_user(
    email: str,
    password: str,
    pool: ConnectionPool | None,
) -> User | None:
    if pool is None:
        return _authenticate_demo_user(email, password)

    def query_user():
        with pool.connection() as connection:
            row = connection.execute(
                """
                SELECT u.id::text, u.email, u.full_name, r.code,
                       u.password_hash, u.is_active, u.credits_balance
                FROM users AS u
                JOIN roles AS r ON r.id = u.role_id
                WHERE lower(u.email) = lower(%s) AND u.deleted_at IS NULL
                """,
                (email.strip(),),
            ).fetchone()

        if row is None:
            # Spend the same hashing time as a real check so response timing
            # does not reveal which email addresses are registered.
            verify_password(password, _TIMING_SALT, _TIMING_HASH)
            return None
        if not row[5] or not verify_stored_password(password, row[4]):
            return None

        with pool.connection() as connection:
            connection.execute(
                "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = %s::uuid",
                (row[0],),
            )
        return row

    row = await anyio.to_thread.run_sync(query_user)
    if row is None:
        return None
    return User(
        id=row[0],
        email=row[1],
        full_name=row[2] or "",
        role=row[3],
        is_active=row[5],
        credits_balance=row[6],
    )


async def get_user_by_id(
    user_id: str,
    pool: ConnectionPool | None,
) -> User | None:
    if pool is None:
        if not DEMO_AUTH_ENABLED:
            return None

        for account in _DEMO_ACCOUNTS:
            if account.user.id == user_id:
                return account.user
        return None

    def query_user():
        with pool.connection() as connection:
            return connection.execute(
                """
                SELECT u.id::text, u.email, u.full_name, r.code, u.is_active,
                       u.credits_balance
                FROM users AS u
                JOIN roles AS r ON r.id = u.role_id
                WHERE u.id = %s::uuid AND u.deleted_at IS NULL
                """,
                (user_id,),
            ).fetchone()

    row = await anyio.to_thread.run_sync(query_user)

    if row is None:
        return None

    return User(
        id=row[0],
        email=row[1],
        full_name=row[2] or "",
        role=row[3],
        is_active=row[4],
        credits_balance=row[5],
    )


async def create_user(
    email: str,
    full_name: str,
    password: str,
    pool: ConnectionPool,
) -> User | None:
    def insert_user():
        with pool.connection() as connection:
            return connection.execute(
                """
                INSERT INTO users (email, full_name, password_hash)
                VALUES (%s, %s, %s)
                ON CONFLICT (lower(email)) DO NOTHING
                RETURNING id::text, email, full_name, credits_balance
                """,
                (email, full_name, hash_password(password)),
            ).fetchone()

    row = await anyio.to_thread.run_sync(insert_user)

    if row is None:
        return None

    return User(
        id=row[0],
        email=row[1],
        full_name=row[2] or "",
        role="user",
        credits_balance=row[3],
    )


async def list_users(pool: ConnectionPool | None) -> list[User]:
    if pool is None:
        if not DEMO_AUTH_ENABLED:
            return []
        return [account.user for account in _DEMO_ACCOUNTS]

    def query_users():
        with pool.connection() as connection:
            return connection.execute(
                """
                SELECT u.id::text, u.email, u.full_name, r.code, u.is_active,
                       u.credits_balance
                FROM users AS u
                JOIN roles AS r ON r.id = u.role_id
                WHERE u.deleted_at IS NULL
                ORDER BY u.created_at DESC
                """
            ).fetchall()

    rows = await anyio.to_thread.run_sync(query_users)

    return [
        User(
            id=row[0],
            email=row[1],
            full_name=row[2] or "",
            role=row[3],
            is_active=row[4],
            credits_balance=row[5],
        )
        for row in rows
    ]


async def count_users(pool: ConnectionPool | None) -> int:
    if pool is None:
        return len(await list_users(pool))

    def query_count():
        with pool.connection() as connection:
            return connection.execute(
                "SELECT count(*) FROM users WHERE deleted_at IS NULL"
            ).fetchone()

    row = await anyio.to_thread.run_sync(query_count)
    return row[0]
