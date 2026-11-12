from fastapi import Request
from psycopg_pool import ConnectionPool

from app.core.config import DATABASE_URL


def create_connection_pool() -> ConnectionPool | None:
    if DATABASE_URL is None:
        return None

    return ConnectionPool(
        conninfo=DATABASE_URL,
        min_size=1,
        max_size=10,
        open=False,
        timeout=30,
    )


def get_connection_pool(request: Request) -> ConnectionPool | None:
    return request.app.state.db_pool