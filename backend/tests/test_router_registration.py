"""Every router module under backend/api must be mounted by create_app().

Routers used to be imported behind ``try/except ImportError`` and could drop
out of the application silently. This guard makes an unmounted router a
test failure.
"""

import importlib
import pkgutil

from fastapi import APIRouter
from fastapi.routing import APIRoute

import backend.api as api_package
from backend.app.server import create_app

# Routers that exist on disk but are deliberately not mounted yet. Each entry
# must name the issue that mounts it; remove the entry in that PR.
NOT_YET_MOUNTED: dict[str, str] = {}


def _router_modules() -> list[tuple[str, APIRouter]]:
    found = []
    for info in pkgutil.iter_modules(api_package.__path__):
        if info.ispkg:
            continue
        module = importlib.import_module(f"backend.api.{info.name}")
        router = getattr(module, "router", None)
        if isinstance(router, APIRouter):
            found.append((info.name, router))
    assert found, "no routers discovered under backend/api"
    return found


def _mounted(app) -> set[tuple[str, str]]:
    """Every served ``(path, METHOD)``, read from the OpenAPI schema.

    ``app.routes`` is not used: newer FastAPI versions keep an included router
    as one wrapper entry instead of copying its routes onto the application.
    """
    return {(path, method.upper()) for path, operations in app.openapi()["paths"].items() for method in operations}


def test_every_api_router_is_mounted() -> None:
    mounted = _mounted(create_app())
    missing: dict[str, list[str]] = {}
    for name, router in _router_modules():
        if name in NOT_YET_MOUNTED:
            continue
        for route in router.routes:
            if not isinstance(route, APIRoute) or not route.include_in_schema:
                continue
            if any((route.path, method) not in mounted for method in route.methods):
                missing.setdefault(name, []).append(route.path)
    assert not missing, f"routers with unmounted routes: {missing}"


def test_not_yet_mounted_list_is_current() -> None:
    mounted_paths = {path for path, _ in _mounted(create_app())}
    for name in NOT_YET_MOUNTED:
        module = importlib.import_module(f"backend.api.{name}")
        paths = [r.path for r in module.router.routes if isinstance(r, APIRoute)]
        assert paths, f"{name} has no routes"
        assert not any(p in mounted_paths for p in paths), f"{name} is mounted; remove it from NOT_YET_MOUNTED"


def test_health_route_is_served(client) -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
