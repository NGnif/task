import os
import tempfile
from dotenv import load_dotenv

# Load .env from project root for local development
_ROOT = os.path.dirname(__file__)
load_dotenv(os.path.join(_ROOT, ".env"), override=False)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    # Default to a writable temp sqlite path in serverless environments
    _default_sqlite = os.path.join(tempfile.gettempdir(), "app.db")
    DATABASE_URL = os.environ.get("DATABASE_URL", _default_sqlite)

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    if "://" in DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_URL}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
