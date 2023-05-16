"""Config file for Pydantic and FastAPI, using environment variables."""

import logging
from functools import lru_cache
from typing import Any, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn, validator

log = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Main settings class, defining environment variables."""

    APP_NAME: str
    SECRET_KEY: str
    DEBUG: str = False
    LOG_LEVEL: str = "INFO"

    API_URL: str = "https://www.envidat.ch"
    API_TOKEN: str = None
    API_USER_SHOW: str = "/api/3/action/user_show"

    DATACITE_API_URL: str
    DATACITE_CLIENT_ID: str
    DATACITE_PASSWORD: str
    DOI_PREFIX: str

    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, list[str]]) -> Union[list[str], str]:
        """Build and validate CORS origins list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    DB_HOST: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    DB_URI: Optional[PostgresDsn] = None

    @validator("DB_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, Any]) -> Any:
        """Build Postgres connection from environment variables."""
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgres",
            user=values.get("DB_USER"),
            password=values.get("DB_PASS"),
            host=values.get("DB_HOST"),
            path=f"/{values.get('DB_NAME') or ''}",
        )

    class Config:
        """Pydantic settings config."""

        case_sensitive = True
        env_file = ".env"


@lru_cache
def get_settings():
    """Cache settings, for calling in multiple modules."""
    _settings = Settings()
    log.info("Loaded settings from cache")
    return _settings


settings = get_settings()
