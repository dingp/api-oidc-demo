from pathlib import Path

from fastapi import Depends, FastAPI, Header, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from n10_api_oidc_demo.auth import require_token_claims
from n10_api_oidc_demo.config import Settings, get_settings
from n10_api_oidc_demo.keycloak import fetch_broker_token

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request, settings: Settings = Depends(get_settings)) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "app_name": settings.app_name,
                "keycloak_base_url": settings.keycloak_base_url.rstrip("/"),
                "keycloak_realm": settings.keycloak_realm,
                "keycloak_client_id": settings.keycloak_client_id,
                "broker_alias": settings.keycloak_broker_alias,
            },
        )

    @app.get("/silent-check-sso.html", response_class=HTMLResponse)
    async def silent_check_sso(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request=request, name="silent-check-sso.html", context={})

    @app.get("/api/health")
    async def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
        return {
            "status": "ok",
            "realm": settings.keycloak_realm,
            "broker_alias": settings.keycloak_broker_alias,
        }

    @app.get("/api/me")
    async def me(claims: dict = Depends(require_token_claims)) -> dict:
        return {
            "authenticated": True,
            "claims": claims,
        }

    @app.get("/api/keycloak/globus-token")
    async def globus_token(
        claims: dict = Depends(require_token_claims),
        authorization: str | None = Header(default=None),
        settings: Settings = Depends(get_settings),
    ) -> dict:
        if not authorization:
            return {"claims": claims, "broker_token": None, "warning": "Missing Authorization header"}

        user_token = authorization.removeprefix("Bearer").strip()
        broker_token = await fetch_broker_token(settings, user_token)
        return {
            "claims": claims,
            "broker_alias": settings.keycloak_broker_alias,
            "broker_token": broker_token,
        }

    return app


app = create_app()
