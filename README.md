# doi-publishing-api

Microservice API to publish DOIs on Datacite.

[View the API docs](https://envidat.gitlab-pages.wsl.ch/doi-publishing-api)

## Usage

This services works in tandem with the email relay server [Catapulte](https://github.com/jdrouet/catapulte).

An example implementation can be found [here](https://gitlabext.wsl.ch/EnviDat/email-microservice).

## Dev

## Generate debug.env

1. Make a file **secret/debug.env** to be removed later.

2. Generate the variables using **secret/env.example** as a reference.

### Option 1: Docker

1. Run the docker container:

```bash
docker compose up -d
```

> The image should pull, or fallback to building.

2. Access at: http://localhost:9555

### Option 2: Standalone

1. Install dependencies:

```bash
pip install pdm
pdm instal
```

2. Run the FastAPI server directly with PDM:

```bash
pdm run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. Access at: http://127.0.0.1:8000

## Prod

Deployment should be handled automatically via Gitlab CI/CD.

To deploy manually follow the instructions below.

### Option 1: Docker

1. Make a file **secret/runtime.env** with required prod env vars.

2. Run the production container:

```bash
docker compose -f docker-compose.main.yml up -d
```

### Option 2: Kubernetes

See README.md under the `chart` directory.

## Pre-commit

- Install pre-commit hooks

```bash
# Install pre-commit
pip install pre-commit
# Install the hooks
pre-commit install
```

- The hooks should run every time you attempt to commit files.

- Alternatively, run the hooks manually on all files with: `pre-commit run --all-files`

- Or to run the hooks using PDM (if PATH doesn't work, e.g. on Windows):

```bash
pdm add pre-commit
pdm run pre-commit run --all-files
```
