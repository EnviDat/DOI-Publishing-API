"""Logic for validating and publishing individual datasets to DataCite."""

import json
import re
from datetime import date

import aiohttp
import asyncio

from envidat_converters.logic.converter_logic.envidat_to_datacite import (
    EnviDatToDataCite,
)

from app.config import config_app
from app.logic.datacite import xml_to_base64

import logging

log = logging.getLogger(__name__)


def is_valid_envidat_name(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9-]+", value))


async def doi_exists_in_dc(session: aiohttp.ClientSession, doi: str) -> bool:
    """Check if a DOI is already registered in the DataCite API."""
    async with session.get(f"{config_app.DATACITE_API_URL}/{doi}") as resp:
        if resp.status == 200:
            return True
        return False


def ends_in_digit(string: str) -> bool:
    """Return True if the string ends with a digit, else return False."""
    if string[-1:].isdigit():
        return True
    return False


def format_doi(doi: str) -> str:
    """Format a DOI for DataCite. Remove anything after a ' ' space character."""
    return doi.split()[0]


def prepare_dataset_for_envidat(dataset, is_test_doi=False):
    """
    Convert Forest3D dataset into EnviDat-like package format.
    Only stringifies fields EnviDat expects as JSON strings.
    """
    dataset_copy = dataset.copy()
    fields_to_stringify = [
        "author",
        "date",
        "funding",
        "maintainer",
        "publication",
        "spatial",
    ]

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
            if "display_name" not in tag and "name" in tag:
                tag["display_name"] = tag["name"]
            for key in ["name", "display_name"]:
                if key in tag and not isinstance(tag[key], str):
                    tag[key] = str(tag[key])

    if is_test_doi:
        dataset_copy["doi"] = format_doi(dataset_copy["doi"])

    return dataset_copy


def extract_tria_url(dataset: dict) -> str:
    """Extract TRIA dataset URL from a dataset.
    URL is assumed to be the "url" value in the first resource.

    Empty string returned if no "url" value can be extracted.
    """
    resources = dataset.get("resources", [])

    if not resources:
        return ""

    return resources[0].get("url", "")


async def publish_dataset_to_datacite(
    session: aiohttp.ClientSession,
    dataset: dict,
    is_forest3d: bool = False,
    is_tria: bool = False,
):
    """Publish/update a dataset in DataCite.

    Converts dataset to DataCite XML format before publication.

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
            "errors": [{"error": f"Dataset does not have a 'doi' field: {dataset}"}],
        }

    name = dataset.get("name")
    if not name:
        return {
            "status_code": 422,
            "errors": [{"error": f"Dataset does not have a 'name' field: {dataset}"}],
        }

    # Format metadata record URL
    if is_forest3d:
        record_url = f"{site_url}/{name}?mode=forest3d"
    elif is_tria:
        record_url = extract_tria_url(dataset)
        if not record_url:
            return {
                "status_code": 422,
                "errors": [
                    {
                        "error": f"TRIA dataset does not have a 'url' value "
                        f"that can be extracted: {dataset}"
                    }
                ],
            }
    else:
        record_url = f"{site_url}/{name}"

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
            timeout=timeout,
        ) as resp:
            if resp.status == 200 or resp.status == 201:
                return {
                    "status_code": resp.status,
                    "result": f"DOI '{doi}' successfully published/updated",
                }
            else:
                try:
                    error_data = await resp.json()
                except aiohttp.ContentTypeError:
                    error_text = await resp.text()
                    error_data = {"error": error_text}
                return {"status_code": resp.status, "errors": [error_data]}

    except aiohttp.ClientConnectionError as e:
        log.exception(f"Connection error: {e}")
        return {"status_code": 503, "errors": [{"error": "Connection error"}]}

    except asyncio.TimeoutError as e:
        log.exception(f"Request timed out: {e}")
        return {"status_code": 408, "errors": [{"error": "Connection timed out"}]}

    except Exception as e:
        log.exception(f"Unexpected error: {e}")
        return {"status_code": 500, "errors": [{"error": "Unexpected error"}]}


async def process_datacite_dataset(
    session: aiohttp.ClientSession,
    dataset: dict,
    is_update: bool,
    is_test_doi: bool,
    today: date,
    validate_name: bool = True,
    is_forest3d: bool = False,
    is_tria: bool = False,
) -> dict:
    """Validate a single dataset and publish/update it in DataCite."""
    doi = dataset.get("doi")
    if not doi:
        return {"error": "Missing 'doi field", "dataset": dataset}

    name = dataset.get("name", "")
    if validate_name and not is_valid_envidat_name(name):
        return {
            "error": f"Invalid 'name' value '{name}': must be alphanumeric "
            f"only and not contain spaces, hyphens are allowed",
            "doi": doi,
            "name": name,
        }

    if is_test_doi:
        doi = format_doi(doi)

    if not ends_in_digit(doi):
        return {
            "error": f"'doi' value '{doi}' does not end with a digit",
            "doi": doi,
            "name": name,
        }

    if is_update:
        metadata_modified = dataset.get("metadata_modified")
        mm_dt_obj = date.fromisoformat(metadata_modified)
        diff = today - mm_dt_obj
        if diff.days > 30 or diff.days < 0:
            return {
                "error": f"'metadata_modified' value '{metadata_modified}' is "
                f"not within the last 30 days",
                "doi": doi,
                "name": name,
            }
    else:
        if await doi_exists_in_dc(session, doi):
            return {
                "doi": doi,
                "status": "DOI already registered with DataCite",
                "name": name,
            }

    formatted_dataset = prepare_dataset_for_envidat(dataset, is_test_doi)
    return await publish_dataset_to_datacite(
        session, formatted_dataset, is_forest3d, is_tria
    )
