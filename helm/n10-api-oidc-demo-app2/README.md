# n10-api-oidc-demo-app2

Helm chart for the second OIDC demo application under `app2/`.

## Default image

- `ghcr.io/dingp/api-oidc-demo-app2:latest`

## Install

```bash
helm upgrade --install n10-api-oidc-demo-app2 helm/n10-api-oidc-demo-app2   -n api-oidc-demo-app2   --create-namespace   --set ingress.enabled=true   --set image.repository=ghcr.io/dingp/api-oidc-demo-app2   --set app.keycloakBaseUrl='https://oidc.lbl-b59.org'   --set app.keycloakRealm='amsc'
```
