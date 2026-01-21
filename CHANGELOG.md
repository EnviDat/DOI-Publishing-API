# CHANGELOG

## 1.2.7 (2026-01-21)
### Fix
- Revert external 'doi' check


## 1.2.6 (2026-01-21)
### Refactor
- 'doi' check error formatting


## 1.2.5 (2026-01-21)
### Refactor
- Check if 'doi' already exists in CKAN if publishing external DOI


## 1.2.4 (2026-01-21)
### Refactor
- Remove external 'doi' API call in publish endpoint 


## 1.2.3 (2026-01-17)
### Fix
- Improve error handling for external doi validation


## 1.2.2 (2026-01-16)
### Refactor
- Clarify external 'doi' publish response message 


## 1.2.1 (2026-01-16)
### Refactor
- Allow 'doi' validation to optionally accept non-EnviDat DOI prefixes


## 1.2.0 (2026-01-16)
### Feature
- Add 'is-external-doi' param to 'datacite/publish' endpoint


## 1.1.0 (2026-01-08)
### Refactor
- Implement pdm for project management
- Remove requirements.txt and replace with pdm.lock and pyproject.toml
### CI
- Refactor build job to use Docker instead of Kaniko
### Docs
- Update dev usage instructions to use pdm dev server
- Simplify other sections of README


## 1.0.2 (2024-12-20)
### Fix
- upgrade envidat-python-utils to version 1.4.10 to use newest version of DataCite 
  converter


## 0.1.0 (2023-07-12)
### Feature
- merge zenodo import feature
- add read_dois_url() to external_doi/utils.py
- add simplified CKAN call_action function
- add zenodo_import.py script
- finish get_zenodo_dois() and add write_dois_urls()
- add get_zenodo_doi() WIP to zenodo.py
- add function to call unauhorized CKAN actions
- add function to retrieve envidat dois
- add ckan_current_package_list_with_resources() to remote_ckan.py
- add response models to external-doi/convert endpoint
- add ConvertSucess and ConvertError classes to external-doi/constants.py
- add default doi matching logic for external-doi/convert endpoint
- add ckan_package_create to remote_ckan.py
- add resources to zenodo converter
- add maintainer to zenodo converter
- wip datacite publishing with emails
- add version to zenodo converter
- add tags to zenodo converter
- add title to zenodo converter
- add spatial to zenodo converter
- add resource_type_general to zenodo converter
- add related_publications to zenodo converter
- add publication to zenodo converter
- add notes to zenodo converter
- add name to zenodo converter
- add funding and license to zenodo converter
- add date to zenodo converter
- add author to zenodo converter
- add zenodo converter handler
- return response from zenodo api in zenodo handler
- call zenodo handler from external-doi/convert endpoint
- add zenodo handlers
- add external-doi/convert endpoint
- add external_doi util for getting external platform
- add zenodo DOI router, import endpoint, json config
- improve error handling for CKAN API calls
- add publish_datacite() helper
- work on /datacite/publish endpoint
- start endpoint datacite/publish
- add doi prefix validation to endpoint datacite/request
- add admin authorization
- support metadata update in datacite/request endpoint
- patch 'package_state' in /datacite/request endpoint
- add ckan_package_patch in remote_ckan.py
- start datacite/request endpoint
- implement ckan cookie test comments
- add test auth with cookie
- reserve draft doi with datacite in datacite/draft endpoint
- improve datacite response models
- improve "datacite/draft" endpoint
- add get_package() function
- add "/datacite/draft" endpoint and supporting logic
- add datacite router
- extract response formatter to helper function
- extract response formatter to helper function
- add reserve draft DOI in DataCite handler
- auth func to return authorization token
- add option to approval/request for updating doi
- start approval api using emailer endpoint
- mostly working DOI router, WIP draft/update
- CRUD for doi_prefix API
- auth funcs for Depends user and admin
- find next doi suffix id minter logic
- add reserve draft DOI in DataCite handler
- project structure work in progress
- argparse python func to extract openapi.json
- first commit for working api server

### Fix

- set ckan var from auth in DEBUG mode
- set package private field to False on publish
- response handling, remove todos
- datacite publishing workflow, three stages working
- tweak email endpoints, to/from emails
- doi minter, handle case where already exists
- remove refs to approval api router
- handle failed zenodo record conversion in zenodo_import.py script
- convert publication year to string in zenodo converter
- working approval endpoints, prior to removal
- add id to "user_show" call in auth.get_user
- update all routers to work with auth Depends
- working auth functions extracting authorization header
- DEBUG setting as bool not str
- add get_admin to doi router, fix draft endpoint logic
- remove /approve endpoint, pub status update_requested=updated
- use separate Edit Pydantic models for doi and prefix
- doi models, unique together constraint, table names, no ckan_name
- add DOI_SUFFIX_TAG option to settings
- IS_DOCKER bool parsing
- running dev server locally, without debugger active
- load .env in root for config by default
- update dotenv debug function error handling
- use lru_cache for fastapi settings

### Refactor

- updates to remoteckan module, update zenodo cli commands
- remove filehandler from zenodo utils (use STDOUT)
- additional logging on ckan get and patch
- implement assignment expressions in zenodo converter
- update auth to include ckan session + logging
- include ckan_name in DoiRealisation model
- extract and send error message to email microservice
- update docstring
- update log and print statements
- handle semicolons in tags in zenodo converter
- set 'private' key default so that packages are unpublished
- rename function that calls authorized CKAN actions
- implement config placeholder values in zenodo converter helpers
- improve error handling in zenodo converter
- add return types to zenodo handlers
- add return type classes to convert_doi()
- assign default config values in zenodo converter
- add 'status_code' to response in zenodo converter
- convert HTML notes to mardown in zenodo converter
- return error if title not found in zenodo converter
- add "CC0-1.0" to licenses in zenodo converter
- update placeholder authors in zenodo converter
- update config env vars
- DEBUG user variables, SITE_DATASET_URL --> DATACITE_DATA_URL
- move publication logic in zenodo converter
- improve notes in zenodo converter
- implement auth depdency injections in datacite endpoints
- improve user id extraction in zenodo converter
- remove mandatory authorization from remote_ckan.ckan_package_show
- improve settings extraction in datacite handlers
- improve auth implementation in external-doi endpoint
- improve authorization and settings logic in datacite endpoints
- revert to calling previous auth functions
- revert to previous authorization functions
- improve error handling for loading config in zenodo converter
- modify external-doi/convert endpoint to include add-placeholders query parameter
- improve logic to retry API calls
- improve error handling for datacite publish handler
- add package_state patch call to datacite/publish endpoint
- improve error handling in datacite/publish endpoint
- improve error handling in DataCite endpoints
- improve error formatting for DataCite API calls
- improve error handling for DataCite API calls
- remove 'publication_state' change for metadata updates
- extract doi validation to helper function
- rename and update imports for app.auth.authorize_user
- improve validation for auth.get_user()
- move RemoteCKAN utils to separate module
- update config url validation
- remove redundant settings, add EMAIL_ENDPOINT & EMAIL_FROM
- working doi endpoints, withoit datacite handler
- add all routers to root router
- add init files to subdirs
- move dotenv loading to config.py to allow file debugging
- refactor: remove email logic (moved to separate microservice)
- comment out non-functional code, enable piece by piece
- remove SMTP vars
- update image reg name
