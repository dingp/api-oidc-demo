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
