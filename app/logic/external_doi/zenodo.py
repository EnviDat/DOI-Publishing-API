"""Retrieve and convert Zenodo DOI metadata to EnviDat CKAN package format"""

import json
import requests


# TODO review error messages
def convert_zenodo_doi(
        doi: str, add_placeholders: bool = False
) -> dict:
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
        add_placeholders (bool): If true placeholder values are added for
                         required EnviDat package fields.
                         Default value is False.

    Returns:
        dict: Dictionary with metadata in EnviDat CKAN package
                or error dictionary
    """

    record_id = get_zenodo_record_id(doi)
    if not record_id:
        return {
            "status_code": 400,
            "message": f"The following DOI was not found: {doi}",
            "error": "Cannot extract record ID from input Zenodo DOI"
        }

    with open("app/config/zenodo.json", "r") as zenodo_config:
        config = json.load(zenodo_config)

    records_url = config.get("externalApi", {}).get("zenodoRecords")
    if not record_id:
        # TODO email admin config error
        return {
            "status_code": 500,
            "message": "Cannot process DOI. Please contact EnviDat team.",
            "error": "Cannot not get externalApi.zenodoRecords from config"
        }

    api_url = f"{records_url}/{record_id}"
    timeout = config.get("timeout", 3)

    response = requests.get(api_url, timeout=timeout)

    # TODO start dev here
    # TODO handle non 200 status code on response from zenodo
    # TODO convert Zenodo response to EnviDat format

    if response.status_code != 200:
        return {
            "status_code": response.status_code,
            "message": f"The following DOI was not found: {doi}",
            "error": response.json()
        }

    envidat_record = convert_zenodo_to_envidat(response.json())

    return envidat_record


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


def convert_zenodo_to_envidat(
        metadata: dict, add_placeholders: bool = False
) -> dict:
    """
    Convert Zenodo record dictionary to EnviDat CKAN package format.

    If add_placeholders true then add default values from config.
    Values added are required by EnviDat CKAN to create a new package.

     Args:
        metadata (dict): Response data object from Zenodo API call
        add_placeholders (bool): If true placeholder values are added for
                         required EnviDat package fields.
                         Default value is False.
    """

    # Assign dictionary to contain values converted from Zenodo
    # to EnviDat CKAN package format
    pkg = {}

    data = metadata.get("metadata")

    # TODO determine if DOI should be validated

    # TODO start dev here
    # TODO convert creators to EnviDat authors format
    creators = data.get("creators")

    return creators


