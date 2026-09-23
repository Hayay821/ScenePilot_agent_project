import os
from dataclasses import dataclass
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("BOLDMAKER_HOST", "127.0.0.1")
    port: int = int(os.getenv("BOLDMAKER_PORT", "8010"))
    data_root: Path = Path(os.getenv("BOLDMAKER_DATA_ROOT", Path(__file__).parent / "data"))
    serve_frontend: bool = _env_bool("BOLDMAKER_SERVE_FRONTEND", True)
    cors_origins: str = os.getenv("BOLDMAKER_CORS_ORIGINS", "*")
    cloud_api_base: str = os.getenv("BOLDMAKER_CLOUD_API_BASE", "http://120.26.152.99:8000")
    cloud_timeout_seconds: float = float(os.getenv("BOLDMAKER_CLOUD_TIMEOUT_SECONDS", "10"))
    session_ttl_hours: int = int(os.getenv("BOLDMAKER_SESSION_TTL_HOURS", "168"))
    max_upload_mb: int = int(os.getenv("BOLDMAKER_MAX_UPLOAD_MB", "2048"))
    allow_uid_header: bool = _env_bool("BOLDMAKER_ALLOW_UID_HEADER", True)
    test_account: str = os.getenv("BOLDMAKER_TEST_ACCOUNT", "test")
    test_password: str = os.getenv("BOLDMAKER_TEST_PASSWORD", "test")
    test_uid: str = os.getenv("BOLDMAKER_TEST_UID", "test")


settings = Settings()
