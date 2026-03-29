# n10-api-oidc-demo Helm Chart

This chart installs the FastAPI Keycloak OIDC demo.

## Required values

Set these values for your environment before installing:

- `image.repository`
- `app.keycloakBaseUrl`
- `app.keycloakRealm`
- `app.keycloakClientId`
- `ingress.enabled` and `ingress.hosts` if you want external access

## Install

```bash
helm upgrade --install n10-api-oidc-demo helm/n10-api-oidc-demo \
  -n keycloak-demo \
  --create-namespace \
  --set image.repository=ghcr.io/<owner>/n10-api-oidc-demo \
  --set app.keycloakBaseUrl='https://keycloak.example.org' \
  --set app.keycloakRealm='demo' \
  --set app.keycloakClientId='demo-web'
```
