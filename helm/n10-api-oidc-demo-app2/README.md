# n10-api-oidc-demo-app2

Helm chart for the second OIDC demo application under `app2/`.

This chart installs only the application Deployment and Service. It does not create an Ingress. The intended flow is:

1. install a separate ingress and certificate chart such as `helm/tls-acme`
2. obtain TLS certificates first
3. update that ingress to point at the `app2` Service created by this chart

## Default image

- `ghcr.io/dingp/api-oidc-demo-app2:latest`

## Install

```bash
helm upgrade --install n10-api-oidc-demo-app2 helm/n10-api-oidc-demo-app2   -n api-oidc-demo-app2   --create-namespace   --set image.repository=ghcr.io/dingp/api-oidc-demo-app2   --set app.keycloakBaseUrl='https://oidc.lbl-b59.org'   --set app.keycloakRealm='amsc'
```
