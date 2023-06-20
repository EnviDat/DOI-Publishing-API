"""Constants used by envidat_doi module."""

from enum import Enum


class ExternalPlatform(str, Enum):
    """External platforms class."""

    ZENODO = "zenodo"


EXTERNAL_PLATFORM_NAMES = {"zenodo": ExternalPlatform.ZENODO}

EXTERNAL_PLATFORM_PREFIXES = {"10.5281": ExternalPlatform.ZENODO}
