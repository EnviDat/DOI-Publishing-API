"""Reserve and Publish DOIs to Datacite."""

# TODO review and possibly remove dependencies in lib/envidat

from typing import TypedDict, Annotated
import json
import requests

from ckanapi import RemoteCKAN, NotFound, NotAuthorized
from fastapi import HTTPException, Header
# from pydantic import BaseModel
from app.config import settings

import logging
log = logging.getLogger(__name__)


def get_package(package_id: str,
                authorization: Annotated[str | None, Header()] = None):
    """Return CKAN package"""
    if not authorization:
        log.error("No Authorization header present")
        raise HTTPException(status_code=401,
                            detail="No Authorization header present")

    try:
        ckan = RemoteCKAN(settings.API_URL, apikey=authorization)
        package = ckan.call_action("package_show", {'id': package_id})
    except NotFound as e:
        log.exception(e)
        raise HTTPException(status_code=404,
                            detail="Package not found")
    except NotAuthorized as e:
        log.exception(e)
        raise HTTPException(status_code=403,
                            detail="User not authorized to read package")

    return package


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


# ********************** TESTS *****************************

# Tests: reserve_draft_doi_datacite()

# Invalid DOI
# test = reserve_draft_doi_datacite("beautiful-doi")

# Valid DOI
# test = reserve_draft_doi_datacite("10.16904/envidat.test15")
# print(test)
