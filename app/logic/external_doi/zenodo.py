"""Retrieve and convert Zenodo DOI metadata to EnviDat CKAN package format"""


# TODO review error formatting
def convert_zenodo_doi(doi: str) -> dict:
    """
    Return metadata for input doi and convert metadata to EnviDat
    CKAN package format.

    Note: Only converts data that exists in Zenodo metadata record
    and does not provide default values for all
    EnviDat CKAN package required/optional fields.

    If Zenodo doi metadata cannot be retrieved or conversion fails then
    returns error dictionary.

    Args:
        doi (str): Input doi string

    Returns:
        dict: Dictionary with metadata in EnviDat CKAN package
                or error dictionary
    """

    record_id = get_zenodo_record_id(doi)

    if not record_id:
        return {
            "status_code": 400,
            "error": "Cannot extract record ID from input Zenodo DOI",
            "message": f"The following DOI was not found: {doi}"
        }

    # TODO start dev here

    return record_id


def get_zenodo_record_id(doi: str) -> str | None:
    """
    Return record ID extracted from Zenodo Doi.
    If extraction fails return None.

    Example DOI: "10.5281/zenodo.5230562"
    Example returns record ID: "5230562"

    Args:
        doi (str): Input doi string

    Returns:
        str | None: String with record ID or None

    """
    period_index = doi.rfind(".")

    if period_index == -1:
        return None

    record_id = doi[period_index + 1:]

    if not record_id:
        return None

    return record_id

