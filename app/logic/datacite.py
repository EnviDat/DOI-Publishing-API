"""Reserve and Publish DOIs to Datacite."""

import base64
import json

# Setup logging
import logging
from typing import TypedDict

import requests
from envidat.converters.datacite_converter import convert_datacite
from fastapi import HTTPException

# from pydantic import BaseModel
from app.config import settings

log = logging.getLogger(__name__)


class DoiSuccess(TypedDict):
    """DOI sucesss class."""

    status_code: int
    result: dict


class DoiErrors(TypedDict):
    """DOI errors class."""

    status_code: int
    errors: list[dict]


# TODO review and possibly remove dependencies in lib/envidat

# TODO review if Pydantic model appropriate for function arguments
# class DoiSuccess(BaseModel):
#     status_code: int
#     result: dict
#
#
# class DoiErrors(BaseModel):
#     status_code: int
#     errors: list[dict]#


def reserve_draft_doi_datacite(doi: str) -> DoiSuccess | DoiErrors:
    """Reserve a DOI identifer in "Draft" state with DataCite.

    For relevant DataCite documentation see:
    https://support.datacite.org/docs/api-create-dois#create-an-identifier-in-draft-state

    Args:
        doi (str): DOI assigned to EnviDat package in "doi" field

    Returns:
        DoiSuccess | DoiErrors: See TypedDict class definitions
    """
    log.info("Reserving draft DOI in datacite")

    # Extract variables from config needed to call DataCite API
    api_url = settings.DATACITE_API_URL
    client_id = settings.DATACITE_CLIENT_ID
    password = settings.DATACITE_PASSWORD
    timeout = settings.DATACITE_TIMEOUT

    # Assign DOI to payload in DataCite format
    payload = {"data": {"type": "dois", "attributes": {"doi": doi}}}

    # Convert payload to JSON and then send POST request to DataCite API
    payload_json = json.dumps(payload)
    headers = {"Content-Type": "application/vnd.api+json"}

    try:
        log.debug(f"Attempting POST to {api_url} with params: {payload_json}")
        response = requests.post(
            api_url,
            headers=headers,
            auth=(client_id, password),
            data=payload_json,
            timeout=timeout,
        )

    except requests.exceptions.ConnectTimeout as e:
        log.exception(e)
        return {"status_code": 408, "errors": [{"error": "Connection timed out"}]}

    except Exception as e:
        log.exception(e)
        return {
            "status_code": 500,
            "errors": [{"error": "Internal server error from DataCite"}],
        }

    # Return formatted DOI success or errors object
    return format_response(response)


# TODO review exception formatting, including from calls to helpers
def publish_datacite(package: dict) -> DoiSuccess | DoiErrors:
    """Publish/update an EnviDat record in DataCite.

       Converts EnviDat record to DataCite XML format before publication.

       For DataCite documentation of this process see:
       https://support.datacite.org/docs/api-create-dois#changing-the-doi-state
       https://support.datacite.org/docs/api-create-dois#provide-metadata-in-formats
       -other-than-json

    Args:
        package (dict): Individual EnviDat metadata entry record
                                    dictionary.

    Returns:
        DoiSuccess | DoiErrors: See TypedDict class definitions
    """
    # Extract variables from config needed to call DataCite API
    api_url = settings.DATACITE_API_URL
    client_id = settings.DATACITE_CLIENT_ID
    password = settings.DATACITE_PASSWORD
    site_url = settings.DATACITE_DATA_URL_PREFIX
    timeout = settings.DATACITE_TIMEOUT

    # Get doi and validate,
    # if doi not truthy or has invalid prefix then raises HTTPException
    doi = validate_doi(package)

    # Get metadata record URL
    name = package.get("name", package["id"])
    url = f"{site_url}/{name}"

    # Assign name_doi_map used in DataCite conversion

    # Assign conversion_error to return if conversion of package to
    # DataCite XML fails
    conversion_error = {
        "status_code": 500,
        "errors": [{"error": "Failed to convert package to DataCite format XML"}],
    }

    # Convert metadata record to DataCite formatted XML
    # and encode to base64 formatted string
    try:
        xml = convert_datacite(package)
        if xml:
            xml_encoded = xml_to_base64(xml)
            if not xml_encoded:
                return conversion_error
        else:
            return conversion_error
    except ValueError as e:
        log.error(e)
        return conversion_error

    # Create payload, set "event" to "publish"
    payload = {
        "data": {
            "id": doi,
            "type": "dois",
            "attributes": {
                "event": "publish",
                "doi": doi,
                "url": url,
                "xml": xml_encoded,
            },
        }
    }

    # Convert payload to JSON and then send PUT request to DataCite
    url = f"{api_url}/{doi}"
    payload_json = json.dumps(payload)
    headers = {"Content-Type": "application/vnd.api+json"}

    try:
        response = requests.put(
            url,
            headers=headers,
            auth=(client_id, password),
            data=payload_json,
            timeout=timeout,
        )

    except requests.exceptions.ConnectTimeout as e:
        log.exception(e)
        return {"status_code": 408, "errors": [{"error": "Connection timed out"}]}

    except Exception as e:
        log.exception(e)
        return {
            "status_code": 500,
            "errors": [{"error": "Internal server error from DataCite"}],
        }

    # Return formatted DOI success or errors object
    return format_response(response)


