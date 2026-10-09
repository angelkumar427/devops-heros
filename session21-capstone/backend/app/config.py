"""Settings come from the environment (Docker Compose / Kubernetes ConfigMap + Secret)."""
import os
from urllib.parse import quote_plus


def database_url() -> str:
    # A full DATABASE_URL wins (local runs, tests). In Kubernetes the parts arrive separately
    # so the password can come from a Secret without being baked into a connection string.
    if url := os.environ.get("DATABASE_URL"):
        return url
    user = os.environ.get("POSTGRES_USER", "stockpilot")
    password = quote_plus(os.environ.get("POSTGRES_PASSWORD", ""))
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ.get("POSTGRES_DB", "stockpilot")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


APP_ENV = os.environ.get("APP_ENV", "dev")
APP_VERSION = os.environ.get("APP_VERSION", "dev")
CORS_ORIGINS = [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o]
