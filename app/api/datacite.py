"""DataCite API Router."""

import logging

from fastapi import APIRouter, Depends, Header, Request
from typing import Annotated

from app.auth import get_user


log = logging.getLogger(__name__)


# TODO implement authorization
# TODO remove dependencies if unused
router = APIRouter(prefix="/datacite", tags=["datacite"]
                   # dependencies=[Depends(get_user)]
                   )


# TODO make header auth work in Swagger
@router.get("")
async def test(authorization: Annotated[str | None, Header()] = None):
    """Get all dois."""
    auth = get_user(authorization)
    return auth
