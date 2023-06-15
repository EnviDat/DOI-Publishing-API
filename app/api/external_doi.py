"""
Router used to convert DOIs and associated metadata from external platforms
into EnviDat CKAN package format
"""

from typing import Annotated

from fastapi import APIRouter, Query, Security, Response
from fastapi.security import APIKeyHeader

from app.auth import authorize_user
from app.logic.external_doi.constants import ExternalPlatform
from app.logic.external_doi.utils import get_doi_external_platform

# Setup logging
import logging

log = logging.getLogger(__name__)

# TODO test with production
# TODO finalize authorization method (header vs. cookie)


# Setup external-doi router
router = APIRouter(prefix="/external-doi", tags=["external-doi"])

# Setup authorization header
authorization_header = APIKeyHeader(name='Authorization',
                                    description='ckan cookie for logged in '
                                                'user passed in authorization '
                                                'header')


# TODO potentially remove responses, response arg
#  and response.status_code block
@router.get(
    "/convert",
    name="Convert external DOI"
)
def convert_external_doi(
        doi: Annotated[str, Query(description="DOI from external platform",
                                  example="10.5281/zenodo.6514932")],
        user_id: Annotated[str, Query(alias="user-id",
                                      description="CKAN user id or name")],
        response: Response,
        authorization: str = Security(authorization_header)
):
    """
    Convert DOI and associated metadata from external plaforms
    into EnviDat CKAN package formatted json.
    """

    # Authorize user, if user invalid then raises HTTPException
    authorize_user(user_id, authorization)

    external_platform = get_doi_external_platform(doi)

    # TODO handle default in case external_platform is None or not matched,
    #  try calling supported APIs
    match external_platform:

        # TODO call ZenodoAPI
        case ExternalPlatform.ZENODO:
            pass

    return external_platform
