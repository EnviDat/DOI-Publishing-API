"""Send emails via mailer API."""

import logging

import requests

from app.config import settings

log = logging.getLogger(__name__)


async def request_approval_email(package_id: str, user_email: str):
    """Send an email to the admin requesting publish approval."""
    # Logic to gather all package details

    params = {
        "from": settings.EMAIL_FROM,
        "to": settings.EMAIL_FROM,
        "params": {
            "user_name": user_email,
            "package_title": "",
            "approver": settings.EMAIL_FROM,
            "site_url": settings.API_URL,
        },
    }
    r = requests.post(
        settings.EMAIL_ENDPOINT,
        headers={"Content-Type": "application/json"},
        json=params,
    )
    log.debug(f"Email API response: {r.status_code}")


async def approval_granted_email(package_id: str, user_email: str):
    """Inform the user that publishing has been approved."""
    # Logic to gather all package details

    params = {
        "from": settings.EMAIL_FROM,
        "to": user_email,
        "params": {
            "package_title": "",
            "site_url": settings.API_URL,
        },
    }
    r = requests.post(
        settings.EMAIL_ENDPOINT,
        headers={"Content-Type": "application/json"},
        json=params,
    )
    log.debug(f"Email API response: {r.status_code}")
