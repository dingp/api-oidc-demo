# Keycloak Design for Demo 2

This document describes a Keycloak-side design for a second demo application with:

- multiple API endpoints
- different claims driven by requested scopes
- three access tiers
- different token lifetime rules by tier

The design below assumes:

- Keycloak URL: `https://oidc.lbl-b59.org`
- Realm: `amsc`
- API resource name: `api-oidc-demo-2-api`
- Tier 1 browser client: `api-oidc-demo-2-tier1`
- Tier 2 browser client: `api-oidc-demo-2-tier2`
- Tier 3 browser client: `api-oidc-demo-2-tier3`

## What Keycloak Can And Cannot Do

Keycloak can do all of the following:

- issue different claims based on requested client scopes
- gate scopes by client choice
- gate higher-privilege access by user or group role assignment
- set different token and session lifetimes per client

Keycloak does not natively support one browser client whose token lifetime changes based on which optional scopes were requested in that login.

Because of that, the clean design is:

- one API resource client: `api-oidc-demo-2-api`
- one tier-1 login client: `api-oidc-demo-2-tier1`
- one tier-2 login client: `api-oidc-demo-2-tier2`
- one tier-3 login client: `api-oidc-demo-2-tier3`

This gives you:

- tier 1: readonly scopes, available to all users, `4 hours` access token, `7 days` refresh/session bound
- tier 2: full scopes, available to all users, `2 hours` access token, `2 days` refresh/session bound
- tier 3: same scopes as tier 2, available only to selected users, longer lifetime

## Revised Access Model

The model is intentionally hybrid.

- tier 1 is selected by client choice
- tier 2 is selected by client choice
- tier 3 is selected by client choice and additionally gated by a user or group role assignment

That means:

- any user may authenticate with `api-oidc-demo-2-tier1`
- any user may authenticate with `api-oidc-demo-2-tier2`
- only selected users may authenticate successfully with `api-oidc-demo-2-tier3`

For authorization inside the API, the simplest and most predictable approach is to enforce the `scope` claim directly.

## Proposed Endpoint And Scope Model

Use four demo endpoints:

- `GET /api/demo2/projects`
- `GET /api/demo2/reports`
- `GET /api/demo2/users`
- `PUT /api/demo2/preferences`

Use four optional OIDC client scopes:

- `demo2.projects.read`
- `demo2.reports.read`
- `demo2.users.read`
- `demo2.users.write`

Map them to endpoint authorization like this:

- `GET /api/demo2/projects` requires `demo2.projects.read`
- `GET /api/demo2/reports` requires `demo2.reports.read`
- `GET /api/demo2/users` requires `demo2.users.read`
- `PUT /api/demo2/preferences` requires `demo2.users.write`

## Why Scope-Based API Authorization Is Better Here

If every user can choose tier 1 or tier 2, then endpoint permissions are really driven by:

- which client the user chose
- which scopes that client can request

That makes the `scope` claim the most direct thing for the API to validate.

The backend can still validate `aud`, issuer, signature, expiration, and other standard JWT fields, but for endpoint authorization it should check the granted scopes.

## Proposed Clients

### API Resource Client

Create a client named `api-oidc-demo-2-api`.

Purpose:

- represents the protected API as a resource server
- provides the audience value checked by the backend
- optionally holds client roles if you want them later, but they are not required for the initial demo

Recommended settings:

- `Client type`: `OpenID Connect`
- `Client authentication`: `Off`
- `Authorization`: `Off`
- `Standard flow`: `Off`
- `Direct access grants`: `Off`
- `Service accounts roles`: `Off`

### Tier 1 Browser Client

Create client `api-oidc-demo-2-tier1`.

Purpose:

- readonly token
- available to all users
- 4-hour access token
- 7-day refresh/session bound

Attach only readonly optional scopes to this client.

### Tier 2 Browser Client

Create client `api-oidc-demo-2-tier2`.

Purpose:

- full-access token
- available to all users
- 2-hour access token
- 2-day refresh/session bound

Attach all demo scopes to this client.

### Tier 3 Browser Client

Create client `api-oidc-demo-2-tier3`.

Purpose:

- full-access token
- same scopes as tier 2
- longer token lifetime
- available only to selected users

Attach the same demo scopes as tier 2 to this client.

Then gate this client with a user or group role so only selected users may use it.

