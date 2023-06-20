"""Utils for envidat_doi module."""

from app.logic.external_doi.constants import (
    EXTERNAL_PLATFORM_NAMES,
    EXTERNAL_PLATFORM_PREFIXES,
    ExternalPlatform,
)


def get_doi_external_platform(doi: str) -> ExternalPlatform | None:
    """Return ExternalPlatform that most likely corresponds to input doi string.

    If external platform not found then returns None.

    Args:
        doi (str): Input doi string

    Returns:
        ExternalPlatform | None
    """
    # Search by names for doi that corresponds to supported external platform
    for key, value in EXTERNAL_PLATFORM_NAMES.items():
        if key in doi:
            return value

    # Search by DOI prefixes for doi that corresponds to
    # supported external platforms
    for key, value in EXTERNAL_PLATFORM_PREFIXES.items():
        if key in doi:
            return value

    return None
