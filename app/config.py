"""Config file for Pydantic and FastAPI, using environment variables."""

import logging
from functools import lru_cache
from typing import Any, Optional, Union
from dotenv import dotenv_values

from pydantic import (
    AnyHttpUrl,
    PostgresDsn,
    field_validator,
    BaseModel,
    ValidationError,
    computed_field,
)
from pydantic_core import Url

log = logging.getLogger(__name__)


class ConfigAppModel(BaseModel):
    """Main settings class, defining environment variables."""

    __NAME__ = "doi-publishing-api"
    APP_VERSION: str
    ROOT_PATH: Optional[str] = ""
    DEBUG: bool = False
    CKAN_API_URL: AnyHttpUrl = "https://www.envidat.ch"

    @field_validator("CKAN_API_URL", mode="after")
    @classmethod
    def convert_ckan_api_to_string(cls, v: AnyHttpUrl) -> str:
        """Convert CKAN_API_URL to string."""
        if isinstance(v, Url):
            return str(v)
        if isinstance(v, str):
            return v
        raise ValueError(v)

    DATACITE_API_URL: AnyHttpUrl

    @field_validator("DATACITE_API_URL", mode="after")
    @classmethod
    def convert_datacite_api_to_string(cls, v: AnyHttpUrl) -> str:
        """Convert DATACITE_API_URL to string."""
        if isinstance(v, Url):
            return str(v)
        if isinstance(v, str):
            return v
        raise ValueError(v)

    DATACITE_CLIENT_ID: str
    DATACITE_PASSWORD: str
    DATACITE_TIMEOUT: int | float = 3
    DATACITE_RETRIES: int = 1
    DATACITE_SLEEP_TIME: int = 3
    DATACITE_DATA_URL_PREFIX: str = "https://www.envidat.ch/#/metadata"
    DOI_PREFIX: str
    DOI_SUFFIX_TAG: Optional[str] = ""

    BACKEND_CORS_ORIGINS: Union[str, list[AnyHttpUrl]] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, list[Url]]) -> Union[list[str], str]:
        """Build and validate CORS origins list."""
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, list):
            return [str(origin) for origin in v]
        raise ValueError(v)

    DB_HOST: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    @computed_field
    @property
    def DB_URI(cls) -> Any:
        """Build Postgres connection from environment variables."""
        pg_url = PostgresDsn.build(
            scheme="postgres",
            username=cls.DB_USER,
            password=cls.DB_PASS,
            host=cls.DB_HOST,
            path=cls.DB_NAME,
        )
        return str(pg_url)

    EMAIL_ENDPOINT: AnyHttpUrl
    EMAIL_FROM: str

@lru_cache
def get_config_app() -> ConfigAppModel | Exception:
    """Return config for app as object. Validate and cache .env environment variables.

    :return ConfigAppModel with valiated environment variables
        or Exception if validation fails
    """
    env_dict = dotenv_values(".env", verbose=True)

    try:
        _config = ConfigAppModel(**env_dict)
        return _config
    except ValidationError as e:
        raise Exception(f"Failed to validate environment variables, error(s): {e}")


config_app = get_config_app()


def get_log_level(debug: bool) -> str:
    """Return string used for log level of app.

    :param debug: Bool that indicates if debug mode is being used
    :return string: "DEBUG" or "WARNING"
    """
    if debug:
        return "DEBUG"
    return "WARNING"


log_level = get_log_level(config_app.DEBUG)
