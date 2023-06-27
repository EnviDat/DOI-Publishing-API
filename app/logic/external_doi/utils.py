"""Utils for envidat_doi module."""

from app.logic.external_doi.constants import (
    EXTERNAL_PLATFORM_NAMES,
    EXTERNAL_PLATFORM_PREFIXES,
    ConvertError,
    ConvertSuccess,
    ExternalPlatform,
)
from app.logic.external_doi.zenodo import convert_zenodo_doi
from app.logic.remote_ckan import ckan_current_package_list_with_resources


def get_doi_external_platform(doi: str) -> ExternalPlatform | None:
    """Return ExternalPlatform that most likely corresponds to input DOI string.

    If external platform not found then returns None.

    Args:
        doi (str): Input DOI string

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


def convert_doi(
    doi: str, owner_org: str, user: dict, add_placeholders: bool = False
) -> ConvertSuccess | ConvertError:
    """Tries to return metadata for input DOI and convert metadata to EnviDat
    CKAN package format.

    Calls supported external platforms. If DOI cannot be matched to external platform
    then returns error dictionary.

    Args:
        doi (str): Input DOI string
        owner_org (str): 'owner_org' assigned to user in EnviDat CKAN
        user (dict): CKAN user dictionary
        add_placeholders (bool): If true placeholder values are added for
                       required EnviDat package fields. Default value is False.
    """
    converters = [convert_zenodo_doi]

    for converter in converters:
        if converter is convert_zenodo_doi:
            record = convert_zenodo_doi(doi, owner_org, user, add_placeholders)
            if record.get("status_code") == 200:
                return record

    return {
        "status_code": 404,
        "message": f"The following DOI is not currently "
        f"supported for conversion: {doi}",
        "error": f"Cannot convert the DOI: {doi}",
    }
