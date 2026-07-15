"""Forest3D API Router."""

import asyncio
from typing import Annotated
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Header, status

from app.auth import get_datacite_session
from app.config import config_app

import logging

from app.logic.http_utils import fetch_remote_json
from app.logic.publisher import process_datacite_dataset

log = logging.getLogger(__name__)


router = APIRouter(
    prefix="/forest3d",
    tags=["forest3d"],
)


@router.get("/datacite/publish")
async def publish_bulk_forest3d(
    is_update: Annotated[
        bool,
        Query(
            alias="is-update",
            description="If true updates Forest3D datasets already published in "
            "DataCite. "
            "The 'metadata_modified' date must be "
            "within the last 30 days.",
        ),
    ] = False,
    is_test_doi: Annotated[
        bool,
        Query(
            alias="is-test-doi",
            description="If true formats 'doi' value to be compatible with "
            "DataCite standards: everything after a ' ' (space) "
            "character is removed. Should only be used while testing "
            "publishing/updating DOIs with DataCite test account.",
        ),
    ] = False,
    forest3d_key: Annotated[
        str | None,
        Header(
            alias="forest3d-key",
            description="Header parameter that matches environment variable "
            "'FOREST3D_API_KEY'.",
        ),
    ] = None,
):
    """Bulk publish Forest3D datasets with Datacite.

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
    forest3d_datasets = await fetch_remote_json(forest3d_url)

    if not isinstance(forest3d_datasets, list):
        raise HTTPException(422, "Parsed JSON must be a list")

    # ---- Publish DOIs concurrently to DataCite
    today = date.today()

    async with get_datacite_session() as session:
        results = await asyncio.gather(
            *(
                process_datacite_dataset(
                    session,
                    record,
                    is_update,
                    is_test_doi,
                    today,
                    validate_name=True,
                    is_forest3d=True,
                )
                for record in forest3d_datasets
            )
        )

    return results
