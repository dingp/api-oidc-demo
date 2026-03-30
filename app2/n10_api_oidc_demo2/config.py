from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="N10 OIDC Demo 2", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    keycloak_base_url: str = Field(alias="KEYCLOAK_BASE_URL")
    keycloak_realm: str = Field(alias="KEYCLOAK_REALM")
    keycloak_verify_tls: bool = Field(default=True, alias="KEYCLOAK_VERIFY_TLS")
    trusted_proxy_cidrs: str = Field(default="10.42.0.0/16,127.0.0.1/32", alias="TRUSTED_PROXY_CIDRS")

    oidc_api_audience: str = Field(default="api-oidc-demo-2-api", alias="OIDC_API_AUDIENCE")
    oidc_verify_audience: bool = Field(default=True, alias="OIDC_VERIFY_AUDIENCE")

    tier1_client_id: str = Field(default="api-oidc-demo-2-tier1", alias="DEMO2_TIER1_CLIENT_ID")
    tier2_client_id: str = Field(default="api-oidc-demo-2-tier2", alias="DEMO2_TIER2_CLIENT_ID")
    tier3_client_id: str = Field(default="api-oidc-demo-2-tier3", alias="DEMO2_TIER3_CLIENT_ID")

    tier1_scopes: str = Field(
        default="openid profile demo2.projects.read demo2.reports.read demo2.users.read",
        alias="DEMO2_TIER1_SCOPES",
    )
    tier2_scopes: str = Field(
        default="openid profile demo2.projects.read demo2.reports.read demo2.users.read demo2.users.write",
        alias="DEMO2_TIER2_SCOPES",
    )
    tier3_scopes: str = Field(
        default="openid profile demo2.projects.read demo2.reports.read demo2.users.read demo2.users.write",
        alias="DEMO2_TIER3_SCOPES",
    )

    @property
    def issuer(self) -> str:
        return f"{self.keycloak_base_url.rstrip('/')}/realms/{self.keycloak_realm}"

    @property
    def jwks_url(self) -> str:
        return f"{self.issuer}/protocol/openid-connect/certs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
