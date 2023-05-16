# DOI Publishing API

Microservice API used by EnviDat to publish DOIs on Datacite.

[View the API docs](https://envidat.gitlab-pages.wsl.ch/doi-publishing-api)

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
