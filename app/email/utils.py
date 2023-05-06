from logging import getLogger

import requests

from app.config import settings
from app.email.constants import PublishAction, PublishSubject, PublishTemplateName
from app.utils import load_dotenv_if_in_debug_mode

log = getLogger(__name__)


# TODO improve exception handling with more specific exceptions
# TODO write docstring
def get_user_show(user_id: str) -> dict | None:

    # Extract environment variables from config needed to call CKAN
    load_dotenv_if_in_debug_mode()

    api_host = settings.API_HOST
    api_user_show = settings.API_USER_SHOW
    api_token = settings.API_TOKEN

    if any(key is None for key in [api_host, api_user_show, api_token]):
        msg = "Not all required variables are set: API_HOST, API_USER_SHOW, API_TOKEN"
        log.error(msg)
        raise KeyError(msg) from None

    # Extract and return user's name and email from user account data
    # returned from CKAN API call
    try:
        # Request user's account from CKAN
        api_url = f"{api_host}{api_user_show}{user_id}"
        headers = {"Authorization": api_token}
        response = requests.get(api_url, headers=headers)

        # Handle unexpected response status_code
        # Expected successful response status_code: 200
        if response.status_code != 200:
            log.error(
                f"ERROR call to CKAN returned unexpected response status_code: "
                f"{response.status_code}"
            )
            log.error(f"ERROR message from CKAN: {response.json()}")
            return None

        # Return user's account information
        if response:
            data = response.json()
            return data["result"]

    except ConnectionError as e:
        log.error(e)
        return None

    except Exception as e:
        log.error(e)
        return None


# TODO write docstring
def get_dict_value(input_dict: dict, key: str):
    """Returns value from input dictionary.

    Default value is None.
    String values are stripped of whitespace.
    """
    value = input_dict.get(key, None)

    if type(value) == "str":
        return value.strip()

    return value


# TODO implement templates for all publish_action cases
# TODO write docstring
# Get subject and template that corresponds to publication_action
def get_publish_email_subject_template(publish_action):
    match publish_action:

        case PublishAction.REQUEST:
            subject = PublishSubject.REQUEST.value
            template_name = PublishTemplateName.REQUEST.value

        case PublishAction.APPROVE:
            subject = PublishSubject.APPROVE.value
            template_name = PublishTemplateName.REQUEST.value

        case PublishAction.DENY:
            subject = PublishSubject.DENY.value
            template_name = PublishTemplateName.REQUEST.value

        case PublishAction.FINISH:
            subject = PublishSubject.FINISH.value
            template_name = PublishTemplateName.REQUEST.value

        # TODO handle default case
        case _:
            # TODO log error
            return None, None

    return subject, template_name


# TODO write docstring
def has_none_kwarg(**kwargs):
    has_none = False

    for key, val in kwargs.items():
        if val is None:
            log.error(f"ERROR: email argument '{key}' is None, check logs")
            has_none = True

    return has_none
