# DOI Publishing API Chart

Chart for DOI Publishing API in FastAPI.

- Interfaces with production database.
- Can autoscale with load.

## Secrets

Requires secrets to be pre-populated.

- **doi-publishing-vars** prod db password, fastapi variables

  - key: DB_PASS  (for production database)
  - key: SECRET_KEY  (for fastapi)
  - key: BACKEND_CORS_ORIGINS  (list in format '["http://...", "..."]')
    - Note: also add the Auth0 domain to the CORS list.

  ```bash
  kubectl create secret generic doi-publishing-vars \
  --from-literal=DB_PASS=xxxxxxx \
  --from-literal=SECRET_KEY=xxxxxxx \
  --from-literal=BACKEND_CORS_ORIGINS='["xxx", "xxx"]'
  ```

- **envidat-star** for https / tls certs

  - Standard Kubernetes TLS secret for \*.envidat.ch

## Deployment

```bash
helm upgrade --install doi-publishing-api oci://registry-gitlab.wsl.ch/envidat/doi-publishing-api --namespace envidat --create-namespace
```
