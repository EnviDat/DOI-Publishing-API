"""TRIA API Router."""

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
    prefix="/tria",
    tags=["tria"],
)


@router.get("/datacite/publish")
async def publish_bulk_tria(
    is_update: Annotated[
        bool,
        Query(
            alias="is-update",
            description="If true updates TRIA datasets already published in "
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
    tria_key: Annotated[
        str | None,
        Header(
            alias="tria-key",
            description="Header parameter that matches environment variable "
            "'TRIA_API_KEY'.",
        ),
    ] = None,
):
    """Bulk publish TRIA datasets with Datacite.

    TRIA is a modern, flexible repository tailored to intra-annually resolved wood
    cell anatomical data and associated images developed and maintained by the WSL.

    To learn more about TRIA see: https://webapps.wsl.ch/tria

    The metadata for TRIA datasets are read from an external online JSON file that
    is set in the environment variable 'TRIA_URL'.

    Requires 'tria-key' header parameter that matches environment variable
    'TRIA_API_KEY'.

    'doi' values must end with a digit to be considered valid.

    Optionally if 'is-update' query parameter is true then updates existing TRIA
    datasets in DataCite (if the 'metadata_modified' date is within the last 30 days.)
    """
    # ---- Validate header key
    if not tria_key or tria_key != config_app.TRIA_API_KEY:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing API key")

    # ---- Load input TRIA JSON
    tria_url = config_app.TRIA_URL
    tria_datasets = await fetch_remote_json(tria_url)

    if not isinstance(tria_datasets, list):
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
                    validate_name=False,
                    is_tria=True,
                )
                for record in tria_datasets
            )
        )

    return results
