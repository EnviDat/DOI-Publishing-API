"""Retrieve and convert Zenodo DOI metadata to EnviDat CKAN package format"""

import json
import requests
import datetime


# TODO review error messages
def convert_zenodo_doi(
        doi: str,
        user_id: str,
        add_placeholders: bool = False
) -> dict:
    """
    Return metadata for input doi and convert metadata to EnviDat
    CKAN package format.

    Note: Converts data that exists in Zenodo metadata record
    By default does not provide default placeholders values for
    EnviDat CKAN package required/optional fields.
    If add_placeholders is True adds default placeholder values.

    If Zenodo doi metadata cannot be retrieved or conversion fails then
    returns error dictionary.

    Args:
        doi (str): Input doi string
        user_id (str): CKAN user id or name
        add_placeholders (bool): If true placeholder values are added for
                       required EnviDat package fields. Default value is False.

    Returns:
        dict: Dictionary with metadata in EnviDat CKAN package
                or error dictionary
    """

    record_id = get_zenodo_record_id(doi)
    if not record_id:
        return {
            "status_code": 400,
            "message": f"The following DOI was not found: {doi}",
            "error": "Cannot extract record ID from input Zenodo DOI"
        }

    with open("app/config/zenodo.json", "r") as zenodo_config:
        config = json.load(zenodo_config)

    records_url = config.get("externalApi", {}).get("zenodoRecords")
    if not records_url:
        # TODO email admin config error
        return {
            "status_code": 500,
            "message": "Cannot process DOI. Please contact EnviDat team.",
            "error": "Cannot not get externalApi.zenodoRecords from config"
        }

    api_url = f"{records_url}/{record_id}"
    timeout = config.get("timeout", 3)

    response = requests.get(api_url, timeout=timeout)

    # TODO start dev here
    # TODO handle non 200 status code on response from zenodo
    # TODO convert Zenodo response to EnviDat format

    if response.status_code != 200:
        return {
            "status_code": response.status_code,
            "message": f"The following DOI was not found: {doi}",
            "error": response.json()
        }

    envidat_record = convert_zenodo_to_envidat(
        response.json(),
        user_id,
        add_placeholders
    )

    return envidat_record


def get_zenodo_record_id(doi: str) -> str | None:
    """
    Return record ID extracted from Zenodo Doi.
    If extraction fails return None.

    Example DOI: "10.5281/zenodo.5230562"
    Example returns record ID: "5230562"

    Args:
        doi (str): Input doi string

    Returns:
        str | None: String with record ID or None

    """
    period_index = doi.rfind(".")

    if period_index == -1:
        return None

    record_id = doi[period_index + 1:]

    if not record_id:
        return None

    return record_id


# TODO add placeholder values for required fields if add_placeholders true
# TODO test creating CKAN package empty metadata
#  and dict returned from add_placeholders true
# TODO add try/except handling
def convert_zenodo_to_envidat(
        metadata: dict,
        user_id: str,
        add_placeholders: bool = False
) -> dict:
    """
    Convert Zenodo record dictionary to EnviDat CKAN package format.

    If add_placeholders true then add default values from config.
    Values added are required by EnviDat CKAN to create a new package.

     Args:
        metadata (dict): Response data object from Zenodo API call
        user_id (str): CKAN user id or name
        add_placeholders (bool): If true placeholder values are added for
                       required EnviDat package fields. Default value is False.
    """

    # Assign dictionary to contain values converted from Zenodo
    # to EnviDat CKAN package format
    pkg = {}

    data = metadata.get("metadata", {})

    # TODO determine if DOI should be validated

    creators = data.get("creators", [])
    authors = get_authors(creators, add_placeholders)
    if authors:
        pkg.update({"author": json.dumps(authors, ensure_ascii=False)})

    pkg.update({"creator_user_id": user_id})

    publication_date = data.get("publication_date", "")
    date = get_date(publication_date, add_placeholders)
    if date:
        pkg.update({"date": json.dumps(date)})

    # TODO start dev here, assign doi

    return pkg


def get_authors(creators: list, add_placeholders: bool = False) -> list:
    """
    Returns authors in EnviDat format

    Args:
        creators (dict): creators list in Zenodo record
        add_placeholders (bool): If true placeholder values are added for
                     required EnviDat package fields. Default value is False.
    """
    authors = []

    # Add empty object to creators to handle no creators
    # and add_placholders is true
    if add_placeholders and not creators:
        creators = [{}]

    for creator in creators:

        author = {}

        creator_names = creator.get("name", "")
        if "," in creator_names:
            names = creator_names.partition(",")
            author.update({
                "given_name": names[2].strip(),
                "name": names[0].strip()
            })
        elif " " in creator_names:
            names = creator_names.partition(" ")
            author.update({
                "given_name": names[0].strip(),
                "name": names[2].strip()
            })
        # TODO finalize placeholder name
        elif add_placeholders:
            author.update({"name": "UNKNOWN"})

        affiliation = creator.get("affiliation", "")
        # TODO finalize placeholder affiliation
        if add_placeholders and not affiliation:
            author.update({"affiliation": "UNKNOWN"})
        else:
            author.update({"affiliation": affiliation.strip()})

        identifier = creator.get("orcid", "")
        if identifier:
            author.update({"identifier": identifier.strip()})

        authors.append(author)

    return authors


def get_date(publication_date: str, add_placeholders: bool = False) -> list:
    """
    Returns dates in Envidat format

     Args:
        publication_date (str) : publication_date string in Zenodo record
        add_placeholders (bool): If true placeholder values are added for
                     required EnviDat package fields. Default value is False.
    """
    dates = []

    # TODO finalize placeholder date and date_type
    if add_placeholders and not publication_date:
        date_today = datetime.date.today()
        date_str = date_today.strftime("%Y-%m-%d")
        date = {
            "date": date_str,
            "date_type": "created"
        }
        dates.append(date)

    elif publication_date:
        date = {
            "date": publication_date,
            "date_type": "created"
        }
        dates.append(date)

    return dates

# TODO remove tests
# TEST
# test = get_authors([{}], True)
# # test = get_authors([{}], True)
# # test = get_authors([{}])
# print(test)
#
# test = convert_zenodo_to_envidat({}, '123', True)
# # test = convert_zenodo_to_envidat({}, '123')
# print(test)

# test = get_date("")
# print(test)