## Proposed Tier Lifetimes

### Tier 1

On `api-oidc-demo-2-tier1` set:

- `Access Token Lifespan`: `4 hours`
- `Client Session Idle`: `7 days`
- `Client Session Max`: `7 days`

### Tier 2

On `api-oidc-demo-2-tier2` set:

- `Access Token Lifespan`: `2 hours`
- `Client Session Idle`: `2 days`
- `Client Session Max`: `2 days`

### Tier 3

Tier 3 is the same scope set as tier 2, but with a longer lifetime.

A reasonable starting point is:

- `Access Token Lifespan`: `8 hours`
- `Client Session Idle`: `7 days`
- `Client Session Max`: `7 days`

If you want different numbers, change them at the client level without changing the rest of the model.

### Realm Lifetime Prerequisites

The realm settings must not be shorter than the longest client overrides.

In realm `amsc`, make sure:

- `SSO Session Idle` is greater than or equal to `7 days`
- `SSO Session Max` is greater than or equal to `7 days`

If the realm values are shorter, they override the client settings.

## Audience Recommendation

If the API validates the `aud` claim, add `api-oidc-demo-2-api` as an audience to all three browser clients.

Create a shared audience client scope:

- `api-oidc-demo-2-audience`

Add an audience mapper:

- `Name`: `aud-api-oidc-demo-2-api`
- `Included Client Audience`: `api-oidc-demo-2-api`
- `Add to access token`: `On`
- `Add to ID token`: `Off`
- `Add to token introspection`: `On`

Attach that client scope as a default scope to tier 1, tier 2, and tier 3.

## Requested Scope Examples

Tier 1 login request:

```text
openid profile demo2.projects.read demo2.reports.read demo2.users.read
```

Tier 2 login request:

```text
openid profile demo2.projects.read demo2.reports.read demo2.users.read demo2.users.write
```

Tier 3 login request:

```text
openid profile demo2.projects.read demo2.reports.read demo2.users.read demo2.users.write
```

Tier 2 and tier 3 have the same scopes. They differ only in:

- client identity
- lifetime policy
- who is allowed to use the client

## How To Restrict Tier 3 To Selected Users

Use a realm role specifically for tier-3 eligibility.

Recommended realm role name:

- `api-oidc-demo-2-tier3-eligible`

Assign that role only to selected users or groups.

Then configure the browser authentication flow so tier-3 logins are denied unless the user has that role.

Use this practical rule:

- tier 1 client: no special user role required
- tier 2 client: no special user role required
- tier 3 client: user must have realm role `api-oidc-demo-2-tier3-eligible`

The recommended enforcement pattern is:

- create a dedicated client scope named `demo2.tier3`
- attach `demo2.tier3` as a default client scope only to client `api-oidc-demo-2-tier3`
- add a conditional subflow to the browser authentication flow
- in that subflow, check for client scope `demo2.tier3`
- if that scope is present, check whether the user has realm role `api-oidc-demo-2-tier3-eligible`
- if the user does not have that role, deny access with a clear error message

This pattern is based on Keycloak's built-in conditional authenticators:

- `Condition - client scope`
- `Condition - User Role`
- `Deny Access`

## Concrete Naming Plan For The Demo

### Proposed Clients

Use these exact client IDs:

- API resource client: `api-oidc-demo-2-api`
- Tier 1 browser client: `api-oidc-demo-2-tier1`
- Tier 2 browser client: `api-oidc-demo-2-tier2`
- Tier 3 browser client: `api-oidc-demo-2-tier3`

### Proposed API Endpoints

Use four demo endpoints:

- `GET /api/demo2/projects`
- `GET /api/demo2/reports`
- `GET /api/demo2/users`
- `PUT /api/demo2/preferences`

### Proposed Optional Client Scopes

Create these client scopes:

- `demo2.projects.read`
- `demo2.reports.read`
- `demo2.users.read`
- `demo2.users.write`

These map directly to endpoint authorization checks:

- `GET /api/demo2/projects` -> `demo2.projects.read`
- `GET /api/demo2/reports` -> `demo2.reports.read`
- `GET /api/demo2/users` -> `demo2.users.read`
- `PUT /api/demo2/preferences` -> `demo2.users.write`

### Proposed Tier-3 Eligibility Role

Create this realm role:

- `api-oidc-demo-2-tier3-eligible`

