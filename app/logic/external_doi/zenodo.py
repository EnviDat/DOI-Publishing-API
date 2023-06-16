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

    # Extract record_id
    record_id = get_zenodo_record_id(doi)
    if not record_id:
        return {
            "status_code": 400,
            "message": f"The following DOI was not found: {doi}",
            "error": "Cannot extract record ID from input Zenodo DOI"
        }

    # TODO review and remove unused key-value pairs
    # TODO write validator that makes sure
    #  all needed config keys and values exist
    # Get config
    with open("app/config/zenodo.json", "r") as zenodo_config:
        config = json.load(zenodo_config)

    # Assign records_url, return error if needed values not set in config
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

    # Get record from Zenodo API
    response = requests.get(api_url, timeout=timeout)

    # TODO convert Zenodo response to EnviDat format

    # Handle unsuccessful response
    if response.status_code != 200:
        return {
            "status_code": response.status_code,
            "message": f"The following DOI was not found: {doi}",
            "error": response.json()
        }

    # Convert Zenodo record to EnviDat format
    envidat_record = convert_zenodo_to_envidat(
        response.json(),
        user_id,
        config,
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
#  and dict returned if add_placeholders true
# TODO add try/except handling
def convert_zenodo_to_envidat(
        data: dict,
        user_id: str,
        config: dict,
        add_placeholders: bool = False
) -> dict:
    """
    Convert Zenodo record dictionary to EnviDat CKAN package format.

    If add_placeholders true then add default values from config.
    Values added are required by EnviDat CKAN to create a new package.

     Args:
        data (dict): Response data object from Zenodo API call
        user_id (str): CKAN user id or name
        config (dict): config dictionary created from config/zenodo.json
        add_placeholders (bool): If true placeholder values are added for
                       required EnviDat package fields. Default value is False.
    """

    # Assign dictionary to contain values converted from Zenodo
    # to EnviDat CKAN package format
    pkg = {}

    # TODO determine if DOI should be validated (should it be mandatory?)
    doi = data.get("doi")
    if doi:
        pkg.update({"doi": doi})

    # Extract "metadata" dictionary from input "data"
    # User metadata to extract and convert values to EnviDat package format
    metadata = data.get("metadata", {})

    # author
    creators = metadata.get("creators", [])
    authors = get_authors(creators, add_placeholders)
    if authors:
        pkg.update({"author": json.dumps(authors, ensure_ascii=False)})

    # creator_user_id
    pkg.update({"creator_user_id": user_id})

    # date
    publication_date = metadata.get("publication_date", "")
    date = get_date(publication_date, add_placeholders)
    if date:
        pkg.update({"date": json.dumps(date, ensure_ascii=False)})

    # funding
    grants = metadata.get("grants", [])
    funding = get_funding(grants, add_placeholders)
    if funding:
        pkg.update({"funding": json.dumps(funding, ensure_ascii=False)})

    # TODO determine if language should be assigned
    # language

    # license
    license_id = metadata.get("license", {}).get("id", "")
    license_data = get_license(license_id, config, add_placeholders)

    pkg.update({
        "license_id": license_data.get("license_id", "other-undefined"),
        "license_title": license_data.get("license_title", "other-undefined")
    })

    license_url = license_data.get("license_url")
    if license_url:
        pkg.update({"license_url": license_url})

    # TODO determine if maintainer should be user
    # TODO add placeholder values for maintainer because it is required
    # maintainer

    # TODO start dev here
    # name

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
        publication_date (str): publication_date string in Zenodo record
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


def get_funding(grants: list, add_placeholders: bool = False) -> list:
    """
    Returns funding in EnviDat format

    Args:
        grants (list): grants list in Zenodo record
        add_placeholders (bool): If true placeholder values are added for
                     required EnviDat package fields. Default value is False.
    """
    funding = []

    # TODO finalize placeholder funder
    if add_placeholders and not grants:
        funder = {"institution": "UNKNOWN"}
        funding.append(funder)

    for grant in grants:
        institution = grant.get("funder", {}).get("name")
        funding.append({"institution": institution})

    # Remove duplicate funders
    funding_no_duplicates = []
    for funder in funding:
        if funder not in funding_no_duplicates:
            funding_no_duplicates.append(funder)

    return funding_no_duplicates


def get_license(
        license_id: str,
        config: dict,
        add_placeholders: bool = False
) -> dict:
    """
    Returns license data in dictionary with EnviDat formatted keys

    Args:
        license_id (str): license_id string in Zenodo record
        config (dict):
        add_placeholders (bool): If true placeholder values are added for
                     required EnviDat package fields. Default value is False.
    """

    # Extract licenses from config
    envidat_licenses = config.get("envidatLicenses", {})

    # Assign other_undefined for placeholder values and unkown licenses
    other_undefined = envidat_licenses.get(
        "other-undefined", {
            "license_id": "other-undefined",
            "license_title": "Other (Specified in the description)"
        }
    )

    # TODO finalize placeholder license
    if add_placeholders and not license_id:
        return other_undefined

    match license_id:

        case "CC-BY-4.0":
            return envidat_licenses.get("cc-by", other_undefined)

        case "CC-BY-SA-4.0":
            return envidat_licenses.get("cc-by-sa", other_undefined)

        case "CC-BY-NC-4.0":
            return envidat_licenses.get("cc-by-nc", other_undefined)

        case _:
            return other_undefined


# TODO remove tests
# TESTS
# test = get_authors([{}], True)
# # test = get_authors([{}], True)
# # test = get_authors([{}])
#
# test = convert_zenodo_to_envidat({}, '123', True)
# # test = convert_zenodo_to_envidat({}, '123')

# test = get_date("")
# test = get_funding([], True)

# print(test)