def format_response(response: requests.models.Response) -> DoiSuccess | DoiErrors:
    """Format the DataCite response.

    Checks if response has successful HTTP status code (200-299) and returns
    DataCite response object formatted in DoiSuccess or DoiErrors format.

    Args:
        response (requests.models.Response): Response from call to DataCite API

    Returns:
        DoiSuccess | DoiErrors: See TypedDict class definitions
    """
    response_json = response.json()

    successful_status_codes = range(200, 300)

    if response.status_code in successful_status_codes:
        doi = response_json.get("data").get("id")
        if doi:
            return {"status_code": response.status_code, "result": response_json}
        else:
            return {
                "status_code": 500,
                "errors": [
                    {
                        "parsing_error": "Failed to parse DOI from DataCite response",
                        "datacite_response": response_json,
                    }
                ],
            }
    else:
        return {
            "status_code": response.status_code,
            "errors": response_json.get("errors"),
        }


def validate_doi(package: dict):
    """Returns doi if it truthy and has EnviDat doi prefix.

    Else raises HTTPException

    Args:
        package (dict): CKAN EnviDat package dictionary

    Returns:
        doi (str): validated doi from input package
    """
    # Check if doi is truthy in package
    package_id = package.get("id")
    doi = package.get("doi")

    log.debug(f"Validating DOI. Package ID: {package_id}, DOI: {doi}")

    if not doi:
        log.error(f"Attempted publish, but no DOI exists for package ID: {package_id}")
        raise HTTPException(status_code=500, detail="Package does not have a doi")

    # Validate doi prefix
    doi_prefix = settings.DOI_PREFIX
    prefix = (doi.partition("/"))[0]
    if prefix != doi_prefix:
        log.debug(f"DOI prefix is invalid: {prefix}")
        raise HTTPException(status_code=403, detail="Invalid DOI prefix")

    return doi


def xml_to_base64(xml: str) -> str:
    """Converts XML formatted string to base64 formatted string.

       Returns string in base64 format (not bytes)

    Args:
        xml (str): String in XML format

    Returns:
        str: base64 formatted string conversion of input xml_str
    """
    if isinstance(xml, str):
        xml_bytes = xml.encode("utf-8")
        xml_encoded = base64.b64encode(xml_bytes)
        xml_str = xml_encoded.decode()
        return xml_str


def get_error_message(datacite_response: DoiSuccess | DoiErrors) -> str:
    """Returns error message string extracted from formatted DataCite response.

    In case of errors returns default error string.

    Args:
         datacite_response (DoiSuccess | DoiErrors): see TypedDict class definitions
    """
    try:
        errors = datacite_response.get("errors", {})
        return json.dumps(errors)
    except Exception as e:
        log.exception(f"ERROR getting error message from DataCite response:  {e}")
        return "Unknown error"
