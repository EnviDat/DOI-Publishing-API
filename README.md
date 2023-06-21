# DOI Publishing API

Microservice API to publish DOIs on Datacite.

[View the API docs](https://envidat.gitlab-pages.wsl.ch/doi-publishing-api)

## Usage

This services works in tandem with the email relay server [Catapulte](https://github.com/jdrouet/catapulte).

An example implementation can be found [here](https://gitlabext.wsl.ch/EnviDat/email-microservice).

## Dev

### Docker

1. Make a directory `secrets`, with three files:

- fastapi.env
- db.env
- smtp.env

2. Generate the variables using **debug.env.example** as a reference.

3. Run the docker container:

```bash
docker compose up -d
```

4. Access at: http://localhost:9555

### Standalone

1. Generate **secrets/debug.env**, using **debug.env.example** as a reference.

2. Install dependencies:

```bash
pip install pdm
pdm instal
```

3. Run the FastAPI server directly with PDM:

```bash
pdm run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

4. Access at: http://127.0.0.1:8000

## Prod

### Docker

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```shell
helm upgrade --install doi-publishing-api oci://registry-gitlab.wsl.ch/envidat/doi-publishing-api --namespace envidat --create-namespace
```

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

> Note: Make sure you don't commit the updated `pyproject.toml` and `pdm.lock` files.
