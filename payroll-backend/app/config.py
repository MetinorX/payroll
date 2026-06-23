from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/postgres"
    test_database_url: str = "sqlite+aiosqlite:///./test.db"
    secret_key: str = "super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    debug: bool = True
    log_level: str = "INFO"
    rate_limit_enabled: bool = True
    rate_limit_max_attempts: int = 5
    rate_limit_window_seconds: int = 60
    db_pool_size: int = 5
    db_max_overflow: int = 2

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
