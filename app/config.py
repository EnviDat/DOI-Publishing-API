"""Config file for Pydantic and FastAPI, using environment variables."""

import logging
from functools import lru_cache
from typing import Any, Optional, Union

from pydantic import (
    AnyHttpUrl,
    Extra,
    FieldValidationInfo,
    PostgresDsn,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Main settings class, defining environment variables."""

    APP_NAME: str
    SECRET_KEY: str
    LOG_LEVEL: str = "INFO"
    PROXY_PREFIX: Optional[str] = ""

    DEBUG_USER_ID: Optional[str] = None
    DEBUG_USER_EMAIL: Optional[str] = None
    DEBUG: bool = False

    @field_validator("DEBUG", mode="before")
    @classmethod
    def get_debug_user_details(cls, v: str, info: FieldValidationInfo) -> Any:
        """If DEBUG var set, ensure debug user details are set."""
        if not v:
            return v
        if not info.data.get("DEBUG_USER_ID"):
            log.error(info.data.get("DEBUG_USER_ID"))
            raise ValueError("DEBUG_USER_ID is not present in the environment")
        if not info.data.get("DEBUG_USER_EMAIL"):
            raise ValueError("DEBUG_USER_EMAIL is not present in the environment")
        return v

    CKAN_API_URL: AnyHttpUrl = "https://www.envidat.ch"

    @field_validator("CKAN_API_URL", mode="before")
    @classmethod
    def convert_ckan_api_to_string(cls, v: AnyHttpUrl) -> str:
        """Convert CKAN_API_URL to string."""
        if isinstance(v, AnyHttpUrl):
            return str(v)
        elif isinstance(v, str):
            return v
        raise ValueError(v)

    DATACITE_API_URL: AnyHttpUrl
    DATACITE_CLIENT_ID: str
    DATACITE_PASSWORD: str
    DATACITE_TIMEOUT: int | float = 3
    DATACITE_RETRIES: int = 1
    DATACITE_SLEEP_TIME: int = 3
    DATACITE_DATA_URL_PREFIX: str = "https://www.envidat.ch/#/metadata"
    DOI_PREFIX: str
    DOI_SUFFIX_TAG: Optional[str] = ""

    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
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

    @field_validator("DB_URI", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: FieldValidationInfo) -> Any:
        """Build Postgres connection from environment variables."""
        if isinstance(v, str):
            return v
        pg_url = PostgresDsn.build(
            scheme="postgres",
            username=info.data.get("DB_USER"),
            password=info.data.get("DB_PASS"),
            host=info.data.get("DB_HOST"),
            path=f"/{info.data.get('DB_NAME') or ''}",
        )
        # FIXME temp workaround for tortoise
        # MultiHostUrl' object has no attribute 'get'
        return str(pg_url)

    EMAIL_ENDPOINT: AnyHttpUrl
    EMAIL_FROM: str

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", extra=Extra.allow
    )


@lru_cache
def get_settings():
    """Cache settings, for calling in multiple modules."""
    # Dotenv loaded here to allow debugging files directly
    from app.utils import load_dotenv_if_not_docker

    load_dotenv_if_not_docker(force=True)
    _settings = Settings()
    log.info("Loaded settings from cache")
    return _settings


settings = get_settings()
