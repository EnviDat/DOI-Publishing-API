"""Endpoints to trigger emails."""

import logging

from fastapi import APIRouter

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/mail",
    tags=["mail"],
)


@router.get("/request-approval")
async def get_all_dois():
    """Request approval to publish."""
    return


@router.get("/approve")
async def get_all_dois():
    """Request approval to publish."""
    return
