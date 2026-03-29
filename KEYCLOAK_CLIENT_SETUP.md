# Keycloak Client Setup for `api-oidc-demo`

This guide describes the Keycloak configuration required for the demo application running at `https://app-oidc-demo.lbl-b59.org`.

## Environment

- Keycloak URL: `https://oidc.lbl-b59.org`
- Realm: `amsc`
- Application URL: `https://app-oidc-demo.lbl-b59.org`
- Broker alias: `globus`
- Client ID: `api-oidc-demo`

## 1. Create the client

1. Sign in to the Keycloak admin console at `https://oidc.lbl-b59.org/admin/`.
2. Switch to realm `amsc`.
3. Go to `Clients`.
4. Click `Create client`.
5. Set:
   - `Client type`: `OpenID Connect`
   - `Client ID`: `api-oidc-demo`
6. Save.

## 2. Configure client capabilities

For this browser-based demo, configure the client as a public OIDC client:

- `Client authentication`: `Off`
- `Authorization`: `Off`
- `Standard flow`: `On`
- `Implicit flow`: `Off`
- `Direct access grants`: `Off`
- `Service accounts roles`: `Off`

Save the client.

## 3. Configure login, redirect, and logout URLs

Set these values on the client settings page:

- `Root URL`: `https://app-oidc-demo.lbl-b59.org`
- `Home URL`: `https://app-oidc-demo.lbl-b59.org/`

`Valid redirect URIs` should include:

- `https://app-oidc-demo.lbl-b59.org`
- `https://app-oidc-demo.lbl-b59.org/`
- `https://app-oidc-demo.lbl-b59.org/*`
- `https://app-oidc-demo.lbl-b59.org/silent-check-sso.html`

`Valid post logout redirect URIs` should include:

- `https://app-oidc-demo.lbl-b59.org`
- `https://app-oidc-demo.lbl-b59.org/`
- optionally `https://app-oidc-demo.lbl-b59.org/*`

`Web origins` should include:

- `https://app-oidc-demo.lbl-b59.org`

Save the client.

## 4. Configure the `globus` identity provider

1. Go to `Identity Providers`.
2. Open the provider with alias `globus`.
3. Ensure these settings are enabled:
   - `Store Tokens`: `On`
   - `Stored Tokens Readable`: `On`
4. Save.

These are required because the backend retrieves the stored external Globus token from Keycloak.

## 5. Grant the broker `read-token` client role

The broker token endpoint requires permission to read stored external tokens.

Check the `broker` client roles in realm `amsc` and ensure `read-token` is effectively granted.

Practical requirement for this demo:

- the user session used against `/realms/amsc/broker/globus/token` must include the `broker` client role `read-token`

Verify this by:

1. Going to `Clients`.
2. Opening the built-in client `broker`.
3. Confirming the client role `read-token` exists.
4. Mapping that role so the authenticating user receives it, directly or via group/role mapping.

## 6. Add an audience mapper for `api-oidc-demo`

This demo validates Keycloak access tokens locally. If audience validation is enabled, the access token must include `api-oidc-demo` in the `aud` claim.

Add a hardcoded audience mapper:

1. Open client `api-oidc-demo`.
2. Go to `Client scopes`.
3. Pick the dedicated client scope for `api-oidc-demo`, or create and attach a custom client scope.
4. Open `Mappers`.
5. Click `Add mapper` or `Configure a new mapper`.
6. Choose `Audience`.
7. Set:
   - `Name`: `aud-api-oidc-demo`
   - `Included Client Audience`: `api-oidc-demo`
   - `Add to access token`: `On`
   - `Add to ID token`: `Off`
   - `Add to token introspection`: `On` if desired
8. Save.

After saving, log out and log back in so the new access token contains the updated audience.

## 7. Token usage in the demo

The backend expects the frontend to send a Keycloak access token, not an ID token.

Broker token endpoint:

`GET https://oidc.lbl-b59.org/realms/amsc/broker/globus/token`

Request header:

`Authorization: Bearer <keycloak-access-token>`

The backend then extracts the external Globus token from the broker-token payload and uses the token with scope:

`https://auth.globus.org/scopes/ed3e577d-f7f3-4639-b96e-ff5a8445d699/iri_api`

for this downstream API:

`GET https://api.iri.nersc.gov/api/v1/account/projects`

## 8. Useful OIDC endpoints

- Issuer: `https://oidc.lbl-b59.org/realms/amsc`
- JWKS: `https://oidc.lbl-b59.org/realms/amsc/protocol/openid-connect/certs`
- Broker token endpoint: `https://oidc.lbl-b59.org/realms/amsc/broker/globus/token`
- OIDC discovery: `https://oidc.lbl-b59.org/realms/amsc/.well-known/openid-configuration`

## 9. Application values to align

Make sure your app configuration uses:

- `KEYCLOAK_BASE_URL=https://oidc.lbl-b59.org`
- `KEYCLOAK_REALM=amsc`
- `KEYCLOAK_CLIENT_ID=api-oidc-demo`
- `KEYCLOAK_BROKER_ALIAS=globus`
- `IRI_PROJECTS_URL=https://api.iri.nersc.gov/api/v1/account/projects`
- `IRI_API_SCOPE=https://auth.globus.org/scopes/ed3e577d-f7f3-4639-b96e-ff5a8445d699/iri_api`

## References

- Keycloak JavaScript adapter: <https://www.keycloak.org/securing-apps/javascript-adapter>
- Keycloak OIDC layers and logout behavior: <https://www.keycloak.org/securing-apps/oidc-layers>
- Keycloak Server Administration Guide: <https://www.keycloak.org/docs/latest/server_admin/>
