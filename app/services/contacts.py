import anyio
from psycopg import Error as PsycopgError
from psycopg_pool import ConnectionPool, PoolTimeout


class ContactPersistenceError(Exception):
    pass


def _insert_contact_message(
    pool: ConnectionPool,
    name: str,
    email: str,
    subject: str,
    message: str,
) -> str:
    with pool.connection() as connection:
        row = connection.execute(
            """
            INSERT INTO contact_messages (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
            RETURNING id::text
            """,
            (name, email, subject, message),
        ).fetchone()

    if row is None:
        raise ContactPersistenceError("The contact message insert returned no id.")
    return row[0]


async def save_contact_message(
    pool: ConnectionPool,
    name: str,
    email: str,
    subject: str,
    message: str,
) -> str:
    try:
        return await anyio.to_thread.run_sync(
            _insert_contact_message,
            pool,
            name,
            email,
            subject,
            message,
        )
    except (PsycopgError, PoolTimeout) as error:
        raise ContactPersistenceError("Could not save the contact message.") from error