Assign it only to selected users or groups.

### Proposed Browser Client Scope Attachments

For `api-oidc-demo-2-tier1`, attach these as optional client scopes:

- `demo2.projects.read`
- `demo2.reports.read`
- `demo2.users.read`

Do not attach `demo2.users.write` to tier 1.

For `api-oidc-demo-2-tier2`, attach these as optional client scopes:

- `demo2.projects.read`
- `demo2.reports.read`
- `demo2.users.read`
- `demo2.users.write`

For `api-oidc-demo-2-tier3`, attach these as optional client scopes:

- `demo2.projects.read`
- `demo2.reports.read`
- `demo2.users.read`
- `demo2.users.write`

### Proposed Token Lifetime Settings

For `api-oidc-demo-2-tier1`:

- `Access Token Lifespan`: `4 hours`
- `Client Session Idle`: `7 days`
- `Client Session Max`: `7 days`

For `api-oidc-demo-2-tier2`:

- `Access Token Lifespan`: `2 hours`
- `Client Session Idle`: `2 days`
- `Client Session Max`: `2 days`

For `api-oidc-demo-2-tier3`:

- `Access Token Lifespan`: `8 hours`
- `Client Session Idle`: `7 days`
- `Client Session Max`: `7 days`

### Recommended API Authorization Checks

The API server should authorize against the space-delimited `scope` claim.

Expected checks:

- `GET /api/demo2/projects` requires `demo2.projects.read`
- `GET /api/demo2/reports` requires `demo2.reports.read`
- `GET /api/demo2/users` requires `demo2.users.read`
- `PUT /api/demo2/preferences` requires `demo2.users.write`

### Recommended Frontend Choice Model

Expose three login choices:

- `Login Tier 1`
- `Login Tier 2`
- `Login Tier 3`

Behavior:

- tier 1 requests the tier-1 client with readonly scopes
- tier 2 requests the tier-2 client with full scopes
- tier 3 requests the tier-3 client with full scopes

If a user is not tier-3 eligible, the tier-3 path should fail clearly at login or result in no usable elevated session.

## Click-By-Click Keycloak Admin Recipe

The steps below assume Keycloak admin console at `https://oidc.lbl-b59.org/admin/` and realm `amsc`.

## 1. Create The API Resource Client

1. Sign in to the admin console.
2. Switch to realm `amsc`.
3. Click `Clients`.
4. Click `Create client`.
5. Set `Client type` to `OpenID Connect`.
6. Set `Client ID` to `api-oidc-demo-2-api`.
7. Click `Next`.
8. Set:
   - `Client authentication`: `Off`
   - `Authorization`: `Off`
   - `Standard flow`: `Off`
   - `Direct access grants`: `Off`
   - `Service accounts roles`: `Off`
9. Click `Save`.

## 2. Create The Optional Client Scopes

Create four client scopes.

For each scope:

1. Click `Client scopes`.
2. Click `Create client scope`.
3. Set:
   - `Name`: one of `demo2.projects.read`, `demo2.reports.read`, `demo2.users.read`, `demo2.users.write`
   - `Protocol`: `openid-connect`
4. Click `Save`.

## 3. Create The Shared Audience Scope

1. Click `Client scopes`.
2. Click `Create client scope`.
3. Set:
   - `Name`: `api-oidc-demo-2-audience`
   - `Protocol`: `openid-connect`
4. Click `Save`.
5. Open `api-oidc-demo-2-audience`.
6. Go to `Mappers`.
7. Click `Add mapper`.
8. Choose `Audience`.
9. Set:
   - `Name`: `aud-api-oidc-demo-2-api`
   - `Included Client Audience`: `api-oidc-demo-2-api`
   - `Add to access token`: `On`
   - `Add to ID token`: `Off`
   - `Add to token introspection`: `On`
10. Save.

## 4. Create The Tier 1 Browser Client

1. Click `Clients`.
2. Click `Create client`.
3. Set:
   - `Client type`: `OpenID Connect`
   - `Client ID`: `api-oidc-demo-2-tier1`
4. Click `Next`.
5. Set:
   - `Client authentication`: `Off`
   - `Authorization`: `Off`
   - `Standard flow`: `On`
   - `Implicit flow`: `Off`
   - `Direct access grants`: `Off`
   - `Service accounts roles`: `Off`
