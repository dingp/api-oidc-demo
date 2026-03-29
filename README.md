# N10 API OIDC Demo

This repository contains the code and deployment assets for a FastAPI demo that authenticates requests with a Keycloak-issued token and retrieves the stored external broker token for the `globus` identity provider.

## Repository Contents

- `app/`: application code, HTML templates, Python dependencies, and local configuration example
- `image/Dockerfile`: container image definition for the FastAPI app
- `helm/n10-api-oidc-demo`: Helm chart for deploying the app to Kubernetes
- `.github/workflows/build-image.yaml`: GitHub Actions workflow that builds and publishes the image to GHCR

## Application Layout

The runnable app lives under `app/`:

- `app/n10_api_oidc_demo/main.py`: FastAPI entrypoint
- `app/n10_api_oidc_demo/auth.py`: bearer token validation against Keycloak JWKS
- `app/n10_api_oidc_demo/keycloak.py`: Keycloak broker token call
- `app/templates/`: single-page frontend and silent SSO helper
- `app/requirements.txt`: Python dependencies
- `app/.env.example`: local environment example

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
cp app/.env.example .env
uvicorn n10_api_oidc_demo.main:app --app-dir app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Docker Build

Build the image from the repository root:

```bash
docker build -f image/Dockerfile -t n10-api-oidc-demo .
```

## Helm Install

Install or upgrade with:

```bash
helm upgrade --install n10-api-oidc-demo helm/n10-api-oidc-demo \
  -n keycloak-demo \
  --create-namespace \
  --set image.repository=ghcr.io/<owner>/n10-api-oidc-demo \
  --set app.keycloakBaseUrl='https://keycloak.example.org' \
  --set app.keycloakRealm='demo' \
  --set app.keycloakClientId='demo-web'
```

If you expose the app publicly, make sure the Keycloak client allows the final redirect URI and web origin.

## Notes

- This demo intentionally accepts the frontend's ID token as the API bearer token because that is the requested flow.
- For production APIs, an access token is normally the correct credential instead.
- The backend expects the Keycloak broker alias to be `globus` by default, but that is configurable in both `.env` and Helm values.
