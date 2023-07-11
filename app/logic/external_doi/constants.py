"""Constants used by envidat_doi module."""

from enum import Enum
from typing import TypedDict


class ConvertSuccess(TypedDict):
    """External platform conversion success class."""

    status_code: int
    result: dict


class ConvertError(TypedDict):
    """External platform conversion error class."""

    status_code: int
    message: str
    error: str


class ExternalPlatform(str, Enum):
    """External platforms class."""

    ZENODO = "zenodo"


EXTERNAL_PLATFORM_NAMES = {"zenodo": ExternalPlatform.ZENODO}

EXTERNAL_PLATFORM_PREFIXES = {"10.5281": ExternalPlatform.ZENODO}
