"""Send emails via mailer API."""

import logging

import requests

from app.config import config_app
from app.utils import fix_url_double_slash

log = logging.getLogger(__name__)


async def datacite_failed_email(
    package_id: str, user_name: str, user_email: str, error_msg: str
):
    """Inform the admin that a DOI task failed."""
    params = {
        "from": config_app.EMAIL_FROM,
        "to": config_app.EMAIL_FROM,
        "params": {
            "user_name": user_name,
            "user_email": user_email,
            "package_title": package_id,
            "package_url_prefix": config_app.DATACITE_DATA_URL_PREFIX,
            "error_msg": error_msg,
            "site_url": config_app.CKAN_API_URL,
        },
    }
    log.debug(f"Sending DOI task failure email to admin {config_app.EMAIL_FROM}")
    url = f"{config_app.EMAIL_ENDPOINT}/templates/datacite-task-failed/json"
    log.debug(f"Email URL: {url}")
    r = requests.post(
        fix_url_double_slash(url),
        headers={"Content-Type": "application/json"},
        json=params,
    )
    log.debug(f"Email API response: {r.status_code}")


async def request_approval_email(
    package_id: str,
    user_name: str,
    user_email: str,
    is_update: bool = False,
):
    """Send an email to the admin requesting publish approval."""
    params = {
        "from": config_app.EMAIL_FROM,
        "to": config_app.EMAIL_FROM,
        "params": {
            "user_name": user_name,
            "user_email": user_email,
            "package_title": package_id,
            "package_url_prefix": config_app.DATACITE_DATA_URL_PREFIX,
            "is_update": is_update,
            "site_url": config_app.CKAN_API_URL,
        },
    }
    log.debug(f"Sending DOI approval email to admin {config_app.EMAIL_FROM}")
    url = f"{config_app.EMAIL_ENDPOINT}/templates/datacite-request/json"
    log.debug(f"Email URL: {url}")
    r = requests.post(
        fix_url_double_slash(url),
        headers={"Content-Type": "application/json"},
        json=params,
    )
    log.debug(f"Email API response: {r.status_code}")


async def approval_granted_email(package_id: str, user_name: str, emails: list[str]):
    """Inform the multiple users that publishing has been approved."""
    params = {
        "from": config_app.EMAIL_FROM,
        "to": emails,
        "params": {
            "user_name": user_name,
            "package_title": package_id,
            "package_url_prefix": config_app.DATACITE_DATA_URL_PREFIX,
            "site_url": config_app.CKAN_API_URL,
        },
    }
    log.debug(f"Sending DOI approval granted email to {emails}")
    url = f"{config_app.EMAIL_ENDPOINT}/templates/datacite-published/json"
    log.debug(f"Email URL: {url}")
    r = requests.post(
        fix_url_double_slash(url),
        headers={"Content-Type": "application/json"},
        json=params,
    )
    log.debug(f"Email API response: {r.status_code}")
