"""Retrieve and convert Zenodo DOI metadata to EnviDat CKAN package format."""

import json

import logging
import re
from datetime import date, datetime

import markdownify
import requests

from app.logic.external_doi.constants import ConvertError, ConvertSuccess
from app.logic.remote_ckan import ckan_current_package_list_with_resources

log = logging.getLogger(__name__)


# TODO run code formatters pre-commit hook

def convert_zenodo_doi(
        doi: str, owner_org: str, user: dict, add_placeholders: bool = False
) -> ConvertSuccess | ConvertError:
    """Return metadata for input doi and convert metadata to EnviDat
    CKAN package format.

    Note: Converts data that exists in Zenodo metadata record
    By default does not provide default placeholders values for
    EnviDat CKAN package required/optional fields.
    If add_placeholders is True adds default placeholder values.

    If Zenodo doi metadata cannot be retrieved or conversion fails then
    returns error dictionary.

    Args:
        doi (str): Input doi string
        owner_org (str): 'owner_org' assigned to user in EnviDat CKAN
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
            "error": f"Cannot extract record ID from input Zenodo DOI: {doi}",
        }

    # Get config
    config_path = "app/config/zenodo.json"
    try:
        with open(config_path, "r") as zenodo_config:
            config = json.load(zenodo_config)
    except FileNotFoundError as e:
        log.error(f"ERROR: {e}")
        return {
            "status_code": 500,
            "message": "Cannot process DOI. Please contact EnviDat team.",
            "error": f"Cannot find config file: {config_path}",
        }

    # Assign records_url
    records_url = config.get("zenodoAPI", {}).get(
        "zenodoRecords", "https://zenodo.org/api/records"
    )

    # Get record from Zenodo API
    api_url = f"{records_url}/{record_id}"
    timeout = config.get("timeout", 3)

    try:
        # Get record from Zenodo API
        response_zenodo = requests.get(api_url, timeout=timeout)

        # Handle unsuccessful response
        if response_zenodo.status_code != 200:
            return {
                "status_code": response_zenodo.status_code,
                "message": f"The following DOI was not found: {doi}",
                "error": response_zenodo.json(),
            }

        # Convert Zenodo record to EnviDat format
        envidat_record = convert_zenodo_to_envidat(
            response_zenodo.json(), owner_org, user, config, add_placeholders
        )

    except Exception as e:
        log.error(f"ERROR: {e}")
        return {
            "status_code": 500,
            "message": f"Could not process DOI {doi}. Please contact EnviDat team.",
            "error": f"Failed to process DOI {doi}. Check logs for errors.",
        }

    return envidat_record


def get_zenodo_record_id(doi: str) -> str | None:
    """Return record ID extracted from Zenodo Doi.
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

    return record_id.strip()


