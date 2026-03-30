from ipaddress import ip_address, ip_network
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from n10_api_oidc_demo2.auth import parse_scope_set, require_scopes, require_token_claims
from n10_api_oidc_demo2.config import Settings, get_settings

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

PROJECTS = [
    {"id": "proj-001", "name": "Exascale Demo", "status": "active"},
    {"id": "proj-002", "name": "Data Broker", "status": "planned"},
]
REPORTS = [
    {"id": "rpt-2026-03", "title": "Quarterly Access Review", "state": "published"},
    {"id": "rpt-2026-04", "title": "Usage Forecast", "state": "draft"},
]
USERS = [
    {"username": "alice", "display_name": "Alice Example", "role": "reader"},
    {"username": "bob", "display_name": "Bob Example", "role": "operator"},
]
PREFERENCES = {
    "theme": "teal",
    "page_size": 25,
    "email_notifications": False,
}
IP_POLICIES: dict[str, list[str]] = {}


class DemoPreferenceUpdate(BaseModel):
    theme: str = "teal"
    page_size: int = 25
    email_notifications: bool = False


class IpPolicyUpdate(BaseModel):
    allowed_ranges: list[str] = Field(default_factory=list)


def get_trusted_proxy_networks(settings: Settings) -> list:
    return [ip_network(item.strip(), strict=False) for item in settings.trusted_proxy_cidrs.split(",") if item.strip()]


def get_effective_client_ip(request: Request, settings: Settings) -> str:
    client_host = request.client.host if request.client else None
    if not client_host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine client IP address",
        )

    client_ip = ip_address(client_host)
    trusted_proxies = get_trusted_proxy_networks(settings)
    forwarded_for = request.headers.get("x-forwarded-for", "").strip()
    if forwarded_for and any(client_ip in network for network in trusted_proxies):
        first = forwarded_for.split(",", 1)[0].strip()
        if first:
            return first
    return client_host


def normalize_allowed_ranges(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        item = value.strip()
        if not item:
            continue
        try:
            normalized.append(str(ip_network(item, strict=False)))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Invalid IP range",
                    "value": item,
                },
            ) from exc
    return normalized


def get_subject(claims: dict) -> str:
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing subject",
        )
    return subject


def get_ip_policy_state(claims: dict, request: Request, settings: Settings) -> dict[str, object]:
    subject = get_subject(claims)
    request_ip = get_effective_client_ip(request, settings)
    allowed_ranges = IP_POLICIES.get(subject, [])
    return {
        "subject": subject,
        "request_ip": request_ip,
        "allowed_ranges": allowed_ranges,
        "enforced": bool(allowed_ranges),
    }


def enforce_ip_policy(claims: dict, request: Request, settings: Settings) -> dict[str, object]:
    state = get_ip_policy_state(claims, request, settings)
    allowed_ranges = state["allowed_ranges"]
    if not allowed_ranges:
        return state

    current_ip = ip_address(state["request_ip"])
    if any(current_ip in ip_network(cidr) for cidr in allowed_ranges):
        return state

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "message": "Request IP is outside the allowed ranges for this subject",
            "request_ip": state["request_ip"],
            "allowed_ranges": allowed_ranges,
        },
    )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request, settings: Settings = Depends(get_settings)) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "app_name": settings.app_name,
                "keycloak_base_url": settings.keycloak_base_url.rstrip("/"),
                "keycloak_realm": settings.keycloak_realm,
                "api_audience": settings.oidc_api_audience,
                "tier1_client_id": settings.tier1_client_id,
                "tier2_client_id": settings.tier2_client_id,
                "tier3_client_id": settings.tier3_client_id,
                "tier1_scopes": settings.tier1_scopes,
                "tier2_scopes": settings.tier2_scopes,
                "tier3_scopes": settings.tier3_scopes,
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
            "api_audience": settings.oidc_api_audience,
        }

    @app.get("/api/me")
    async def me(
        request: Request,
        claims: dict = Depends(require_token_claims),
        settings: Settings = Depends(get_settings),
    ) -> dict:
        return {
            "authenticated": True,
            "claims": claims,
            "scopes": sorted(parse_scope_set(claims)),
            "ip_policy": get_ip_policy_state(claims, request, settings),
        }

    @app.get("/api/demo2/ip-policy")
    async def read_ip_policy(
        request: Request,
        claims: dict = Depends(require_token_claims),
        settings: Settings = Depends(get_settings),
    ) -> dict:
        return {
            "endpoint": "ip_policy.read",
            "ip_policy": get_ip_policy_state(claims, request, settings),
        }

    @app.put("/api/demo2/ip-policy")
    async def update_ip_policy(
        payload: IpPolicyUpdate,
        request: Request,
        claims: dict = Depends(require_token_claims),
        settings: Settings = Depends(get_settings),
    ) -> dict:
        subject = get_subject(claims)
        normalized = normalize_allowed_ranges(payload.allowed_ranges)
        IP_POLICIES[subject] = normalized
        return {
            "endpoint": "ip_policy.update",
            "ip_policy": get_ip_policy_state(claims, request, settings),
        }

    @app.get("/api/demo2/projects")
    async def projects(request: Request, claims: dict = Depends(require_scopes("demo2.projects.read")),
        settings: Settings = Depends(get_settings)) -> dict:
        ip_policy = enforce_ip_policy(claims, request, settings)
        return {
            "endpoint": "projects",
            "required_scope": "demo2.projects.read",
            "scopes": sorted(parse_scope_set(claims)),
            "ip_policy": ip_policy,
            "items": PROJECTS,
        }

    @app.get("/api/demo2/reports")
    async def reports(request: Request, claims: dict = Depends(require_scopes("demo2.reports.read")),
        settings: Settings = Depends(get_settings)) -> dict:
        ip_policy = enforce_ip_policy(claims, request, settings)
        return {
            "endpoint": "reports",
            "required_scope": "demo2.reports.read",
            "scopes": sorted(parse_scope_set(claims)),
            "ip_policy": ip_policy,
            "items": REPORTS,
        }

    @app.get("/api/demo2/users")
    async def users(request: Request, claims: dict = Depends(require_scopes("demo2.users.read")),
        settings: Settings = Depends(get_settings)) -> dict:
        ip_policy = enforce_ip_policy(claims, request, settings)
        return {
            "endpoint": "users.list",
            "required_scope": "demo2.users.read",
            "scopes": sorted(parse_scope_set(claims)),
            "ip_policy": ip_policy,
            "items": USERS,
        }

    @app.put("/api/demo2/preferences")
    async def update_preferences(
        payload: DemoPreferenceUpdate,
        request: Request,
        claims: dict = Depends(require_scopes("demo2.users.write")),
        settings: Settings = Depends(get_settings),
    ) -> dict:
        ip_policy = enforce_ip_policy(claims, request, settings)
        updated = payload.model_dump()
        PREFERENCES.update(updated)
        return {
            "endpoint": "preferences.update",
            "required_scope": "demo2.users.write",
            "scopes": sorted(parse_scope_set(claims)),
            "ip_policy": ip_policy,
            "preferences": PREFERENCES,
        }

    return app


app = create_app()
