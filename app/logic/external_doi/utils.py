"""Utils for external_doi module."""

import csv
import json
from logging import getLogger

import requests
import xlsxwriter

from app.logic.external_doi.constants import (
    EXTERNAL_PLATFORM_NAMES,
    EXTERNAL_PLATFORM_PREFIXES,
    ConvertError,
    ConvertSuccess,
    ExternalPlatform,
)
from app.logic.external_doi.zenodo import convert_zenodo_doi, get_envidat_dois

log = getLogger(__name__)


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


def get_zenodo_dois(api_token: str, q: str, size: str = "10000") -> list[str] | None:
    """Return Zenodo DOIs extracted from records produced by search query.

    In case of errors returns None.
    NOTE: Only returns Zenodo DOIS that are NOT already in EnviDat CKAN instance.
    For Zenodo API documentation see: https://developers.zenodo.org/#records

    Args:
        api_token (str): api token for CKAN
        q (str): search query (using Elasticsearch query string syntax)
        size (str): number of results to return, default value is "10000"
    """
    # Get config
    config_path = "app/config/zenodo.json"
    try:
        with open(config_path, "r") as zenodo_config:
            config = json.load(zenodo_config)
    except FileNotFoundError as e:
        log.error(f"{e}")
        return None

    # Assign records_url
    records_url = config.get("zenodoAPI", {}).get(
        "zenodoRecords", "https://zenodo.org/api/records"
    )

    # Get URL used to call Zenodo API
    if q:
        api_url = f"{records_url}/?q={q}&size={size}"
    else:
        api_url = f"{records_url}/?size={size}"

    log.info(f"Calling Zenodo records API with the URL: {api_url}")

    # Get response from Zenodo API and extract DOIs
    try:
        response = requests.get(api_url, timeout=10)

        # Handle unsuccessful response
        if response.status_code != 200:
            log.error(
                f"Could not return Zenodo records " f"for the following URL: {api_url}"
            )
            return None

        # Extract records from Zenodo response
        response_json = response.json()
        records = response_json.get("hits", {}).get("hits", [])

        # Get EnviDat dois
        envidat_dois = get_envidat_dois(api_token)

        # Get list of Zenodo DOIs not already in EnviDat and that contain 'zenodo'
        dois = []
        for record in records:
            doi = record.get("doi")
            if doi:
                if doi in envidat_dois:
                    log.info(f"DOI already in EnviDat: {doi}")
                elif "zenodo" in doi:
                    dois.append(doi)

        return dois

    except Exception as e:
        log.error(f"{e}")
        return None


def write_dois_urls(
    dois: list[str], doi_prefix: str = None, output_path: str = "zenodo_dois.xls"
):
    """Writes list of DOIs to Excel file.
    Each DOI will be a clickable URL in the output Excel file.

    Args:
        dois (list): list of DOI strings
        doi_prefix (str): if doi_prefix included then prepends doi_prefix to each DOI
        output_path (str): path and name of output file, if specified then writes file
         there, else writes to root directory with default name "zenodo_dois.xlsx"
    """
    if doi_prefix:
        dois = [f"{doi_prefix}{doi}" for doi in dois]

    workbook = xlsxwriter.Workbook(output_path)
    worksheet = workbook.add_worksheet()

    row = 0
    column = 0

    for doi in dois:
        worksheet.write_url(row, column, doi)
        row += 1

    workbook.close()

    return


def read_dois_urls(input_path: str) -> list[str] | None:
    """Returns list of DOIs strings read from csv file.
    In case of errors returns None.

    Args:
        input_path (str): path and name of input file
    """
    try:
        with open(input_path, encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            dois = []

            for row in reader:
                dois.append(row[0])

        return dois

    except Exception as e:
        log.error(f"{e}")
        return None
