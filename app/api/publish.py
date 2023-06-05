# TODO review, extract code needed, and remove module

import logging
from pathlib import Path

from envidat.api.v1 import get_envidat_record
from envidat.doi.datacite_publisher import publish_datacite
from fastapi import APIRouter, Response
from fastapi.templating import Jinja2Templates
from fastapi_mail import MessageType

from app.email.constants import PublishAction
from app.email.send_email import send_email_async
from app.email.utils import (
    get_dict_value,
    get_publish_email_subject_template,
    get_user_show,
    has_none_kwarg,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/publish", tags=["publish"])


# TODO implement authentication, likely with JWT tokens
# TODO check if AttributeError is best way to handle unknown errors
# TODO check if 500 is best default error status code
# TODO investigate how to add schema to API documentation on /docs
# TODO write doc string
# TODO test triggering all errors
@router.get("/datacite", tags=["publish"])
def publish_record_to_datacite(
    name: str, response: Response, is_update: bool = False, cookie=None
):
    # Get EnviDat record from CKAN API call, pass cookie if it is truthy
    try:
        if cookie:
            record = get_envidat_record(name, cookie=cookie)
        else:
            record = get_envidat_record(name)

        # Handle HTTP errors from CKAN API call (default status_code is 500)
        status_code = record.get("status_code", 500)
        if status_code != 200:
            response.status_code = status_code
            return {
                "error": record.get(
                    "result",
                    "Failed to extract record as JSON " "from CKAN " "API, check logs",
                )
            }
    except AttributeError as e:
        log.error(e)
        response.status_code = 500
        return {
            "error": "Failed to extract record as JSON from CKAN API, " "check logs"
        }

    # Publish package to DataCite and return DOI
    try:
        # Extract package from record result
        package = record.get("result")

        # If package and is_update is True then update existing DataCite record
        if package and is_update:
            dc_response = publish_datacite(package, is_update=is_update)
        # Else if package then publish package to DataCite
        elif package:
            dc_response = publish_datacite(package)
        else:
            response.status_code = 500
            return {"error": "Failed to extract 'result' from record"}

        # Handle dc_response not truthy
        if not dc_response:
            response.status_code = 500
            return {
                "error": "Failed to publish EnviDat record to DataCite, "
                "check logs for errors"
            }

        # Assign response status_code (default status_code is 500)
        # Expected successful response status_code: 201
        dc_status_code = dc_response.get("status_code", 500)
        response.status_code = dc_status_code

        # Handle HTTP errors from publishing to DataCite
        if dc_status_code != 201:
            return {"error": dc_response.get("result", "Internal Server Error")}

        # TODO implement notification email
        # Else send notification email and return published DOI
        return {"doi": dc_response.get("result")}

    except AttributeError as e:
        log.error(e)
        response.status_code = 500
        return {
            "error": "Failed to publish EnviDat record to DataCite, "
            "check logs for errors"
        }


# TODO change package_name argument to package_id
#  (test using package name as well) as
#  this will be used to get package name and maintainer email
# TODO make an email sender function that uses background tasks
# TODO try to find corresponding template and match (otherwise send error),
#  then send email
# TODO check if templates should be HTML or plain text
# TODO change return value
# TODO implement try/exception error handling
# TODO write docstring
@router.get("/email/{publish_action}")
async def send_email_publish_async(
    publish_action: PublishAction,
    user_id: str,
    package_name: str,
    admin_email: str = "envidat@wsl.ch",
    subtype: MessageType = MessageType.plain,
):
    # Get subject and template_name needed to send email
    subject, template_name = get_publish_email_subject_template(publish_action)

    # TODO replace with get_response_json(), extract "result" key
    #  from returned value
    # TODO start dev here
    # Get user's account information from CKAN API
    user = get_user_show(user_id)

    # Check if user is truthy
    if not user:
        return None

    # Get arguments needed to send email from user's account
    user_name = get_dict_value(user, "fullname")
    user_email = get_dict_value(user, "email")

    # TODO get maintainer_email
    # TODO check if maintainer_email should be validated
    # TODO check if package_name should be validated,
    #  (hyphens between names and no white space)
    # TODO START DEV here
    # Get EnviDat record from CKAN API
    record = get_envidat_record(package_name)

    # Handle HTTP errors from CKAN API call (default status_code is 500)
    status_code = record.get("status_code", 500)
    if status_code != 200:
        return None

    # Extract package from record result
    record.get("result")

    # Validate arguments used to send email are not None
    email_kwargs = {
        "subject": subject,
        "template_name": template_name,
        "user_name": user_name,
        "user_email": user_email,
    }

    has_none = has_none_kwarg(**email_kwargs)

    # Return None if at least one email argument is None
    if has_none:
        return None

    # TODO review formatting of subject (i.e. including colon)
    # Format subject
    subject = f"{subject}: {package_name}"

    # TODO possibly use EmailStr annotation to help validate email addresses
    # TODO make sure there are no duplicate email addresses in recipients list
    # TODO START DEV here
    recipients = [user_email, admin_email]

    # Load and render template used for email body
    templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
    template = templates.get_template(template_name)
    template_variables = {
        "admin_email": admin_email,
        "user_name": user_name,
        "user_email": user_email,
        "package": package_name,
    }
    body = template.render(**template_variables)

    await send_email_async(subject, recipients, body, subtype)

    return "Success"
