"""Retrieve and convert Zenodo DOI metadata to EnviDat CKAN package format."""

from datetime import datetime, date
import json
import re

import requests


# TODO review error messages
def convert_zenodo_doi(doi: str, user: dict, add_placeholders: bool = False) -> dict:
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
        user (dict): CKAN user dictionary
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
            "error": "Cannot extract record ID from input Zenodo DOI",
        }

    # TODO review and remove unused key-value pairs
    # TODO write validator that makes sure
    #  all needed config keys and values exist
    # Get config
    config_path = "app/config/zenodo.json"
    try:
        with open(config_path, "r") as zenodo_config:
            config = json.load(zenodo_config)
    except FileNotFoundError:
        # TODO email admin config error
        return {
            "status_code": 500,
            "message": "Cannot process DOI. Please contact EnviDat team.",
            "error": f"Cannot not find config file: {config_path}",
        }

    # Assign records_url, return error if needed values not set in config
    records_url = config.get("externalApi", {}).get("zenodoRecords")
    if not records_url:
        # TODO email admin config error
        return {
            "status_code": 500,
            "message": "Cannot process DOI. Please contact EnviDat team.",
            "error": "Cannot not get externalApi.zenodoRecords from config",
        }

    # Get record from Zenodo API
    api_url = f"{records_url}/{record_id}"
    timeout = config.get("timeout", 3)

    response = requests.get(api_url, timeout=timeout)

    # TODO convert Zenodo response to EnviDat format

    # Handle unsuccessful response
    if response.status_code != 200:
        return {
            "status_code": response.status_code,
            "message": f"The following DOI was not found: {doi}",
            "error": response.json(),
        }

    # Convert Zenodo record to EnviDat format
    envidat_record = convert_zenodo_to_envidat(
        response.json(), user, config, add_placeholders
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

    record_id = doi[period_index + 1 :]

    if not record_id:
        return None

    return record_id.strip()


# TODO add placeholder values for required fields if add_placeholders true
# TODO test creating CKAN package empty metadata
#  and dict returned if add_placeholders true
# TODO add try/except handling
def convert_zenodo_to_envidat(
    data: dict, user: dict, config: dict, add_placeholders: bool = False
) -> dict:
    """Convert Zenodo record dictionary to EnviDat CKAN package format.

    If add_placeholders true then add default values from config.
    Values added are required by EnviDat CKAN to create a new package.

    Args:
        data (dict): Response data object from Zenodo API call
        user (dict): CKAN user dictionary
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

    # TODO review if function should throw error if id does not exist
    #  (should it be mandatory?)
    # creator_user_id
    creator_user_id = user.get("id")
    if creator_user_id:
        pkg.update({"creator_user_id": creator_user_id})

    # date
    publication_date = metadata.get("publication_date", "")
    dte = get_date(publication_date, add_placeholders)
    if dte:
        pkg.update({"date": json.dumps(dte, ensure_ascii=False)})

    # publication
    publication = get_publication(publication_date, add_placeholders)
    if publication:
        pkg.update({"publication": json.dumps(publication, ensure_ascii=False)})

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

    pkg.update(
        {
            "license_id": license_data.get("license_id", "other-undefined"),
            "license_title": license_data.get(
                "license_title", "Other (Specified " "in the " "description)"
            ),
        }
    )

    license_url = license_data.get("license_url")
    if license_url:
        pkg.update({"license_url": license_url})

    # TODO determine if maintainer should be user
    # TODO add placeholder values for maintainer because it is required
    # maintainer

    # name
    title = metadata.get("title", "")
    # TODO handle if title does not exist (name is required)

    name = get_name(title, add_placeholders)
    if name:
        pkg.update({"name": name})

    # title
    # TODO handle if title does not exist (title is required)
    # TODO possibly implement add_placeholders
    if title:
        pkg.update({"title": title})

    # notes
    description = metadata.get("description", "")
    notes = get_notes(description, config, add_placeholders)
    if notes:
        pkg.update({"notes": notes})

    # TODO determine how owner_org should be assigned (it is mandatory)
    # owner_org

    # related_publications
    references = metadata.get("references", [])
    related_publications = get_related_publications(references)
    if related_publications:
        pkg.update({"related_publications": related_publications})

    # TODO review if default value of resource_type_general should be "dataset",
    #  see "publication_type" in Zenodo docs
    pkg.update({"resource_type_general": "dataset"})

    # spatial
    # default spatial value is point set to WSl Birmsensdorf, Switzerland
    # office coordinates
    if add_placeholders:
        spatial = config\
            .get("spatial", {})\
            .get("default",
                 "{\"type\": \"Point\", \"coordinates\": [8.4545978, 47.3606372]}")
        pkg.update({"spatial": spatial})

    # TODO start dev here
    # tags
    keywords = metadata.get("keywords", [])
    tags = get_tags(keywords, title, add_placeholders)
    if tags:
        pkg.update({"tags": tags})

    return pkg


def get_authors(creators: list, add_placeholders: bool = False) -> list:
    """Returns authors in EnviDat formattted list.

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
            author.update({"given_name": names[2].strip(), "name": names[0].strip()})
        elif " " in creator_names:
            names = creator_names.partition(" ")
            author.update({"given_name": names[0].strip(), "name": names[2].strip()})
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
    """Returns dates in Envidat format.

    Args:
        publication_date (str): publication_date string in Zenodo record
        add_placeholders (bool): If true placeholder values are added for
                     required EnviDat package fields. Default value is False.
    """
    dates = []

    # TODO finalize placeholder date and date_type
    if add_placeholders and not publication_date:
        date_today = date.today()
        date_str = date_today.strftime("%Y-%m-%d")
        date_dict = {"date": date_str, "date_type": "created"}
        dates.append(date_dict)

    elif publication_date:
        date_dict = {"date": publication_date, "date_type": "created"}
        dates.append(date_dict)

    return dates


def get_publication(publication_date: str, add_placeholders: bool = False) -> dict:
    """
    Returns publication in EnviDat format

    Args:
        publication_date (str): publication_date string in Zenodo record
        add_placeholders (bool): If true placeholder values are added for
                     required EnviDat package fields. Default value is False.
    """
    publication = {}

    # TODO finalize placeholder publication_year and publisher
    if add_placeholders and not publication_date:
        date_today = date.today()
        year = date_today.strftime("%Y")
        publication.update({"publication_year": year, "publisher": "Zenodo"})

    # TODO finalize placeholder publication_year and publisher
    elif publication_date:
        try:
            dt = datetime.strptime(publication_date, "%Y-%m-%d")
            year = dt.year
            publication.update({"publication_year": year, "publisher": "Zenodo"})
        # TODO should default values be assigned if ValueError?
        except ValueError:
            # date_today = date.today()
            # year = date_today.strftime("%Y")
            # publication.update({"publication_year": year, "publisher": "Zenodo"})
            return publication

    return publication


def get_funding(grants: list, add_placeholders: bool = False) -> list:
    """Returns funding in EnviDat formatted list.

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


def get_license(license_id: str, config: dict, add_placeholders: bool = False) -> dict:
    """Returns license data in dictionary with EnviDat formatted keys.

    Args:
        license_id (str): license_id string in Zenodo record
        config (dict): Zenodo config dictionary
        add_placeholders (bool): If true placeholder values are added for
                     required EnviDat package fields. Default value is False.
    """
    # Extract licenses from config
    envidat_licenses = config.get("envidatLicenses", {})

    # Assign other_undefined for placeholder values and unknown licenses
    other_undefined = envidat_licenses.get(
        "other-undefined",
        {
            "license_id": "other-undefined",
            "license_title": "Other (Specified in the description)",
        },
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


def get_name(title: str, add_placeholders: bool = False) -> str:
    """Returns name (of metadata entry) in lowercase with words joined by hyphens.

    If name with hyphens longer than 80 characters truncates name to last whole
    word.

    Args:
        title (str): title string in Zenodo record
        add_placeholders (bool): If true placeholder values are added for
                     required EnviDat package fields. Default value is False.
    """
    # TODO finalize placeholder name (or return error)
    if add_placeholders and not title:
        pass

    regex_replacement = "[^0-9a-z- ]"
    name = re.sub(regex_replacement, "", title.lower())

    name_split = name.split(" ")
    name_join = "-".join(name_split)

    if len(name_join) > 80:
        name_trunc = name_join[:80]
        name_trunc_split = name_trunc.split("-")
        name_trunc_split.pop()
        return "-".join(name_trunc_split)

    return name_join


# TODO confirm EnviDat CKAN can accept HTML strings for "notes" value
# TODO determine if notes should still be returned if len(description) < 100
def get_notes(description: str, config: dict, add_placeholders: bool = False) -> str:
    """
    Returns notes, if notes are less than 100 characters then inserts
    message from config to beginning of notes.

    Args:
        description (str): description string in Zenodo record
        config (dict): Zenodo config dictionary
        add_placeholders (bool): If true placeholder values are added for
                     required EnviDat package fields. Default value is False.
    """
    notes_message = config.get("notes", {}).get(
        "default",
        "Automatic message from EnviDat Admin: the "
        "description of this dataset is too short and "
        "therefore, not informative enough. Please improve "
        "and then delete this message. ",
    )

    if add_placeholders and len(description) < 100:
        description = f"{notes_message}{description}"

    return description.strip()


def get_related_publications(references: list) -> str:
    """
    Returns related_publications in markdown string (as an unordered list)

    If references empty then returns empty string ""

    Args:
        references (list): references list in Zenodo record
    """
    related_publications = ""

    if references:
        start_str = "* "
        related_publications = "\r\n * ".join(references)
        return f"{start_str}{related_publications}"

    return related_publications


def get_tags(keywords: list, title: str, add_placeholders: bool = False) -> list:
    """
    Return tags in EnviDat format

    Args:
        keywords (list): keywords in Zenodo record
        title (str): title string in Zenodo record
        add_placeholders (bool): If true placeholder values are added for
                   required EnviDat package fields. Default value is False.
    """
    tags = []

    # Handle all keywords in one element and separated by commas
    if len(keywords) == 1:
        keywords = keywords[0].split(",")

    # Format keywords
    regex_replacement = "[^0-9A-Z-_. ]"
    for keyword in keywords:
        word = re.sub(regex_replacement, "", keyword.upper().strip())
        tags.append({"name": word})

    # TODO review if ZENODO keyword should be added by default to tags
    tags.append({"name": "ZENODO"})

    if add_placeholders:
        extra_tags = get_extra_tags(title, tags)
        tags += extra_tags

    return tags


# TODO test if it is possible to create datset with duplicate tag names
def get_extra_tags(title: str, tags: list) -> list:
    """
    Returns extra tags extracted from title in EnviDat format

    Example Zenodo DOI without any keywords: 10.5281/zenodo.7370384

    Args:
       title (str): title string in Zenodo record
       tags (list): tags list in EnviDat format
    """
    extra_tags = []

    if len(tags) < 5:

        num_new_tags = 5 - len(tags)
        counter = 0

        words = title.split(" ")
        index = 0

        while counter < num_new_tags:

            # Handle short titles
            if index + 1 > len(words):
                extra_tags.append({"name": "ZENODO"})
                counter += 1
                index += 1
                continue

            # Format word
            regex_replacement = "[^0-9A-Z-_. ]"
            word = re.sub(regex_replacement, "", words[index].upper().strip())

            # Append formatted word to extra_tags if it is at least 4 characters
            if len(word) >= 4:
                extra_tags.append({"name": word})
                counter += 1

            index += 1

    return extra_tags


# TODO remove tests
# TESTS
# test = get_extra_tags("", [])
# test = get_tags([], "Yes I three k*werlk", True)
# print(test)

# test = get_authors([{}], True)
# # test = get_authors([{}], True)
# # test = get_authors([{}])
#
# test = convert_zenodo_to_envidat({}, '123', True)
# # test = convert_zenodo_to_envidat({}, '123')

# test = get_date("")
# test = get_funding([], True)

# string = "function00al red()()(undancy of non-vo***lant small mammPPPals " \
#          "increases in " \
#          "human234576666"
# test = get_name(string)

# test = get_notes("134gdd ", {}, True)

# print(test)

# test = get_publication("", True)
# print(test)
