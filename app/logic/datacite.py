"""Reserve and Publish DOIs to Datacite."""

# TODO review and possibly remove dependencies in lib/envidat

from typing import TypedDict
import json
import requests
from fastapi import HTTPException

# from pydantic import BaseModel
from app.config import settings


# Setup logging
import logging
log = logging.getLogger(__name__)


class DoiSuccess(TypedDict):
    status_code: int
    result: dict


class DoiErrors(TypedDict):
    status_code: int
    errors: list[dict]


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

    # Extract variables from config needed to call DataCite API
    try:
        api_url = settings.DATACITE_API_URL
        client_id = settings.DATACITE_CLIENT_ID
        password = settings.DATACITE_PASSWORD
    except KeyError as e:
        return {
            "status_code": 500,
            "errors": [
                {"config_error": f"config setting '{e}' does not exist"}
            ]
        }

    # Assign DOI to payload in DataCite format
    payload = {
        "data": {
            "type": "dois",
            "attributes": {
                "doi": doi
            }
        }
    }

    # Convert payload to JSON and then send POST request to DataCite API
    payload_json = json.dumps(payload)
    headers = {"Content-Type": "application/vnd.api+json"}

    response = requests.post(api_url,
                             headers=headers,
                             auth=(client_id, password),
                             data=payload_json)

    # Return formatted DOI success or errors object
    # Expected status_code is 201
    return format_response(response, 201)


def format_response(response: requests.models.Response,
                    expected_status_code: int) -> DoiSuccess | DoiErrors:
    """
    Checks if response has expected HTTP status code and returns DataCite
        response object formatted in DoiSuccess or DoiErrors format.

    Args:
        response (requests.models.Response): Response from call to DataCite API
        expected_status_code (int): Expected HTTP status code

     Returns:
        DoiSuccess | DoiErrors: See TypedDict class definitions
    """
    response_json = response.json()

    if response.status_code == expected_status_code:
        doi = response_json.get('data').get('id')
        if doi:
            return {
                "status_code": response.status_code,
                "result": response_json
            }
        else:
            return {
                "status_code": 500,
                "errors": [
                    {
                        "parsing_error": "Failed to parse DOI from DataCite "
                                         "response",
                        "datacite_response": response_json
                    }
                ]
            }
    else:
        return {
            "status_code": response.status_code,
            "errors": response_json.get('errors')
        }


def validate_doi(package: dict):
    """
    Returns doi if it truthy and has EnviDat doi prefix.

    Args:
        package (dict): CKAN EnviDat package dictionary

    Returns:
        doi (str): validated doi from input package
    """

    # Check if doi is truthy in package
    doi = package.get('doi')
    if not doi:
        raise HTTPException(status_code=500,
                            detail="Package does not have a doi")

    # Validate doi prefix
    try:
        doi_prefix = settings.DOI_PREFIX
        prefix = (doi.partition('/'))[0]
        if prefix != doi_prefix:
            raise HTTPException(status_code=403, detail="Invalid DOI prefix")
    except KeyError as e:
        raise HTTPException(status_code=500,
                            detail=f"Config setting does not exist: {e}")

    return doi
