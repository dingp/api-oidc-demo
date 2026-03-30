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


## Multi-Flow Access

The API accepts bearer tokens from multiple authorization flows as long as the token has audience `api-oidc-demo-2-api` and the required scopes.

Recommended caller types:

- Web UI: Authorization Code with PKCE using tier clients
- CLI: Device Authorization Grant using client `api-oidc-demo-2-cli`
- Service automation: Client Credentials using client `api-oidc-demo-2-service`

### Device Flow Helper

A small helper script is available at `app2/scripts/device_flow.sh`.

Example:

```bash
app2/scripts/device_flow.sh   https://oidc.lbl-b59.org   amsc   api-oidc-demo-2-cli   "openid profile demo2.projects.read demo2.reports.read demo2.users.read"
```

After it returns an access token, you can call the API directly:

```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN"   http://localhost:8000/api/demo2/projects
```
