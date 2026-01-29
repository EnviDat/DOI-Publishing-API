"""Forest3D API Router."""

import asyncio
from typing import Annotated

from app.logic.forest3d import publish_forest3d_to_datacite, \
    prepare_dataset_for_envidat, doi_exists_in_dc, format_doi, is_valid_envidat_name
from fastapi import APIRouter, Depends, HTTPException, Query
import aiohttp

from app.auth import get_admin, get_datacite_session
from app.config import config_app

import logging
log = logging.getLogger(__name__)


router = APIRouter(
    prefix="/forest3d",
    tags=["forest3d"],
    dependencies=[Depends(get_admin)]
)


@router.get(
    "/publish-bulk-datacite"
)
async def publish_bulk_forest3d(
        is_update: Annotated[
            bool,
            Query(
                alias="is-update",
                description="If true updates datasets already published in DataCite."
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
        ] = False
):
    """Publish several Forest3D datasets with Datacite.

    Optionally if 'is-update' query parameter is true then updates existing Forest3D
    datasets in DataCite.

    The metadata for Forest3D datasets are read from an external online JSON file.

    Only authorized admin can use this endpoint.
    """
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
    async with get_datacite_session() as session:
        async def process_dataset(dataset):

            name = dataset.get("name", "")
            if not is_valid_envidat_name(name):
                return {
                    "error": f"Invalid 'name' value '{name}': must be alphanumeric "
                             f"only and not contain spaces, hyphens are allowed",
                    "dataset": dataset
                }

            doi = dataset.get("doi")
            if not doi:
                return {"error": "Missing 'doi field", "dataset": dataset}

            if is_test_doi:
                doi = format_doi(doi)

            if not is_update:
                if await doi_exists_in_dc(session, doi):
                    return {
                        "doi": doi,
                        "status": "DOI already registered with DataCite"
                    }

            formatted_dataset = prepare_dataset_for_envidat(dataset, is_test_doi)
            result = await publish_forest3d_to_datacite(session, formatted_dataset)
            return result

        results = await asyncio.gather(*(process_dataset(i) for i in forest3d_datasets))

    return results
