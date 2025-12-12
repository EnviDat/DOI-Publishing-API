"""Forest3D API Router."""

import asyncio

from app.logic.forest3d import doi_exists, publish_forest3d_to_datacite, \
    prepare_dataset_for_envidat
from fastapi import APIRouter, Depends, HTTPException
import aiohttp

from app.auth import get_admin, get_datacite_session
from app.config import config_app

import logging
log = logging.getLogger(__name__)


router = APIRouter(prefix="/forest3d", tags=["forest3d"])


# TODO specify and return a data type
@router.get(
    "/publish-bulk-datacite"
)
async def publish_bulk_forest3d(
    # admin=Depends(get_admin),  # TODO start dev here, implement
):
    """Publish or update several Forest3D datasets with Datacite.

    The metadata for Forest3D datasets are read from an external online JSON file.

    Only authorized admin can use this endpoint.
    """
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

    # Publish DOIs concurrently to DataCite
    async with get_datacite_session() as session:
        async def process_dataset(dataset):
            doi = dataset.get("doi")
            if not doi:
                return {"error": "Missing 'doi field", "dataset": dataset}

            # TODO handle updating existing datasets, possibly as a query parameter
            #  boolean flag
            if await doi_exists(session, doi):
                return {"doi": doi, "status": "DOI already registered with DataCite"}

            formatted_dataset = prepare_dataset_for_envidat(dataset)
            result = await publish_forest3d_to_datacite(session, formatted_dataset)
            return result

        results = await asyncio.gather(*(process_dataset(i) for i in forest3d_datasets))

    return results
