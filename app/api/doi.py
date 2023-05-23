"""DOIs API Router."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from tortoise.contrib.fastapi import HTTPNotFoundError

from app.config import settings
from app.logic.minter import get_next_doi_suffix_id
from app.models.doi import (
    DoiRealisation,
    DoiRealisationEditPydantic,
    DoiRealisationInPydantic,
    DoiRealisationPydantic,
)

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dois",
    tags=["dois"],
)


class Status(BaseModel):
    """Helper class to display message from API after function run."""

    message: str


@router.get("", response_model=list[DoiRealisationPydantic])
async def get_all_dois():
    """Get all dois."""
    log.debug("Getting all dois")
    return await DoiRealisationPydantic.from_queryset(DoiRealisation.all())


@router.get(
    "/{id}",
    response_model=DoiRealisationPydantic,
    responses={404: {"model": HTTPNotFoundError}},
)
async def get_doi_by_id(id: str):
    """Get specific doi."""
    log.debug(f"Getting doi ID {id}")
    return await DoiRealisationPydantic.from_queryset_single(
        DoiRealisation.get(doi_pk=id)
    )


@router.get(
    "/{prefix}/{suffix}",
    response_model=DoiRealisationPydantic,
    responses={404: {"model": HTTPNotFoundError}},
)
async def get_doi_by_prefix_suffix(prefix: str, suffix: str):
    """Get specific doi by prefix/suffix combo."""
    log.debug(f"Getting doi {prefix}/{suffix}")
    return await DoiRealisationPydantic.from_queryset_single(
        DoiRealisation.get(prefix_id=prefix, suffix_id=suffix)
    )


@router.post("", response_model=DoiRealisationInPydantic)
async def create_doi_db_only(doi: DoiRealisationInPydantic):
    """Create new doi."""
    log.debug(f"Creating new DOI with params: {doi}")

    doi_exists = await DoiRealisation.get_or_none(
        prefix_id=settings.DOI_PREFIX,
        suffix_id=doi.suffix_id,
    )

    if doi_exists:
        HTTPException(status_code=409, detail=f"DOI already exists: {doi}")

    doi_obj = await DoiRealisation.create(**doi.dict(exclude_unset=True))
    return await DoiRealisationInPydantic.from_tortoise_orm(doi_obj)


@router.delete(
    "/{id}", response_model=Status, responses={404: {"model": HTTPNotFoundError}}
)
async def delete_doi(id: str):
    """Delete specific doi."""
    log.debug(f"Attempting to delete doi ID {id}")
    deleted_count = await DoiRealisation.filter(doi_pk=id).delete()
    if not deleted_count:
        log.error(f"Failed deleting doi ID {id}. Does not exist ")
        raise HTTPException(status_code=404, detail=f"doi {id} not found")
    return Status(message=f"Deleted doi {id}")


@router.post("/draft", response_model=DoiRealisationPydantic)
async def create_doi_draft(package_id: str):
    """Create new DOI in DB and Datacite using CKAN Package ID.

    POST is required to prevent conflict with GET /doi/{id}.
    """
    log.debug(f"Creating new draft doi for package id: {package_id}")

    next_id = await get_next_doi_suffix_id()

    new_doi = {
        "prefix_id": settings.DOI_PREFIX,
        "suffix_id": f"{settings.DOI_SUFFIX_TAG}{next_id}",
        "ckan_id": package_id,
        # "ckan_name": package.name,
        "site_id": "doi-publishing-api",
        "tag_id": "envidat.",
        # "ckan_user": user.name,
        # "metadata": datacite_draft_func(),
        "metadata_format": "ckan",
        "ckan_entity": "package",
    }

    doi_exists = await DoiRealisation.get_or_none(
        prefix_id=new_doi.prefix_id,
        suffix_id=new_doi.suffix_id,
    )

    if doi_exists:
        log.debug("DOI database already exists, continuing to datacite logic")
    else:
        log.debug(f"Creating new DOI with params: {new_doi}")
        await DoiRealisation.create(**new_doi)

    # # Call Datacite draft handler datacite.py
    # if datacite_error:
    #     HTTPException(
    #         status_code=409,
    #         detail=f"Error with datacite draft creation: {datacite_error}"
    #     )

    # return await DoiRealisationInPydantic.from_tortoise_orm(dois_obj)


@router.put(
    "/update/{id}",
    response_model=DoiRealisationEditPydantic,
    responses={404: {"model": HTTPNotFoundError}},
)
async def update_doi(package_id: str, doi: DoiRealisationEditPydantic):
    """Update specific DOI in DB and Datacite for CKAN Package ID."""
    log.debug(f"Attempting to update doi ID {id} with params: {doi}")
    await DoiRealisation.filter(doi_pk=id).update(**doi.dict(exclude_unset=True))

    # # Call Datacite update handler datacite.py
    # if datacite_error:
    #     HTTPException(
    #         status_code=409,
    #         detail=f"Error with datacite update: {datacite_error}"
    #     )

    return await DoiRealisationEditPydantic.from_queryset_single(
        DoiRealisation.get(doi_pk=id)
    )
