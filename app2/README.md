# App 2

This subdirectory contains the second OIDC demo app.

## Behavior

- three Keycloak browser clients: tier 1, tier 2, tier 3
- validates access tokens against the realm JWKS
- checks the `scope` claim for API authorization
- lets the authenticated user set allowed IP ranges for their own subject
- enforces those CIDR ranges on protected demo endpoints
- demo endpoints:
  - `GET /api/demo2/projects`
  - `GET /api/demo2/reports`
  - `GET /api/demo2/users`
  - `PUT /api/demo2/preferences`
  - `GET /api/demo2/ip-policy`
  - `PUT /api/demo2/ip-policy`

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app2/requirements.txt
cp app2/.env.example .env
uvicorn n10_api_oidc_demo2.main:app --app-dir app2 --reload --host 0.0.0.0 --port 8000
```

## Proxy Trust

In the development cluster, ingress-nginx pods are on `10.42.0.0/16`, so the app trusts `X-Forwarded-For` only when the immediate peer is in `TRUSTED_PROXY_CIDRS=10.42.0.0/16,127.0.0.1/32`.
