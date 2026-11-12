import unittest

from fastapi.testclient import TestClient

from app.core.rate_limit import ALL_LIMITERS
from app.main import app


class ApiBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        # No lifespan: run without PostgreSQL, whatever .env says.
        app.state.db_pool = None
        for limiter in ALL_LIMITERS:
            limiter.reset()
        self.client = TestClient(app)

    def test_protected_api_returns_json_401_instead_of_redirect(self) -> None:
        for method, path in [
            ("get", "/api/admin/summary"),
            ("get", "/api/admin/users"),
            ("post", "/api/video/generate"),
            ("get", "/api/generations/5f202bb9-11e7-48f5-914b-1e287e09509e/assets/"
                    "e8532246-6902-4551-87e8-6b3f8074d345"),
        ]:
            with self.subTest(path=path):
                response = getattr(self.client, method)(
                    path,
                    follow_redirects=False,
                    **({"json": {"prompt": "x"}} if method == "post" else {}),
                )
                self.assertEqual(response.status_code, 401)
                self.assertIn("detail", response.json())

    def test_unknown_api_path_is_404_json_not_the_spa(self) -> None:
        for method in ("get", "post"):
            with self.subTest(method=method):
                response = getattr(self.client, method)("/api/does-not-exist")
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.headers["content-type"], "application/json")

    def test_public_config_exposes_server_side_credit_prices(self) -> None:
        prices = self.client.get("/api/config").json()["credit_prices"]
        self.assertEqual(set(prices), {"image_per_image", "video_per_second", "website"})
        self.assertTrue(all(isinstance(value, int) and value > 0 for value in prices.values()))

    def test_repeated_failed_logins_are_rate_limited(self) -> None:
        payload = {"email": "nobody@example.com", "password": "wrong-password"}
        statuses = [
            self.client.post("/api/auth/login", json=payload).status_code for _ in range(6)
        ]
        self.assertEqual(statuses[:5], [401] * 5)
        self.assertEqual(statuses[5], 429)

    def test_security_headers_are_set(self) -> None:
        response = self.client.get("/api/config")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")


if __name__ == "__main__":
    unittest.main()
