"""Mint new DOIs."""

import logging

from app.config import settings
from app.models.doi import DoiRealisation

log = logging.getLogger(__name__)


async def get_next_doi_suffix_id():
    """Get the next suffix ID in a prefix sequence."""
    suffix_ids = (
        await DoiRealisation.filter(
            prefix_id=settings.DOI_PREFIX,
            suffix_id__startswith=settings.DOI_SUFFIX_TAG,
        )
        .order_by("-suffix_id")
        .values_list("suffix_id", flat=True)
    )
    log.debug(f"Filtered suffix IDs: {suffix_ids}")

    numeric_ids = [int(suffix_id.split(".")[-1]) for suffix_id in suffix_ids]
    next_suffix_id = max(numeric_ids, default=0) + 1
    log.debug(f"Generating next DOI suffix in sequence: {next_suffix_id}")

    return next_suffix_id


async def create_db_doi(user_name: str, package_metadata: dict):
    """Create a new DOI in the DB."""
    log.debug("Creating new DB DOI entry start")

    next_id = await get_next_doi_suffix_id()
    if not (package_id := package_metadata.get("id", None)):
        return None
    if not (package_name := package_metadata.get("name", None)):
        return None

    log.debug(f"Creating new DOI for package id: {package_id}")

    new_doi = {
        "prefix_id": settings.DOI_PREFIX,
        "suffix_id": f"{settings.DOI_SUFFIX_TAG}{next_id}",
        "ckan_id": package_id,
        "ckan_name": package_name,
        "site_id": "doi-publishing-api",
        "tag_id": settings.DOI_SUFFIX_TAG,
        "ckan_user": user_name,
        "metadata": package_metadata,
        "metadata_format": "ckan",
        "ckan_entity": "package",
    }

    database_doi = await DoiRealisation.get_or_none(
        prefix_id=new_doi.prefix_id,
        suffix_id=new_doi.suffix_id,
    )

    if database_doi:
        log.debug("DOI already exists in DB, continuing to datacite logic")
    else:
        log.debug(f"Creating new DOI with params: {new_doi}")
        await DoiRealisation.create(**new_doi)

    return f"{new_doi.get('prefix_id', None)}/{new_doi.get('suffix_id', None)}"
