# N10 API OIDC Demo

This repository contains a FastAPI demo and deployment assets for a Keycloak-brokered OIDC flow in realm `amsc`.

The app does four things:

- logs the user in with Keycloak using client `api-oidc-demo`
- validates the incoming Keycloak access token against the realm JWKS
- retrieves the stored external token for the brokered identity provider `globus`
- extracts the Globus token for the IRI scope and calls `https://api.iri.nersc.gov/api/v1/account/projects`

## Repository Contents

- `app/`: application code, templates, static assets, Python dependencies, and local config example
- `image/Dockerfile`: container image definition for the FastAPI app
- `helm/n10-api-oidc-demo`: Helm chart for deploying the app to Kubernetes
- `.github/workflows/build-image.yaml`: GitHub Actions workflow that builds and publishes the image to GHCR
- `KEYCLOAK_CLIENT_SETUP.md`: Keycloak setup guide for realm `amsc`

## Application Layout

The runnable app lives under `app/`:

- `app/n10_api_oidc_demo/main.py`: FastAPI routes and HTML entrypoint
- `app/n10_api_oidc_demo/auth.py`: bearer token validation against Keycloak JWKS
- `app/n10_api_oidc_demo/keycloak.py`: broker token fetch, IRI-scope token extraction, and IRI API call
- `app/n10_api_oidc_demo/config.py`: environment-driven application settings
- `app/templates/`: single-page frontend and silent SSO helper
- `app/static/keycloak.js`: vendored Keycloak JavaScript adapter
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
  -n api-oidc-demo \
  --create-namespace \
  --set ingress.enabled=true \
  --set image.repository=ghcr.io/dingp/api-oidc-demo \
  --set app.keycloakBaseUrl='https://oidc.lbl-b59.org' \
  --set app.keycloakRealm='amsc' \
  --set app.keycloakClientId='api-oidc-demo'
```

If you expose the app publicly, make sure the Keycloak client allows the final redirect URI and web origin.

## Keycloak Configuration Requirements

The Keycloak client and broker setup are documented in `KEYCLOAK_CLIENT_SETUP.md`. The important requirements are:

- realm `amsc`
- client `api-oidc-demo`
- broker alias `globus`
- `Store Tokens` enabled on the `globus` identity provider
- `Stored Tokens Readable` enabled on the `globus` identity provider
- `broker` client role `read-token` effectively granted to the authenticated user
- an audience mapper that adds `api-oidc-demo` to the access token `aud` claim when audience verification is enabled

## Runtime Notes

- The frontend sends the Keycloak access token to the backend.
- The backend calls the Keycloak broker token endpoint with that access token.
- The backend searches the broker token payload for a Globus access token with scope `https://auth.globus.org/scopes/ed3e577d-f7f3-4639-b96e-ff5a8445d699/iri_api`.
- That extracted token is then used to call the IRI API endpoint `https://api.iri.nersc.gov/api/v1/account/projects`.

## Current Deployment Notes

The live demo currently runs in namespace `api-oidc-demo` on the development cluster and exposes these hosts:

- `app-oidc-demo.lbl-b59.org`
- `app.api-oidc-demo.development.svc.spin.nersc.org`

## Notes

- The app validates Keycloak JWTs locally using the realm JWKS.
- If Keycloak access tokens do not contain the correct audience, either add the audience mapper or disable audience verification for the demo.
- The broker token payload shape can vary, so the app checks both `other_tokens` and `bearer_token.other_tokens` when extracting the scoped Globus token.