def convert_zenodo_to_envidat(
        data: dict, owner_org: str, user: dict, config: dict,
        add_placeholders: bool = False
) -> ConvertSuccess | ConvertError:
    """Convert Zenodo record dictionary to EnviDat CKAN package format.

    If add_placeholders true then add default values from config.
    Values added are required by EnviDat CKAN to create a new package.

    Args:
        data (dict): Response data object from Zenodo API call
        owner_org (str): 'owner_org' assigned to user in EnviDat CKAN
        user (dict): CKAN user dictionary
        config (dict): config dictionary created from config/zenodo.json
        add_placeholders (bool): If true placeholder values are added for
                       required EnviDat package fields. Default value is False.
    """
    # Assign dictionary to contain values converted from Zenodo
    # to EnviDat CKAN package format
    pkg = {}

    # Extract "metadata" dictionary from input "data"
    # metadata is used to extract and convert values to EnviDat package format
    metadata = data.get("metadata", {})

    # doi
    doi = data.get("doi")
    pkg.update({"doi": doi})

    # title
    title = metadata.get("title")

    # Return error if title not found
    if not title:
        err = f"'title' not found in DOI: {doi}"
        log.error(err)
        return {
            "status_code": 500,
            "message": f"Could not process DOI: {doi}",
            "error": err,
        }
    # Else add title to pkg
    pkg.update({"title": title})

    # name
    name = get_name(title)
    if name:
        pkg.update({"name": name})

    # author
    creators = metadata.get("creators", [])
    authors = get_authors(creators, user, config, add_placeholders)
    if authors:
        pkg.update({"author": json.dumps(authors, ensure_ascii=False)})

    # maintainer
    maintainer = get_maintainer(user, config)
    pkg.update({"maintainer": json.dumps(maintainer, ensure_ascii=False)})

    # owner_org
    pkg.update({"owner_org": owner_org})

    # date
    publication_date = metadata.get("publication_date", "")
    dte = get_date(publication_date, add_placeholders)
    if dte:
        pkg.update({"date": json.dumps(dte, ensure_ascii=False)})

    # publication
    publication = get_publication(publication_date, config, add_placeholders)
    if publication:
        pkg.update({"publication": json.dumps(publication, ensure_ascii=False)})

    # funding
    grants = metadata.get("grants", [])
    funding = get_funding(grants, config, add_placeholders)
    if funding:
        pkg.update({"funding": json.dumps(funding, ensure_ascii=False)})

    # language ("en" English is default language)
    pkg.update({"language": "en"})

    # license
    license_id = metadata.get("license", {}).get("id", "")
    license_data = get_license(license_id, config, add_placeholders)

    pkg.update(
        {
            "license_id": license_data.get("license_id", "other-undefined"),
            "license_title": license_data.get(
                "license_title", "Other (Specified in the description)"
            ),
        }
    )

    license_url = license_data.get("license_url")
    if license_url:
        pkg.update({"license_url": license_url})

    # notes
    description = metadata.get("description", "")
    notes = get_notes(description, config)
    if notes:
        pkg.update({"notes": notes})

    # related_publications
    references = metadata.get("references", [])
    related_publications = get_related_publications(references)
    if related_publications:
        pkg.update({"related_publications": related_publications})

    # resource_type_general
    pkg.update({"resource_type_general": "dataset"})

    # spatial
    # default spatial value is point set to WSl Birmsensdorf, Switzerland
    # office coordinates
    if add_placeholders:
        spatial = config.get("spatial", {}).get(
            "default", '{"type": "Point", "coordinates": [8.4545978, 47.3606372]}'
        )
        pkg.update({"spatial": spatial})

    # version
    version = metadata.get("version")
    if version:
        pkg.update({"version": version})

    # files
    files = data.get("files", [])
    resources = get_resources(files)
    if resources:
        pkg.update({"resources": resources})

    # tags
    keywords = metadata.get("keywords", [])
    tags = get_tags(keywords, title, add_placeholders)
    if tags:
        pkg.update({"tags": tags})

    return {"status_code": 200, "result": pkg}