6. Click `Save`.
7. Set frontend URLs:
   - `Root URL`
   - `Home URL`
   - `Valid redirect URIs`
   - `Valid post logout redirect URIs`
   - `Web origins`
8. Save.
9. Go to `Client scopes`.
10. Verify built-in `roles` is present as a default scope if you still want role claims in tokens.
11. Add `api-oidc-demo-2-audience` as a `Default` scope.
12. Add these as `Optional` scopes:
   - `demo2.projects.read`
   - `demo2.reports.read`
   - `demo2.users.read`
13. Save.

## 5. Create The Tier 2 Browser Client

1. Click `Clients`.
2. Click `Create client`.
3. Set:
   - `Client type`: `OpenID Connect`
   - `Client ID`: `api-oidc-demo-2-tier2`
4. Click `Next`.
5. Set:
   - `Client authentication`: `Off`
   - `Authorization`: `Off`
   - `Standard flow`: `On`
   - `Implicit flow`: `Off`
   - `Direct access grants`: `Off`
   - `Service accounts roles`: `Off`
6. Click `Save`.
7. Set frontend URLs.
8. Save.
9. Go to `Client scopes`.
10. Add `api-oidc-demo-2-audience` as a `Default` scope.
11. Add these as `Optional` scopes:
   - `demo2.projects.read`
   - `demo2.reports.read`
   - `demo2.users.read`
   - `demo2.users.write`
12. Save.

## 6. Create The Tier 3 Eligibility Role

1. Click `Realm roles`.
2. Click `Create role`.
3. Set role name to `api-oidc-demo-2-tier3-eligible`.
4. Save.

## 7. Create The Tier 3 Marker Scope

Create a marker scope used only for browser-flow enforcement.

1. Click `Client scopes`.
2. Click `Create client scope`.
3. Set:
   - `Name`: `demo2.tier3`
   - `Protocol`: `openid-connect`
4. Leave it with no role scope mappings.
5. Keep `Include in token scope` enabled if you want it visible in the token, or disable it if you want it to be only an internal enforcement marker.
6. Click `Save`.

## 8. Create The Tier 3 Browser Client

1. Click `Clients`.
2. Click `Create client`.
3. Set:
   - `Client type`: `OpenID Connect`
   - `Client ID`: `api-oidc-demo-2-tier3`
4. Click `Next`.
5. Set:
   - `Client authentication`: `Off`
   - `Authorization`: `Off`
   - `Standard flow`: `On`
   - `Implicit flow`: `Off`
   - `Direct access grants`: `Off`
   - `Service accounts roles`: `Off`
6. Click `Save`.
7. Set frontend URLs.
8. Save.
9. Go to `Client scopes`.
10. Add `api-oidc-demo-2-audience` as a `Default` scope.
11. Add these as `Optional` scopes:
   - `demo2.projects.read`
   - `demo2.reports.read`
   - `demo2.users.read`
   - `demo2.users.write`
12. Save.

## 9. Configure Tier Lifetimes

For `api-oidc-demo-2-tier1`:

1. Open client `api-oidc-demo-2-tier1`.
2. Go to `Advanced`.
3. Set:
   - `Access Token Lifespan`: `4 hours`
   - `Client Session Idle`: `7 days`
   - `Client Session Max`: `7 days`
4. Save.

For `api-oidc-demo-2-tier2`:

1. Open client `api-oidc-demo-2-tier2`.
2. Go to `Advanced`.
3. Set:
   - `Access Token Lifespan`: `2 hours`
   - `Client Session Idle`: `2 days`
   - `Client Session Max`: `2 days`
4. Save.

For `api-oidc-demo-2-tier3`:

1. Open client `api-oidc-demo-2-tier3`.
2. Go to `Advanced`.
3. Set:
   - `Access Token Lifespan`: `8 hours`
   - `Client Session Idle`: `7 days`
   - `Client Session Max`: `7 days`
4. Save.

## 10. Verify Realm Token Settings

1. Click `Realm settings`.
2. Open `Tokens`.
3. Verify:
   - `SSO Session Idle` is at least `7 days`
   - `SSO Session Max` is at least `7 days`
4. Review `Revoke Refresh Token` if you want refresh-token rotation.
5. Save if needed.

## 11. Assign Tier-3 Eligibility To Selected Users Or Groups

Direct user assignment:

