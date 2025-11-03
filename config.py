import os
from dotenv import load_dotenv

# Load .env from project root for local development
_ROOT = os.path.dirname(__file__)
load_dotenv(os.path.join(_ROOT, ".env"), override=False)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

    # Normalize deprecated scheme used by some providers
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Require a Postgres URL; do not fall back to SQLite
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is required and must be a pooled Postgres URL (e.g., from Neon/Supabase)."
        )
    if not (
        DATABASE_URL.startswith("postgresql://")
        or DATABASE_URL.startswith("postgresql+psycopg2://")
    ):
        raise RuntimeError("DATABASE_URL must start with 'postgresql://'")

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
