"""Forest3D API Router."""

import asyncio
from typing import Annotated
from datetime import date

from app.logic.forest3d import publish_forest3d_to_datacite, \
    prepare_dataset_for_envidat, doi_exists_in_dc, format_doi, is_valid_envidat_name, \
    ends_in_digit
from fastapi import APIRouter, HTTPException, Query, Header, status
import aiohttp

from app.auth import get_datacite_session
from app.config import config_app

import logging
log = logging.getLogger(__name__)


router = APIRouter(
    prefix="/forest3d",
    tags=["forest3d"],
)


@router.get(
    "/publish-bulk-datacite"
)
async def publish_bulk_forest3d(
        is_update: Annotated[
            bool,
            Query(
                alias="is-update",
                description="If true updates datasets already published in DataCite. "
                            "The 'metadata_modified' date must be "
                            "within the last 30 days."
            )
        ] = False,
        is_test_doi: Annotated[
            bool,
            Query(
                alias="is-test-doi",
                description="If true formats 'doi' value to be compatible with "
                            "DataCite standards: everything after a ' ' (space) "
                            "character is removed."
            )
        ] = False,
        forest3d_key: Annotated[
            str | None,
            Header(
                alias="forest3d-key",
                description="Header parameter that matches environment variable "
                            "'FOREST3D_API_KEY'."
            )
        ] = None
):
    """Publish several Forest3D datasets with Datacite.

    The metadata for Forest3D datasets are read from an external online JSON file that
    is set in the environment variable 'FOREST3D_URL'.

    Requires 'forest3d-key' header parameter that matches environment variable
    'FOREST3D_API_KEY'.

    'doi' values must end with a digit to be considered valid.

    Optionally if 'is-update' query parameter is true then updates existing Forest3D
    datasets in DataCite (if the 'metadata_modified' date is within the last 30 days.)
    """
    # ---- Validate header key
    if not forest3d_key or forest3d_key != config_app.FOREST3D_API_KEY:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing API key")

    # ---- Load input Forest3D JSON
    forest3d_url = config_app.FOREST3D_URL

    async with aiohttp.ClientSession() as public_session:

        async with public_session.get(forest3d_url) as resp:
            if resp.status != 200:
                raise HTTPException(resp.status, "Could not download JSON")
            try:
                forest3d_datasets = await resp.json()
            except Exception:
                raise HTTPException(422, "Remote JSON is invalid")

    if not isinstance(forest3d_datasets, list):
        raise HTTPException(422,
                            "Remote JSON must be a list of dictionaries")


    # ---- Publish DOIs concurrently to DataCite
    today = date.today()

    async with get_datacite_session() as session:
        async def process_dataset(dataset):

            doi = dataset.get("doi")
            if not doi:
                return {"error": "Missing 'doi field", "dataset": dataset}

            name = dataset.get("name", "")
            if not is_valid_envidat_name(name):
                return {
                    "error": f"Invalid 'name' value '{name}': must be alphanumeric "
                             f"only and not contain spaces, hyphens are allowed",
                    "doi": doi,
                    "name": name
                }

            if is_test_doi:
                doi = format_doi(doi)

            if not ends_in_digit(doi):
                return {
                    "error": f"'doi' value '{doi}' does not end with a digit",
                    "doi": doi,
                    "name": name
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
                        "name": name
                    }
            else:
                if await doi_exists_in_dc(session, doi):
                    return {
                        "doi": doi,
                        "status": "DOI already registered with DataCite",
                        "name": name
                    }

            formatted_dataset = prepare_dataset_for_envidat(dataset, is_test_doi)
            result = await publish_forest3d_to_datacite(session, formatted_dataset)
            return result

        results = await asyncio.gather(*(process_dataset(i) for i in forest3d_datasets))

    return results
