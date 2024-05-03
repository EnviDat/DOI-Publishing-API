# doi-publishing-api

Microservice API to publish DOIs on Datacite.

[View the API docs](https://envidat.gitlab-pages.wsl.ch/doi-publishing-api)

## Usage

This services works in tandem with the email relay server [Catapulte](https://github.com/jdrouet/catapulte).

An example implementation can be found [here](https://gitlabext.wsl.ch/EnviDat/email-microservice).

## Dev

## Generate .env

1. Make a file **.env**.

2. Generate the variables using **env.example** as a reference.

### Option 1: Docker

1. Run the docker container:

```bash
docker compose up -d
```

> The image should pull, or fallback to building.


### Option 2: Standalone

1. Install dependencies:

```bash
pip install virtualenv
python -m venv <virtual-environment-name>
   or
Create a virtual environment with PyCharm

<virtual-environment-name>\Scripts\activate
pip install -r requirements.txt
```

2. Run the FastAPI server directly with PDM:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. Access at: http://127.0.0.1:8000

## Prod

1. Configure environment variables used in production

   - Configure CI/CD variables used to log in into production server: `DEPLOY_HOSTNAME`, `DEPLOY_SSH_KEY`, and `DEPLOY_SSH_USER`
   - Create **individual CI/CD variables for each variable** listed in `env.example`
     - The `remote-docker` job of the pipeline adds these environment variables to the Docker image
   - `APP_VERSION` **must be incremented** so that a new image is built and the application includes the updated code
     - Create a git tag for the commit that corresponds to the `APP_VERSION`
   - `ROOT_PATH` is an optional environment variable and should only be used to if the application uses a proxy
     - Be sure to include a `/` before the `ROOT_PATH` value
     - Example configuration: `ROOT_PATH=/doi-api`
     - [Click here for the FastAPI documentation about using a proxy server](https://fastapi.tiangolo.com/advanced/behind-a-proxy/)
   - Create **individual CI/CD variables for each the following variables** that are used for deployment:

     > | Key                        | Example Value                          |
     > | -------------------------- | -------------------------------------- |
     > | `INTERNAL_REG`             | `registry-gitlab.org.ch/orgname`       |
     > | `EXTERNAL_REG`             | `docker.io`                            |
     > | `NGINX_IMG_TAG`            | `1.25`                                 |
     > | `PYTHON_IMG_TAG`           | `3.10`                                 |
     > | `APP_VERSION`              | `0.1.2`                                |
     > | `ROOT_PATH`                | `""`                                   |
     > | `DEBUG`                    | `False`                                |
     > | `DB_HOST`                  | `db_server`                            |
     > | `DB_USER`                  | `envidat_test`                         |
     > | `DB_PASS`                  | `************`                         |
     > | `BACKEND_CORS_ORIGINS`     | `"http://localhost:3001"`              |
     > | `CKAN_API_URL`             | `3.10`                                 |
     > | `DATACITE_API_URL`         | `https://xxx.datacite.org/dois`        |
     > | `DATACITE_DATA_URL_PREFIX` | `https://www.envidat.ch/#/metadata/"`  |
     > | `DATACITE_CLIENT_ID`       | `WSLTEST`                              |
     > | `DATACITE_PASSWORD`        | `*******`                              |
     > | `DOI_PREFIX`               | `10.16904`                             |
     > | `DOI_SUFFIX_TAG`           | `envidat.`                             |
     > | `EMAIL_ENDPOINT`           | `http://abc.com`                       |
     > | `EMAIL_FROM`               | `abc@mail.com`                         |

2. Merge feature/development branch to `main` default branch
   - The `main` branch has a pipeline set up in `.gitlab-ci.yml` that automatically deploys changes to production server
   - The pipeline also requires CI/CD variables that are used to that are used to build and register a containter image: `IMAGE_REGISTRY_USER` and `IMAGE_REGISTRY_PASS`
     - The image related variables can be group variables inherited from the parent group

## Pre-commit hooks

- The pre-commit hooks run every time you attempt to commit files
- To run the pre-commit hooks manually open app in terminal and execute: `pre-commit run --all-files`
- These hooks ensure that the application uses standard stylistic conventions
- To view or alter the pre-commit hooks see: `.pre-commit-config.yaml`

## Tests

- Tests are located in `tests`
- Tests are run during `test` stage of the pipeline, please see `.gitlab-ci.yml`
- To run tests manually open app in terminal and execute: `pytest`

## Scripts

- Scripts and their associated logs are located in the `scripts` directory

## Authors
Ranita Pal, Swiss Federal Institute for Forest, Snow and Landscape Research WSL \
[Rebecca Kurup Buchholz](https://www.linkedin.com/in/rebeccakurupbuchholz/), Swiss Federal Institute for Forest, Snow and Landscape Research WSL \
Sam Woodcock, Swiss Federal Institute for Forest, Snow and Landscape Research WSL

## License

[MIT License](https://gitlabext.wsl.ch/EnviDat/envidat-converters-api/-/blob/main/LICENSE?ref_type=heads)