def get_authors(
        creators: list, user: dict, config: dict, add_placeholders: bool = False
) -> list:
    """Returns authors in EnviDat formattted list.

    Args:
        creators (dict): creators list in Zenodo record
        user (dict): CKAN user dictionary
        config (dict): Zenodo config dictionary
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
        if creator_names and "," in creator_names:
            names = creator_names.partition(",")
            author.update({"given_name": names[2].strip(), "name": names[0].strip()})
        elif creator_names and " " in creator_names:
            names = creator_names.partition(" ")
            author.update({"given_name": names[0].strip(), "name": names[2].strip()})
        elif add_placeholders:
            fullname = user.get("fullname", "")
            if fullname:
                names = fullname.partition(" ")
                author.update(
                    {"given_name": names[0].strip(), "name": names[2].strip()}
                )
            else:
                name_default = (
                    config.get("author", {}).get("default", {}).get("name", "UNKNOWN")
                )
                author.update({"name": name_default})

        affiliation = creator.get("affiliation", "")
        if affiliation:
            author.update({"affiliation": affiliation.strip()})
        elif add_placeholders:
            affiliation_default = (
                config.get("author", {})
                .get("default", {})
                .get("affiliation", "UNKNOWN")
            )
            author.update({"affiliation": affiliation_default})

        identifier = creator.get("orcid", "")
        if identifier:
            author.update({"identifier": identifier.strip()})

        authors.append(author)

    return authors


def get_maintainer(user: dict, config: dict) -> dict:
    """Returns maintainer in EnviDat format.

    Args:
        user (dict): CKAN user dictionary
        config (dict): Zenodo config dictionary
    """
    maintainer = {}

    fullname = user.get("fullname", "")
    if fullname:
        names = fullname.partition(" ")
        maintainer.update({"given_name": names[0].strip(), "name": names[2].strip()})
    else:
        name_default = (
            config.get("maintainer", {}).get("default", {}).get("name", "UNKNOWN")
        )
        maintainer.update({"name": name_default})

    email = user.get("email", "")
    if email:
        maintainer.update({"email": email})
    else:
        email_default = (
            config.get("maintainer", {})
            .get("default", {})
            .get("email", "envidat@wsl.ch")
        )
        maintainer.update({"email": email_default})

    return maintainer


def get_date(publication_date: str, add_placeholders: bool = False) -> list:
    """Returns dates in Envidat format.

    Args:
        publication_date (str): publication_date string in Zenodo record
        add_placeholders (bool): If true placeholder values are added for
                     required EnviDat package fields. Default value is False.
    """
    dates = []

    if add_placeholders and not publication_date:
        date_today = date.today()
        date_str = date_today.strftime("%Y-%m-%d")
        date_dict = {"date": date_str, "date_type": "created"}
        dates.append(date_dict)

    elif publication_date:
        date_dict = {"date": publication_date, "date_type": "created"}
        dates.append(date_dict)

    return dates


def get_publication(
        publication_date: str, config: dict, add_placeholders: bool = False
) -> dict:
    """Returns publication in EnviDat format.

    Args:
        publication_date (str): publication_date string in Zenodo record
        config (dict): Zenodo config dictionary
        add_placeholders (bool): If true placeholder values are added for
                     required EnviDat package fields. Default value is False.
    """
    publication = {}

    publisher_default = (
        config.get("publication", {}).get("default", {}).get("publisher", "Zenodo")
    )

    if add_placeholders and not publication_date:
        date_today = date.today()
        year = date_today.strftime("%Y")
        publication.update({"publication_year": year, "publisher": publisher_default})

    elif publication_date:
        try:
            dt = datetime.strptime(publication_date, "%Y-%m-%d")
            year = str(dt.year)
            publication.update(
                {"publication_year": year, "publisher": publisher_default}
            )
        except ValueError:
            date_today = date.today()
            year = date_today.strftime("%Y")
            publication.update(
                {"publication_year": year, "publisher": publisher_default}
            )
            return publication

    return publication


def get_funding(grants: list, config: dict, add_placeholders: bool = False) -> list:
    """Returns funding in EnviDat formatted list.

    Args:
        grants (list): grants list in Zenodo record
        config (dict): Zenodo config dictionary
        add_placeholders (bool): If true placeholder values are added for
                     required EnviDat package fields. Default value is False.
    """
    funding = []

    if add_placeholders and not grants:
        funder_default = (
            config.get("funding", {}).get("default", {}).get("institution", "UNKNOWN")
        )
        funder = {"institution": funder_default}
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
    envidat_licenses = config.get("licenses", {})

    # Assign other_undefined for placeholder values and unknown licenses
    other_undefined = envidat_licenses.get(
        "other-undefined",
        {
            "license_id": "other-undefined",
            "license_title": "Other (Specified in the description)",
        },
    )

    if add_placeholders and not license_id:
        return other_undefined

    match license_id:
        case "CC-BY-4.0":
            return envidat_licenses.get("cc-by", other_undefined)

        case "CC-BY-SA-4.0":
            return envidat_licenses.get("cc-by-sa", other_undefined)

        case "CC-BY-NC-4.0":
            return envidat_licenses.get("cc-by-nc", other_undefined)

        case "CC0-1.0":
            return envidat_licenses.get("CC0-1.0", other_undefined)

        case _:
            return other_undefined


def get_name(title: str) -> str:
    """Returns name (of metadata entry) in lowercase with words joined by hyphens.

    If name with hyphens longer than 80 characters truncates name to last whole
    word.

    Args:
        title (str): title string in Zenodo record
    """
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


def get_notes(description: str, config: dict) -> str:
    """Returns notes, converts HTML to markdown,
    if notes are less than 100 characters then inserts
    message from config to beginning of notes.

    Args:
        description (str): description string in Zenodo record
        config (dict): Zenodo config dictionary
    """
    description_md = markdownify.markdownify(description.strip())

    notes_message = config.get("notes", {}).get(
        "default",
        "Automatic message from EnviDat Admin: the "
        "description of this dataset is too short and "
        "therefore, not informative enough. Please improve "
        "and then delete this message. ",
    )

    if len(description_md) < 100:
        description_md = f"{notes_message}{description_md}"

    return description_md.strip()


def get_related_publications(references: list) -> str:
    """Returns related_publications in markdown string (as an unordered list).

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
    """Return tags in EnviDat format.

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

    tags.append({"name": "ZENODO"})

    if add_placeholders:
        extra_tags = get_extra_tags(title, tags)
        tags += extra_tags

    return tags


# TODO do not allow duplicate tag names because it causes validation errors later
#  when using package_patch to update tags
def get_extra_tags(title: str, tags: list) -> list:
    """Returns extra tags extracted from title in EnviDat format.

    Function used to generate extra tags because at least 5 tags are required to create
    an EnvDat CKAN package. Duplicate tags are allowed to be sent to CKAN but will not
    appear more than once in CKAN package.

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

        while counter <= num_new_tags:
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


