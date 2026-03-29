from typing import Any

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from n10_api_oidc_demo.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


class TokenValidator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.jwks_client = PyJWKClient(
            settings.jwks_url,
            cache_keys=True,
            max_cached_keys=8,
        )

    def validate(self, token: str) -> dict[str, Any]:
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            options = {"verify_aud": self.settings.oidc_verify_audience}
            audience = self.settings.keycloak_client_id if self.settings.oidc_verify_audience else None
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "RS384", "RS512"],
                audience=audience,
                issuer=self.settings.issuer,
                options=options,
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {exc}",
            ) from exc

        if claims.get("typ") not in {None, "ID", "Bearer"}:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unsupported token type: {claims.get('typ')}",
            )

        return claims


def get_token_validator(settings: Settings = Depends(get_settings)) -> TokenValidator:
    return TokenValidator(settings)


def require_token_claims(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    validator: TokenValidator = Depends(get_token_validator),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    return validator.validate(credentials.credentials)
