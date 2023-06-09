"""Script to convert and import Zenodo DOIs to EnviDat."""

# COMMAND to run from root directory with required argument "--authorization"":
#   python -m scripts.zenodo_import --authorization 23iuo423434298749837498794749749749

# Imports
import argparse

# Setup logging
import logging
import time
from logging import getLogger

from app.auth import get_user
from app.logic.external_doi.utils import read_dois_urls
from app.logic.external_doi.zenodo import convert_zenodo_doi
from app.logic.remote_ckan import ckan_call_action_return_exception, get_ckan

log = getLogger(__name__)
log.setLevel(level=logging.INFO)

# Setup up file log handler
log_file_formatter = logging.Formatter(
    fmt="%(levelname)s %(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler = logging.FileHandler(filename="scripts/logs/zenodo_import.log")
file_handler.setFormatter(log_file_formatter)
file_handler.setLevel(level=logging.INFO)
log.addHandler(file_handler)


def import_zenodo_records():
    """Convert and import Zenodo DOIs to EnviDat.
    Logs success or failure to file_handler.
    """
    # Assign start_time
    print("Starting zenodo_import.py...")
    start_time = time.time()

    # Setup argument parser
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--authorization",
        type=str,
        required=True,
        help="EnviDat CKAN cookie for logged "
        "in user passed in "
        "authorization header",
    )
    parser.add_argument(
        "--owner_org",
        type=str,
        default="bd536a0f-d6ac-400e-923c-9dd351cb05fa",
        help="EnviDat CKAN owner_org, default value corresponds to Trusted Users "
        "Organization",
    )

    parser.add_argument(
        "--csv_path",
        type=str,
        default="scripts/zenodo_dois.csv",
        help="Path to CSV file with Zenodo DOIs. Each DOI should be in "
        "the first column and listed row by row. "
        "Default value is 'scripts/zenodo_dois.csv",
    )

    args = parser.parse_args()

    # Get Zenodo DOIs
    zenodo_dois = read_dois_urls(args.csv_path)
    log.info(
        f"START processing CSV file {args.csv_path}, " f"it has {len(zenodo_dois)} DOIs"
    )

    # Authorize user
    user = get_user(args.authorization)

    # Convert and import Zenodos DOIs
    counter = 1

    for doi in zenodo_dois:
        # Convert record
        record = convert_zenodo_doi(
            doi=doi, owner_org=args.owner_org, user=user, add_placeholders=True
        )

        # Extract name from record
        name = record.get("result", {}).get("name")

        # Handle failed conversion of Zenodo record to EnviDat format
        if not name:
            error = record.get("error")
            log.error(
                f"{counter}  Failed to convert DOI {doi} to EnviDat format, "
                f"error: {error}"
            )
            continue

        # Create CKAN package with converted DOI record
        ckan = get_ckan(args.authorization)
        ckan_pkg = ckan_call_action_return_exception(
            ckan,
            action="package_create",
            data=record.get("result"),
        )

        # Log success or error
        if ckan_pkg.get("success"):
            log.info(
                f"{counter}  Successfully created CKAN package "
                f"for DOI '{doi}' with name '{name}'"
            )
        else:
            result = ckan_pkg.get("result")
            log.error(
                f"{counter}  Failed to created CKAN package for DOI '{doi}' "
                f"with name '{name}', error:  {result}"
            )

        # Increment counter
        counter += 1

    # Assign and format timer, print execution time
    end_time = time.time()
    timer = end_time - start_time
    print(f"...Ending zenodo_import.py, that took {round(timer, 2)} seconds")
    print("\n")


if __name__ == "__main__":
    import_zenodo_records()
