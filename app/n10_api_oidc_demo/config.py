from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="N10 OIDC Demo", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    keycloak_base_url: str = Field(alias="KEYCLOAK_BASE_URL")
    keycloak_realm: str = Field(alias="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(alias="KEYCLOAK_CLIENT_ID")
    keycloak_broker_alias: str = Field(default="globus", alias="KEYCLOAK_BROKER_ALIAS")
    keycloak_verify_tls: bool = Field(default=True, alias="KEYCLOAK_VERIFY_TLS")

    oidc_verify_audience: bool = Field(default=True, alias="OIDC_VERIFY_AUDIENCE")

    iri_projects_url: str = Field(
        default="https://api.iri.nersc.gov/api/v1/account/projects",
        alias="IRI_PROJECTS_URL",
    )
    iri_api_scope: str = Field(
        default="https://auth.globus.org/scopes/ed3e577d-f7f3-4639-b96e-ff5a8445d699/iri_api",
        alias="IRI_API_SCOPE",
    )

    @property
    def issuer(self) -> str:
        return f"{self.keycloak_base_url.rstrip('/')}/realms/{self.keycloak_realm}"

    @property
    def jwks_url(self) -> str:
        return f"{self.issuer}/protocol/openid-connect/certs"

    @property
    def broker_token_url(self) -> str:
        return f"{self.issuer}/broker/{self.keycloak_broker_alias}/token"


@lru_cache
def get_settings() -> Settings:
    return Settings()
