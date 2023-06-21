"""Send emails via mailer API."""

import logging

import requests

from app.config import settings

log = logging.getLogger(__name__)


async def draft_failed_email(
    package_id: str, user_name: str, user_email: str, error_msg: str
):
    """Inform the admin that the draft DOI creation failed."""
    params = {
        "from": settings.EMAIL_FROM,
        "to": settings.EMAIL_FROM,
        "params": {
            "user_name": user_name,
            "user_email": user_email,
            "package_title": package_id,
            "package_url_prefix": settings.DATACITE_DATA_URL_PREFIX,
            "error_msg": error_msg,
            "site_url": settings.CKAN_API_URL,
        },
    }
    r = requests.post(
        f"{settings.EMAIL_ENDPOINT}/templates/datacite-draft-failed/json",
        headers={"Content-Type": "application/json"},
        json=params,
    )
    log.debug(f"Email API response: {r.status_code}")


async def request_approval_email(
    package_id: str,
    user_name: str,
    user_email: str,
    approval_url: str,
    is_update: bool = False,
):
    """Send an email to the admin requesting publish approval."""
    params = {
        "from": settings.EMAIL_FROM,
        "to": user_email,
        "params": {
            "user_name": user_name,
            "user_email": user_email,
            "package_title": package_id,
            "package_url_prefix": settings.DATACITE_DATA_URL_PREFIX,
            "approval_url": approval_url,
            "is_update": is_update,
            "site_url": settings.CKAN_API_URL,
        },
    }
    r = requests.post(
        f"{settings.EMAIL_ENDPOINT}/templates/datacite-request/json",
        headers={"Content-Type": "application/json"},
        json=params,
    )
    log.debug(f"Email API response: {r.status_code}")


async def approval_granted_email(package_id: str, user_name: str, user_email: str):
    """Inform the user that publishing has been approved."""
    params = {
        "from": settings.EMAIL_FROM,
        "to": user_email,
        "params": {
            "user_name": user_name,
            "package_title": package_id,
            "package_url_prefix": settings.DATACITE_DATA_URL_PREFIX,
            "site_url": settings.CKAN_API_URL,
        },
    }
    r = requests.post(
        f"{settings.EMAIL_ENDPOINT}/templates/datacite-published/json",
        headers={"Content-Type": "application/json"},
        json=params,
    )
    log.debug(f"Email API response: {r.status_code}")
