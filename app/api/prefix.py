"""DOI Prefix API Router."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_admin
from app.models.doi import (
    DoiPrefix,
    DoiPrefixEditPydantic,
    DoiPrefixInPydantic,
    DoiPrefixPydantic,
)

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/prefix",
    tags=["doi_prefix"],
    dependencies=[Depends(get_admin)],
)


class Status(BaseModel):
    """Helper class to display message from API after function run."""

    message: str


@router.get("", response_model=list[DoiPrefixPydantic])
async def get_all_doi_prefixes():
    """Get all doi prefixes."""
    log.debug("Getting all doi prefixes")
    return await DoiPrefixPydantic.from_queryset(DoiPrefix.all())


@router.get(
    "/{id}",
    response_model=DoiPrefixPydantic,
)
async def get_doi_prefix(id: str):
    """Get specific doi prefix."""
    log.debug(f"Getting doi prefix ID {id}")
    return await DoiPrefixPydantic.from_queryset_single(DoiPrefix.get(prefix_pk=id))


@router.post("", response_model=DoiPrefixInPydantic)
async def create_doi_prefix(doi_prefix: DoiPrefixInPydantic):
    """Create new doi prefix."""
    log.debug(f"Creating new doi prefix with params: {doi_prefix}")
    dois_obj = await DoiPrefix.create(**doi_prefix.dict(exclude_unset=True))
    return await DoiPrefixInPydantic.from_tortoise_orm(dois_obj)


@router.put(
    "/{id}",
    response_model=DoiPrefixEditPydantic,
)
async def update_species(id: int, doi_prefix: DoiPrefixEditPydantic):
    """Update specific doi prefix."""
    log.debug(f"Attempting to update DOI prefix ID {id} with params: {doi_prefix}")
    await DoiPrefix.filter(prefix_pk=id).update(**doi_prefix.dict(exclude_unset=True))
    return await DoiPrefixEditPydantic.from_queryset_single(DoiPrefix.get(prefix_pk=id))


@router.delete(
    "/{id}", response_model=Status,
)
async def delete_doi_prefix(id: str):
    """Delete specific doi prefix."""
    log.debug(f"Attempting to delete doi prefix ID {id}")
    deleted_count = await DoiPrefix.filter(prefix_pk=id).delete()
    if not deleted_count:
        log.error(f"Failed deleting doi prefix ID {id}. Does not exist ")
        raise HTTPException(status_code=404, detail=f"doi prefix {id} not found")
    return Status(message=f"Deleted doi prefix {id}")
