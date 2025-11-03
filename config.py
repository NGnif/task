import os
from dotenv import load_dotenv

# Load .env from project root for local development
_ROOT = os.path.dirname(__file__)
load_dotenv(os.path.join(_ROOT, ".env"), override=False)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        os.path.join(os.path.dirname(__file__), "app.db"),
    )

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    if "://" in DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_URL}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
