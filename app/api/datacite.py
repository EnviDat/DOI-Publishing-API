"""DataCite API Router."""

import logging

from fastapi import APIRouter, Depends, Header, Request
from typing import Annotated

from app.auth import get_user
from app.logic.datacite import get_package

log = logging.getLogger(__name__)

# TODO improve Swagger documentation of endpoints (title, description,
#  query parameters etc.)

# TODO implement authorization
# TODO remove dependencies if unused
router = APIRouter(prefix="/datacite", tags=["datacite"]
                   # dependencies=[Depends(get_user)]
                   )


# TODO make header auth work in Swagger
# TODO implement error handling if auth not valid
@router.get("/draft")
def get_draft_doi(user: str,
                  package: str,
                  authorization: Annotated[str | None, Header()] = None):
    """Reserve draft DOI in DataCite."""

    # Authorize user
    auth = get_user(user, authorization)

    # TODO test getting package
    # Get package
    package = get_package(package, authorization)

    return auth