1. Click `Users`.
2. Open a selected user.
3. Go to `Role mapping`.
4. Click `Assign role`.
5. Select `api-oidc-demo-2-tier3-eligible`.
6. Click `Assign`.

Group assignment:

1. Click `Groups`.
2. Open the selected group.
3. Go to `Role mapping`.
4. Click `Assign role`.
5. Select `api-oidc-demo-2-tier3-eligible`.
6. Click `Assign`.

## 12. Restrict Tier 3 To The Eligibility Role

Use the built-in browser flow conditions documented by Keycloak.

The design goal is:

- only users with realm role `api-oidc-demo-2-tier3-eligible` may use client `api-oidc-demo-2-tier3`

Recommended enforcement recipe:

1. Open client `api-oidc-demo-2-tier3`.
2. Go to `Client scopes`.
3. Add `demo2.tier3` as a `Default` client scope.
4. Save.

Then create a browser flow copy:

1. Click `Authentication`.
2. Open the `Flows` tab.
3. Find the built-in `browser` flow.
4. Click `Actions` -> `Duplicate`.
5. Name the new flow `browser-demo2-tier3-gate`.
6. Open `browser-demo2-tier3-gate`.

Add a conditional subflow that runs after the user is identified. A practical placement is after the username/password step in the main browser flow.

1. In `browser-demo2-tier3-gate`, click `Add execution` or `Add sub-flow` at the level where the user has already been identified.
2. Create a `Conditional` subflow named `tier3-client-gate`.
3. Inside `tier3-client-gate`, add execution `Condition - client scope`.
4. Configure it with:
   - `Alias`: `if-tier3-client-scope`
   - `Client scope name`: `demo2.tier3`
   - `Negate output`: `Off`
5. Add execution `Condition - User Role`.
6. Configure it with:
   - `Alias`: `if-tier3-eligible-user`
   - `User role`: `api-oidc-demo-2-tier3-eligible`
7. Add execution `Allow Access`.
8. Add another sibling conditional subflow named `tier3-client-deny`.
9. Inside `tier3-client-deny`, add execution `Condition - client scope`.
10. Configure it with:
   - `Alias`: `if-tier3-client-scope-deny`
   - `Client scope name`: `demo2.tier3`
   - `Negate output`: `Off`
11. Add execution `Condition - User Role`.
12. Configure it with:
   - `Alias`: `if-not-tier3-eligible-user`
   - `User role`: `api-oidc-demo-2-tier3-eligible`
   - enable `Negate output` if your UI version offers it for this condition; if not, place this logic in a complementary flow structure so the deny branch is only reached when the allow branch is not satisfied.
13. Add execution `Deny Access`.
14. Configure `Deny Access` with an error message such as `You are not allowed to use tier 3`.

Set the realm browser flow:

1. Go to `Authentication` -> `Bindings`.
2. Set `Browser Flow` to `browser-demo2-tier3-gate`.
3. Save.

Why this works:

- Keycloak documents `Condition - client scope` for checking whether a client scope is present in the authentication request
- Keycloak documents `Condition - User Role` for checking whether the user has a required role
- Keycloak documents `Deny Access` for explicitly blocking the login in a conditional flow

This keeps tier-3 enforcement fully inside Keycloak and avoids putting the eligibility check in your application code.

## 13. Test The Result

For a regular user:

1. authenticate through `api-oidc-demo-2-tier1`
2. request readonly scopes
3. verify the token lifetime is about `4 hours`
4. verify the token contains readonly scopes only

Then:

1. authenticate through `api-oidc-demo-2-tier2`
2. request full scopes
3. verify the token lifetime is about `2 hours`
4. verify the token contains `demo2.users.write`

For a tier-3-eligible user:

1. authenticate through `api-oidc-demo-2-tier3`
2. request the same full scopes as tier 2
3. verify the token lifetime is about `8 hours`
4. verify the token contains the same scopes as tier 2

## Operational Notes

- tier 1 and tier 2 are session choices available to all users
- tier 3 is a privileged session choice available only to selected users
- the API should authorize using the `scope` claim
- the API should also validate issuer, signature, audience, and expiration as usual
- keeping tier 2 and tier 3 scope-identical but lifetime-different is exactly why separate clients are needed

## References

- <https://www.keycloak.org/docs/latest/server_admin/>
- <https://www.keycloak.org/securing-apps/javascript-adapter>
