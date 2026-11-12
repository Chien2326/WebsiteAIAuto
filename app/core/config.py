import os
from dotenv import load_dotenv


load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-only-change-this-session-secret")
DATABASE_URL = os.getenv("DATABASE_URL", "").strip() or None
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "").strip() or None
POLLINATIONS_IMAGE_MODEL = os.getenv(
    "POLLINATIONS_IMAGE_MODEL",
    "tongyi-mai/z-image-turbo",
).strip()
POLLINATIONS_VIDEO_MODEL = os.getenv(
    "POLLINATIONS_VIDEO_MODEL",
    "google/veo-3.1-fast",
).strip()
POLLINATIONS_TEXT_MODEL = os.getenv(
    "POLLINATIONS_TEXT_MODEL",
    "openai/gpt-5.4-nano",
).strip()
DEMO_AUTH_ENABLED = (
    os.getenv("DEMO_AUTH_ENABLED", "true" if APP_ENV != "production" else "false")
    .strip()
    .lower()
    == "true"
)
SESSION_HTTPS_ONLY = os.getenv(
    "SESSION_HTTPS_ONLY",
    "true" if APP_ENV == "production" else "false",
).strip().lower() == "true"

if APP_ENV == "production" and SESSION_SECRET == "dev-only-change-this-session-secret":
    raise RuntimeError("SESSION_SECRET must be configured when APP_ENV=production")

if APP_ENV == "production" and DEMO_AUTH_ENABLED:
    raise RuntimeError("DEMO_AUTH_ENABLED must be false when APP_ENV=production")

if APP_ENV == "production" and DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL must be configured when APP_ENV=production")