"""DataCite API Router"""

import logging

# from fastapi import APIRouter, Depends, Header
# from typing import Annotated
from fastapi import APIRouter, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from app.auth import get_user
from app.logic.datacite import get_package

log = logging.getLogger(__name__)

# TODO review if sign out working properly
# TODO review exception formatting
# TODO improve Swagger documentation of endpoints (title, description,
#  query parameters etc.)
# TODO implement authorization

# TODO remove dependencies if unused
router = APIRouter(prefix="/datacite", tags=["datacite"]
                   # dependencies=[Depends(get_user)]
                   )

# Setup authorization
authorization_header = APIKeyHeader(name='Authorization')


# TODO remove endpoint after testing and move to logic/datacite.py,
#  call from doi/create_doi_draft
# TODO test dataset without doi
# TODO improve docstring
@router.get("/draft")
def reserve_draft_doi(user: str,
                      package: str,
                      authorization: str = Security(authorization_header)):
    """
    Authenticate user, extract DOI from package, and reserve draft DOI in
    DataCite.
    """

    # Check if user has email property, this indicates the user is authorized
    auth = get_user(user, authorization)
    if not auth.get('email'):
        raise HTTPException(status_code=403, detail="User not authorized")

    # Get package and extract doi
    package = get_package(package, authorization)
    doi = package.get('doi')
    if not doi:
        raise HTTPException(status_code=500,
                            detail="Failed to parse doi from package")

    return package
