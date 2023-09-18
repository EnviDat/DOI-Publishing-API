"""Mint new DOIs."""

import json
import logging

from app.config import settings
from app.models.doi import DoiRealisation, DoiRealisationInPydantic

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
    ids_only = ", ".join(
        [suffix.lstrip(settings.DOI_SUFFIX_TAG) for suffix in suffix_ids]
    )
    log.debug(f"Filtered suffix IDs: {ids_only}")

    numeric_ids = [int(suffix_id.split(".")[-1]) for suffix_id in suffix_ids]
    log.debug(f"numeric_ids:  {numeric_ids}")

    next_suffix_id = max(numeric_ids, default=0) + 1
    log.debug(f"Generating next DOI suffix in sequence: {next_suffix_id}")

    return next_suffix_id


async def create_db_doi(user_name: str, package_metadata: dict):
    """Create a new DOI in the DB."""
    # Return DOI if exists already
    if existing_doi := package_metadata.get("doi", None):
        log.warning(f"DOI already exists for package: {existing_doi}")
        return existing_doi

    next_id = await get_next_doi_suffix_id()
    log.info(f"Creating new DOI in database: {next_id}")

    if not (package_id := package_metadata.get("id", None)):
        log.error("No id present in package metadata")
        return None
    if not (package_name := package_metadata.get("name", None)):
        log.error("No name present in package metadata")
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
        "metadata": json.dumps(package_metadata),
        "metadata_format": "ckan",
        "ckan_entity": "package",
    }

    log.debug("Checking database for existing DOI in database")
    database_doi = await DoiRealisation.get_or_none(
        prefix_id=new_doi.get("prefix_id"),
        suffix_id=new_doi.get("suffix_id"),
    )

    if database_doi:
        log.debug("DOI already exists in DB, continuing to datacite logic")
    else:
        log.debug(f"New DOI for validation: {new_doi}")
        try:
            validated_doi = DoiRealisationInPydantic(**new_doi)
            new_doi_dict = validated_doi.dict(exclude_unset=True)
            log.debug(
                f"Creating new database DOI with ID: {new_doi_dict.get('doi_pk')}"
            )
            await DoiRealisation.create(**new_doi_dict)
        except ValueError as e:
            log.error(f"DOI data failed validation: {e}")
            return None

    return (
        f"{new_doi_dict.get('prefix_id', None)}/{new_doi_dict.get('suffix_id', None)}"
    )
