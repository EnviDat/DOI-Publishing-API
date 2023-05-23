"""DOIs API Router."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from tortoise.contrib.fastapi import HTTPNotFoundError

from app.auth import verify_user
from app.models.dois import (
    DoiPrefixEditPydantic,
    DoiPrefixPydantic,
)

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dois",
    tags=["dois"],
)


class Status(BaseModel):
    """Helper class to display message from API after function run."""

    message: str


@router.get("", response_model=list[DoiPrefixPydantic])
async def get_all_dois():
    """Get all dois."""
    log.debug("Getting all dois")
    return await DoiPrefixPydantic.from_queryset(dois.all())


@router.get(
    "/{id}",
    response_model=DoiPrefixPydantic,
    responses={404: {"model": HTTPNotFoundError}},
)
async def get_dois(id: str, user: Depends[verify_user]):
    """Get specific dois."""
    log.debug(f"Getting dois ID {id}")

    # Determine if is an admin
    user.get("sysadmin", False)

    return await DoiPrefixPydantic.from_queryset_single(dois.get(id=id))


@router.post("", response_model=DoiPrefixInPydantic)
async def create_dois(dois: DoiPrefixInPydantic):
    """Create new dois in DB without Datacite."""
    log.debug(f"Creating new dois with params: {dois}")
    dois_obj = await dois.create(**dois.dict(exclude_unset=True))
    return await doisInPydantic.from_tortoise_orm(dois_obj)


@router.get("/draft", response_model=DoiPrefixPydantic)
async def create_dois(id: str):
    """Create new dois in DB and Datacite."""
    log.debug(f"Creating new draft doi for package id: {id}")
    # Logic for datacite here
    # Extract out params from datacite draft
    # if errors in datacite return
    # return JSONResponse(status_code=409)
    # Return the __str__ from model
    await dois.last()

    dois_obj = await dois.create(**dois.dict(exclude_unset=True))
    return await DoisInPydantic.from_tortoise_orm(dois_obj)


@router.put(
    "/update/{id}",
    response_model=DoiPrefixEditPydantic,
    responses={404: {"model": HTTPNotFoundError}},
)
async def update_dois(id: str, dois: DoiPrefixEditPydantic):
    """Update specific dois."""
    log.debug(f"Attempting to update dois ID {id} with params: {dois}")
    await dois.filter(id=id).update(**dois.dict(exclude_unset=True))
    return await DoiPrefixEditPydantic.from_queryset_single(dois.get(id=id))


@router.delete(
    "/{id}", response_model=Status, responses={404: {"model": HTTPNotFoundError}}
)
async def delete_dois(id: str):
    """Delete specific dois."""
    log.debug(f"Attempting to delete dois ID {id}")
    deleted_count = await dois.filter(id=id).delete()
    if not deleted_count:
        log.error(f"Failed deleting dois ID {id}. Does not exist ")
        raise HTTPException(status_code=404, detail=f"dois {id} not found")
    return Status(message=f"Deleted dois {id}")
