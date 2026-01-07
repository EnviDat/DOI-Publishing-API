"""Logic and helpers for Forest3D router."""

import json

import aiohttp
import asyncio

from envidat_converters.logic.converter_logic.envidat_to_datacite import \
    EnviDatToDataCite

from app.config import config_app
from app.logic.datacite import xml_to_base64

import logging
log = logging.getLogger(__name__)


async def doi_exists(session: aiohttp.ClientSession, doi: str) -> bool:
    """Check if a DOI is already registered in the DataCite API."""
    async with session.get(f"{config_app.DATACITE_API_URL}/{doi}") as resp:
        if resp.status == 200:
            return True
        return False


def prepare_dataset_for_envidat(dataset):
    """
    Convert Forest3D dataset into EnviDat-like package format.
    Only stringifies fields EnviDat expects as JSON strings.
    """
    dataset_copy = dataset.copy()
    fields_to_stringify = ["author", "date", "funding", "maintainer", "publication",
                           "spatial"]

    for field in fields_to_stringify:
        if field in dataset_copy:
            val = dataset_copy[field]
            if isinstance(val, (dict, list)):
                dataset_copy[field] = json.dumps(val)
            elif isinstance(val, str):
                # normalize quotes in case single quotes are used
                try:
                    parsed = json.loads(val.replace("'", '"'))
                    dataset_copy[field] = json.dumps(parsed)
                except json.JSONDecodeError:
                    dataset_copy[field] = val.replace("'", '"')
            else:
                # convert numeric or boolean values to string
                dataset_copy[field] = str(val)

    # Convert numeric tag names/display_names to strings
    if "tags" in dataset_copy:
        for tag in dataset_copy["tags"]:
            for key in ["name", "display_name"]:
                if key in tag and not isinstance(tag[key], str):
                    tag[key] = str(tag[key])

    return dataset_copy


async def publish_forest3d_to_datacite(
        session: aiohttp.ClientSession,
        dataset: dict
):
    """Publish/update a Forest3D dataset in DataCite.

       Converts Forest3D record to DataCite XML format before publication.

       For DataCite documentation of this process see:
       https://support.datacite.org/docs/api-create-dois
    """
    api_url = config_app.DATACITE_API_URL
    site_url = config_app.DATACITE_DATA_URL_PREFIX
    timeout = config_app.DATACITE_TIMEOUT

    doi = dataset.get("doi")
    if not doi:
        return {
            "status_code": 422,
            "errors": [{"error": f"Dataset does not have a 'doi' field: {dataset}"}]
        }

    name = dataset.get("name")
    if not name:
        return {
            "status_code": 422,
            "errors": [{"error": f"Dataset does not have a 'name' field: {dataset}"}]
        }

    # TODO review
    # Get metadata record URL
    record_url = f"{site_url}/{name}?mode=forest3d"

    # Assign conversion_error to return if conversion of package to
    # DataCite XML fails
    conversion_error = {
        "status_code": 500,
        "errors": [
            {"error": "Failed to convert Forest3D dataset to DataCite format XML"}
        ],
    }

    # Convert Forest3D dataset to DataCite formatted XML
    # and encode to base64 formatted string
    try:
        if datacite_dataset := EnviDatToDataCite(dataset):
            xml_datacite_dataset = datacite_dataset.__str__()
            xml_encoded = xml_to_base64(xml_datacite_dataset)
            if not xml_encoded:
                return conversion_error
        else:
            return conversion_error
    except ValueError as e:
        log.error(e)
        return conversion_error

    payload = {
        "data": {
            "id": doi,
            "type": "dois",
            "attributes": {
                "event": "publish",
                "doi": doi,
                "url": record_url,
                "xml": xml_encoded,
            },
        }
    }

    # Convert payload to JSON and then send PUT request to DataCite to publish/update
    #   a record
    request_url = f"{api_url}/{doi}"
    payload_json = json.dumps(payload)
    headers = {"Content-Type": "application/vnd.api+json"}

    try:

        async with session.put(
                request_url,
                data=payload_json,
                headers=headers,
                timeout=timeout
        ) as resp:

            if resp.status == 200:
                return {
                    "status_code": resp.status,
                    "result": "DOI successfully published/updated"
                }
            else:
                try:
                    error_data = await resp.json()
                except aiohttp.ContentTypeError:
                    error_text = await resp.text()
                    error_data = {"error": error_text}
                return {
                    "status_code": resp.status,
                    "errors": [error_data]
                }

    except aiohttp.ClientConnectionError as e:
        log.exception(f"Connection error: {e}")
        return {"status_code": 503, "errors": [{"error": "Connection error"}]}

    except asyncio.TimeoutError as e:
        log.exception(f"Request timed out: {e}")
        return {"status_code": 408, "errors": [{"error": "Connection timed out"}]}

    except Exception as e:
        log.exception(f"Unexpected error: {e}")
        return {"status_code": 500,
                "errors": [{"error": "Unexpected error"}]}
