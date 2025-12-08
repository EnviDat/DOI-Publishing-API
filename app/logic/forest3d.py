"""Logic and helpers for Forest3D router."""

import aiohttp
from envidat_converters.logic.converter_logic.envidat_to_datacite import EnviDatToDataCite

from app.config import config_app
from app.logic.datacite import DoiSuccess, DoiErrors, xml_to_base64

import logging
log = logging.getLogger(__name__)


async def doi_exists(session: aiohttp.ClientSession, doi: str) -> bool:
    """Check if a DOI is already registered in the DataCite API."""
    async with session.get(f"{config_app.DATACITE_API_URL}/{doi}") as resp:
        if resp.status == 200:
            return True
        return False


async def publish_forest3d_to_datacite(
        session: aiohttp.ClientSession,
        dataset: dict
) -> DoiSuccess | DoiErrors:
    """Publish/update a Forest3D dataset in DataCite.

       Converts Forest3D record to DataCite XML format before publication.

       For DataCite documentation of this process see:
       https://support.datacite.org/docs/api-create-dois
    """
    # Extract variables from config needed to call DataCite API
    api_url = config_app.DATACITE_API_URL
    client_id = config_app.DATACITE_CLIENT_ID
    password = config_app.DATACITE_PASSWORD
    site_url = config_app.DATACITE_DATA_URL_PREFIX
    timeout = config_app.DATACITE_TIMEOUT

    name = dataset.get("name")
    if not name:
        return {
            "status_code": 408,
            "errors": [{"error": f"Dataset does not have a 'name' field: {dataset}"}]
        }

    # TODO review
    # Get metadata record URL
    url = f"{site_url}/{name}?mode=forest3d"

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
        # TODO resolve differences with input data and expected data from converter
        xml = EnviDatToDataCite(dataset)
        if xml:
            xml_to_str = xml.__str__()
            return xml_to_str
            xml_encoded = xml_to_base64(xml_to_str)
            if not xml_encoded:
                return conversion_error
        else:
            return conversion_error
    except ValueError as e:
        log.error(e)
        return conversion_error

    # # Create payload, set "event" to "publish"
    # payload = {
    #     "data": {
    #         "id": doi,
    #         "type": "dois",
    #         "attributes": {
    #             "event": "publish",
    #             "doi": doi,
    #             "url": url,
    #             "xml": xml_encoded,
    #         },
    #     }
    # }
    #
    # # Convert payload to JSON and then send PUT request to DataCite
    # url = f"{api_url}/{doi}"
    # payload_json = json.dumps(payload)
    # headers = {"Content-Type": "application/vnd.api+json"}
    #
    # try:
    #     response = requests.put(
    #         url,
    #         headers=headers,
    #         auth=(client_id, password),
    #         data=payload_json,
    #         timeout=timeout,
    #     )
    #
    # except requests.exceptions.ConnectTimeout as e:
    #     log.exception(e)
    #     return {"status_code": 408, "errors": [{"error": "Connection timed out"}]}
    #
    # except Exception as e:
    #     log.exception(e)
    #     return {
    #         "status_code": 500,
    #         "errors": [{"error": "Internal server error from DataCite"}],
    #     }
    #
    # # Return formatted DOI success or errors object
    # return format_response(response)