def get_resources(files: list) -> list:
    """Return resource in EnviDat format.

    Args:
        files (list): files in Zenodo record
    """
    resources = []

    for file in files:
        resource = {}

        name = file.get("key")
        if name:
            resource.update({"name": name})

        url = file.get("links", {}).get("self")
        if url:
            resource.update({"url": url})

        size = file.get("size")
        if size:
            resource.update({"size": size})

        type_resource = file.get("type")
        if type_resource:
            resource.update({"format": type_resource})

        restricted = {"level": "public", "allowed_users": "", "shared_secret": ""}
        resource.update({"restricted": json.dumps(restricted, ensure_ascii=False)})

        resources.append(resource)

    return resources


def get_envidat_dois(authorization: str) -> list[str]:
    """
    Returns a list of all DOIs in packages in an EnviDat CKAN instance.
    NOTE: if authorization invalid will still return packages available in public API!

    Args:
        authorization (str): authorization token
    """
    dois = []

    # Get all packages in EnviDat CKAN instance
    package_list = ckan_current_package_list_with_resources(authorization)

    # Extract doi from each package
    for package in package_list:
        doi = package.get("doi")
        if doi:
            dois.append(doi)

    return dois


def get_zenodo_dois(authorization: str, q: str, size: str = "1000"):
    """Return Zenodo DOIs extracted from records produced by search query.

    For Zenodo API documentation see: https://developers.zenodo.org/#records

    Args:
        authorization (str): authorization token
        q (str): search query (using Elasticsearch query string syntax)
        size (str): number of results to return
    """

    # Get config
    config_path = "app/config/zenodo.json"
    try:
        with open(config_path, "r") as zenodo_config:
            config = json.load(zenodo_config)
    except FileNotFoundError as e:
        log.error(f"ERROR: {e}")
        return {
            "status_code": 500,
            "message": "Cannot process DOI. Please contact EnviDat team.",
            "error": f"Cannot find config file: {config_path}",
        }

    # Assign records_url
    records_url = config.get("zenodoAPI", {}).get(
        "zenodoRecords", "https://zenodo.org/api/records"
    )

    # Get URL used to call Zenodo API
    if q:
        api_url = f"{records_url}/?q={q}&size={size}"
    else:
        api_url = f"{records_url}/?size={size}"

    print(api_url)

    try:
        # Get response from Zenodo API
        response = requests.get(api_url, timeout=10)

        # Handle unsuccessful response
        if response.status_code != 200:
            return {
                "status_code": response.status_code,
                "message": f"Could not return Zenodo records "
                           f"for the following URL: {api_url}",
                "error": response.json(),
            }

        # Get EnviDat dois
        envidat_dois = get_envidat_dois(authorization)
        print(len(envidat_dois))  # TODO remove

        response_json = response.json()
        records = response_json.get("hits", {}).get("hits", [])

        counter = 1

        for record in records:

            doi = record.get("doi")
            if doi:
                print(doi)  # TODO remove

                if doi in envidat_dois:
                    # TODO possibly add to output
                    print(f"{counter} DOI already in EnviDat: {doi}")
                    counter += 1

                else:
                    # TODO START dev here
                    # TODO make dois list and add to dois
                    # TODO return list of dois with in a valid doi.org URL format
                    pass

        return records

    except Exception as e:
        log.error(f"ERROR: {e}")
        return {
            "status_code": 500,
            "message": f"Could not return Zenodo records "
                       f"for the following URL: {api_url}",
            "error": f"Failed to process URL: {api_url}. Check logs for errors.",
        }



