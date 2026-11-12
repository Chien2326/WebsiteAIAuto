import unittest
from contextlib import contextmanager
from typing import cast

from pydantic import ValidationError
from psycopg import OperationalError
from psycopg_pool import ConnectionPool

from app.api.contact import ContactMessagePayload
from app.services.contacts import ContactPersistenceError, save_contact_message


class FakeConnection:
    def __init__(self, fail_on_execute: bool = False) -> None:
        self.calls: list[tuple[str, tuple[object, ...] | None]] = []
        self.fail_on_execute = fail_on_execute

    def execute(
        self,
        query: str,
        params: tuple[object, ...] | None = None,
    ) -> "FakeConnection":
        self.calls.append((query, params))
        if self.fail_on_execute:
            raise OperationalError("database unavailable")
        return self

    def fetchone(self) -> tuple[str] | None:
        return ("message-id",)


class FakePool:
    def __init__(self, connection: FakeConnection) -> None:
        self._connection = connection

    @contextmanager
    def connection(self):
        yield self._connection


class ContactMessageTests(unittest.IsolatedAsyncioTestCase):
    def test_payload_trims_text_and_normalizes_email(self) -> None:
        payload = ContactMessagePayload(
            name="  Nguyễn Văn A ",
            email="  USER@Example.com ",
            subject=" Hỗ trợ ",
            message=" Xin chào ",
        )

        self.assertEqual(payload.name, "Nguyễn Văn A")
        self.assertEqual(payload.email, "user@example.com")
        self.assertEqual(payload.subject, "Hỗ trợ")
        self.assertEqual(payload.message, "Xin chào")

    def test_payload_rejects_blank_fields_and_invalid_email(self) -> None:
        with self.assertRaises(ValidationError):
            ContactMessagePayload(
                name=" ",
                email="invalid",
                subject="Chủ đề",
                message="Nội dung",
            )

    async def test_saves_contact_message(self) -> None:
        connection = FakeConnection()
        pool = cast(ConnectionPool, FakePool(connection))

        message_id = await save_contact_message(
            pool,
            "Nguyễn Văn A",
            "user@example.com",
            "Hỗ trợ",
            "Xin chào",
        )

        self.assertEqual(message_id, "message-id")
        self.assertIn("INSERT INTO contact_messages", connection.calls[0][0])
        self.assertEqual(
            connection.calls[0][1],
            ("Nguyễn Văn A", "user@example.com", "Hỗ trợ", "Xin chào"),
        )

    async def test_reports_database_errors(self) -> None:
        pool = cast(ConnectionPool, FakePool(FakeConnection(fail_on_execute=True)))

        with self.assertRaises(ContactPersistenceError):
            await save_contact_message(
                pool,
                "Nguyễn Văn A",
                "user@example.com",
                "Hỗ trợ",
                "Xin chào",
            )


if __name__ == "__main__":
    unittest.main()
