"""Reserve and Publish DOIs to Datacite."""

from typing import TypedDict
from app.config import settings
import json
import requests


class DraftDoiSuccess(TypedDict):
    success: bool
    status_code: int
    result: dict


class DraftDoiErrors(TypedDict):
    success: bool
    status_code: int
    errors: list[dict]


def reserve_draft_doi_datacite(doi: str) -> DraftDoiSuccess | DraftDoiErrors:
    """Reserve a DOI identifer in "Draft" state with DataCite.

    For relevant DataCite documentation see:
    https://support.datacite.org/docs/api-create-dois#create-an-identifier-in-draft-state

    Args: doi (str): DOI assigned to EnviDat package in "doi" field

    Returns:
        DraftDoiSuccess | DraftDoiErrors: See TypedDict class definitions
    """

    # Extract variables from config needed to call DataCite API
    try:
        api_url = settings.DATACITE_API_URL
        client_id = settings.DATACITE_CLIENT_ID
        password = settings.DATACITE_PASSWORD
    except KeyError as e:
        return {
            "success": False,
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

    # Return DOI success or errors object
    if response.status_code == 201:
        reserved_doi = response.json().get('data').get('id')
        if reserved_doi:
            return {
                "success": True,
                "status_code": response.status_code,
                "result": response.json()
            }
        else:
            return {
                "success": False,
                "status_code": 500,
                "errors": [
                    {
                        "parsing_error": "Cannot parse reserved DOI from "
                                         "DataCite response ",
                        "datacite_response": response.json()
                    }
                ]
            }
    else:
        return {
            "success": False,
            "status_code": response.status_code,
            "errors": response.json().get('errors')
        }


# ********************** TESTS *****************************

# Tests: reserve_draft_doi_datacite()

# Invalid DOI
# test = reserve_draft_doi_datacite("beautiful-doi")

# Valid DOI
# test = reserve_draft_doi_datacite("10.16904/envidat.test12")
# print(test)
