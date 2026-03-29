from typing import Any

import httpx
from fastapi import HTTPException, status

from n10_api_oidc_demo.config import Settings


async def fetch_broker_token(settings: Settings, user_token: str) -> Any:
    headers = {"Authorization": f"Bearer {user_token}"}
    timeout = httpx.Timeout(15.0)

    async with httpx.AsyncClient(verify=settings.keycloak_verify_tls, timeout=timeout) as client:
        response = await client.get(settings.broker_token_url, headers=headers)

    if response.status_code == status.HTTP_200_OK:
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return {"raw": response.text}

    try:
        detail: Any = response.json()
    except ValueError:
        detail = response.text

    raise HTTPException(
        status_code=response.status_code,
        detail={
            "message": "Keycloak broker token request failed",
            "keycloak_response": detail,
        },
    )


def extract_scoped_access_token(broker_token: Any, scope: str) -> str:
    if not isinstance(broker_token, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected broker token payload format",
        )

    candidate_lists: list[list[Any]] = []

    top_level_other_tokens = broker_token.get("other_tokens", [])
    if isinstance(top_level_other_tokens, list):
        candidate_lists.append(top_level_other_tokens)

    bearer_token = broker_token.get("bearer_token", {})
    if isinstance(bearer_token, dict):
        nested_other_tokens = bearer_token.get("other_tokens", [])
        if isinstance(nested_other_tokens, list):
            candidate_lists.append(nested_other_tokens)

    for token_list in candidate_lists:
        for token_entry in token_list:
            if not isinstance(token_entry, dict):
                continue

            raw_scope = token_entry.get("scope", "")
            if isinstance(raw_scope, str):
                scopes = set(raw_scope.split())
            elif isinstance(raw_scope, list):
                scopes = {str(item) for item in raw_scope}
            else:
                scopes = set()

            if scope in scopes and token_entry.get("access_token"):
                return token_entry["access_token"]

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "message": "No matching external access token found in broker token payload",
            "required_scope": scope,
            "searched_locations": ["other_tokens", "bearer_token.other_tokens"],
        },
    )


async def fetch_iri_projects(settings: Settings, external_access_token: str) -> Any:
    headers = {"Authorization": f"Bearer {external_access_token}"}
    timeout = httpx.Timeout(20.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(settings.iri_projects_url, headers=headers)

    if response.status_code == status.HTTP_200_OK:
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return {"raw": response.text}

    try:
        detail: Any = response.json()
    except ValueError:
        detail = response.text

    raise HTTPException(
        status_code=response.status_code,
        detail={
            "message": "IRI projects API request failed",
            "iri_response": detail,
        },
    )
