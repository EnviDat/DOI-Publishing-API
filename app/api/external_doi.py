"""Router used to convert DOIs and associated metadata from external platforms
into EnviDat CKAN package format.
"""

# Setup logging
import logging
from typing import Annotated

from fastapi import APIRouter, Query, Response, Security
from fastapi.security import APIKeyHeader

from app.auth import get_user
from app.logic.external_doi.constants import ExternalPlatform
from app.logic.external_doi.utils import get_doi_external_platform
from app.logic.external_doi.zenodo import convert_zenodo_doi

log = logging.getLogger(__name__)

# TODO test with production

# Setup external-doi router
router = APIRouter(prefix="/external-doi", tags=["external-doi"])

# Setup authorization header
authorization_header = APIKeyHeader(
    name="Authorization",
    description="ckan cookie for logged in user passed in authorization header",
)


# Test DOI 2635937
# TODO reivew responses, response arg
#  and response.status_code block
@router.get("/convert", name="Convert external DOI")
def convert_external_doi(
    doi: Annotated[
        str,
        Query(
            description="DOI from external platform",
            examples={
                "doi only": {"value": "10.5281/zenodo.5230562"},
                "doi with url": {"value": "https://doi.org/10.5281/zenodo.5230562"},
            },
        ),
    ],
    response: Response,
    authorization: str = Security(authorization_header),
    add_placeholders: Annotated[
        bool,
        Query(
            alias="add-placeholders",
            description="If true placeholder values are added for "
            "required EnviDat package fields",
        ),
    ] = False,
):
    """Convert DOI and associated metadata from external plaforms
    into EnviDat CKAN package formatted json.
    """
    # Authorize user, if user invalid then raises HTTPException
    user = get_user(authorization)

    # Get external platform name and call corresponding API,
    # then convert the DOI's metadata to EnviDat CKAN package format
    external_platform = get_doi_external_platform(doi)

    # TODO handle default in case external_platform is None (not matched),
    #  try calling all supported APIs
    # TODO set response status codes, use returned dicts from converters
    match external_platform:
        # TODO call ZenodoAPI
        case ExternalPlatform.ZENODO:
            result = convert_zenodo_doi(doi, user, add_placeholders)

        # TODO loop through different converters for default case
        case _:
            result = ""

    # response.status_code = result.get('status_code')
    return result
