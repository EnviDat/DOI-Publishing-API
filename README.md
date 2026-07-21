# doi-publishing-api

Microservice API to publish DOIs on DataCite.

[Read the API docs](https://www.envidat.ch/doi-api/docs)

 ---

## Email 

This service works in tandem with the email relay server [Catapulte](https://github.com/jdrouet/catapulte).

The EnviDat email microservice can be found [here](https://gitlabext.wsl.ch/EnviDat/email-microservice).

## Development Usage

1. Configure environment variables for use **only in local development**

   - Make a file named `.env` in the root directory
   - Generate the variables using `env.example` as a reference
   - New environment variables must be added to:
     - `env.example` because this file is used for validation
     - `environment` section of the `doi-api` containers in the `docker-compose.<branch>.yml` files
     -  Echoed into `build.env` in the `set-vars` job in `gitlab-ci.yml` 

2. Clone project, make sure virtual environment is installed and activated, and execute the following command:

   ```bash
    pdm sync --dev
   ```

3. Run the FastAPI development server:

   ```bash
   pdm run dev
   ```

4. Access local server at: http://127.0.0.1:8000


## Production Usage

1. Configure CI/CD variables used in production server (`main` environment) or staging server (`staging` environment)

   - Create **individual CI/CD variables for each variable** listed in `env.example`
   - `APP_VERSION` **must be incremented** so that a new image is built and the application includes the updated code
     - Create a git tag for the commit that corresponds to the `APP_VERSION`
     - Update the `version` value in `pyproject.toml`
     - Also create an entry in the `CHANGELOG`
   - `ROOT_PATH` is an optional CI/CD variable and should only be used to if the application uses a proxy
     - Be sure to include a `/` before the `ROOT_PATH` value
     - Example configuration: `ROOT_PATH=/doi-api`
     - [Click here for the FastAPI documentation about using a proxy server](https://fastapi.tiangolo.com/advanced/behind-a-proxy/)
   - Create **individual CI/CD variables for each the following variables** (apart from the ones in env.example) that are used for deployment or scheduled pipelines:

     > | Key                | Example Value                                                            |
     > |--------------------|--------------------------------------------------------------------------|
     > | `APP_VERSION`      | `1.1.2`                                                                  |
     > | `ROOT_PATH`        | `""`                                                                     |
     > | `INTERNAL_REG`     | `registry-gitlab.org.ch/orgname`                                         |
     > | `EXTERNAL_REG`     | `docker.io`                                                              |
     > | `NGINX_IMG_TAG`    | `1.25`                                                                   |
     > | `PYTHON_IMG_TAG`   | `3.10`                                                                   |
     > | `FOREST3D_API_URL` | `https://my-server.com/doi-api/forest3d/datacite/publish?is-update=true` |
     > | `TRIA_API_URL`     | `https://my-server.com/doi-api/tria/datacite/publish?is-update=true`     |

2. Merge feature/development branch to `main` default branch
   - The image related variables can be group variables inherited from the parent group

### Forest3D Datasets

The `/forest3d/datacite/publish` endpoint bulk publishes Forest3D endpoints to DataCite. 
- The metadata for Forest3D datasets are read from an external online JSON file that is set in the CI/CD variable `FOREST3D_URL`.
- Requires `forest3d-key` header parameter that matches the value for CI/CD variable `FOREST3D_API_KEY`.
- Forest3D datasets' `doi` values must end with a digit to be considered valid.
- Optionally if `is-update` query parameter is `true` then updates existing Forest3D datasets in DataCite (if the `metadata_modified` date is within the last 30 days.)
- The GitLab scheduled pipeline executes every 24 hours and requires that the CI/CD variable `FOREST3D_API_URL` is set for the corresponding server/environment. 

### TRIA Datasets

The `/tria/datacite/publish` endpoint bulk publishes TRIA datasets to DataCite.
- The metadata for TRIA datasets are read from an external online JSON file that is set in the CI/CD variable `TRIA_URL`.
- Requires `tria-key` header parameter that matches the value for CI/CD variable `TRIA_API_KEY`.
- TRIA datasets' `doi` values must end with a digit to be considered valid.
- Optionally if `is-update` query parameter is `true` then updates existing TRIA datasets in DataCite (if the `metadata_modified` date is within the last 30 days.)
- The GitLab scheduled pipeline executes every 24 hours and requires that the CI/CD variable `TRIA_API_URL` is set for the corresponding server/environment. 

## Pre-commit hooks

- To run the pre-commit hooks manually open app in terminal and execute: `pre-commit run --all-files`
- These hooks ensure that the application uses standard stylistic conventions
- To view or alter the pre-commit hooks see: `.pre-commit-config.yaml`


## Authors

The following employees of the Swiss Federal Institute for Forest, Snow and Landscape Research WSL:
- Ranita Pal
- Rebecca Buchholz
- Sam Woodcock

## License

[MIT License](https://gitlabext.wsl.ch/EnviDat/envidat-converters-api/-/blob/main/LICENSE?ref_type=heads)