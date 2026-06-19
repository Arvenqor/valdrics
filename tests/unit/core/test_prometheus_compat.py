"""Unit tests for app.shared.core.prometheus_compat.

Validates that the monkey-patch for ``prometheus-fastapi-instrumentator``
correctly resolves templated route names when FastAPI ≥0.137 introduces
``_IncludedRouter`` objects that lack a ``.path`` attribute.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRouter
from starlette.types import Scope

from app.shared.core.prometheus_compat import (
    _get_route_name_patched,
    apply_instrumentator_patch,
)
import prometheus_fastapi_instrumentator.routing as _pfi_routing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_scope(path: str, method: str = "GET") -> Scope:
    """Create a minimal ASGI scope for route matching."""
    return {
        "type": "http",
        "method": method,
        "path": path,
        "path_params": {},
        "query_string": b"",
        "root_path": "",
        "headers": [],
    }


def _build_test_app() -> FastAPI:
    """Build a FastAPI app with mixed route types for testing."""
    app = FastAPI()

    # Direct route (standard Route object)
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # Included router → creates _IncludedRouter on FastAPI ≥0.137
    api_router = APIRouter()

    @api_router.get("/items")
    async def list_items() -> list[dict[str, str]]:
        return []

    @api_router.get("/items/{item_id}")
    async def get_item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    @api_router.post("/items")
    async def create_item() -> dict[str, str]:
        return {"created": "true"}

    app.include_router(api_router, prefix="/api/v1")

    # Nested router
    nested = APIRouter()

    @nested.get("/status")
    async def nested_status() -> dict[str, str]:
        return {"nested": "ok"}

    inner = APIRouter()

    @inner.get("/deep")
    async def deep() -> dict[str, str]:
        return {"deep": "ok"}

    nested.include_router(inner, prefix="/inner")
    app.include_router(nested, prefix="/nested")

    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetRouteNamePatched:
    """Tests for the patched route name resolution function."""

    @pytest.fixture(autouse=True)
    def _app(self) -> FastAPI:
        self.app = _build_test_app()
        return self.app

    def test_standard_route_resolution(self) -> None:
        """Standard Route objects (e.g. /health) resolve normally."""
        scope = _make_scope("/health")
        result = _get_route_name_patched(scope, self.app.routes)
        assert result == "/health"

    def test_included_router_exact_match(self) -> None:
        """_IncludedRouter resolves exact paths correctly."""
        scope = _make_scope("/api/v1/items")
        result = _get_route_name_patched(scope, self.app.routes)
        assert result == "/api/v1/items"

    def test_included_router_templated_path(self) -> None:
        """_IncludedRouter resolves templated paths with path params."""
        scope = _make_scope("/api/v1/items/42")
        result = _get_route_name_patched(scope, self.app.routes)
        assert result == "/api/v1/items/{item_id}"

    def test_unmatched_path_returns_none(self) -> None:
        """Non-existent paths return None."""
        scope = _make_scope("/does/not/exist")
        result = _get_route_name_patched(scope, self.app.routes)
        assert result is None

    def test_nested_included_router(self) -> None:
        """Nested _IncludedRouter chains resolve correctly."""
        scope = _make_scope("/nested/status")
        result = _get_route_name_patched(scope, self.app.routes)
        assert result == "/nested/status"

    def test_no_attribute_error_on_included_router(self) -> None:
        """Confirm no AttributeError on routes lacking .path attribute."""
        has_pathless_route = any(
            not hasattr(route, "path") for route in self.app.routes
        )
        assert has_pathless_route, (
            "Test app should have at least one _IncludedRouter without .path"
        )

        # Exercise ALL routes through the patched function — must not raise.
        for path in ["/health", "/api/v1/items", "/api/v1/items/99", "/nested/status"]:
            scope = _make_scope(path)
            _get_route_name_patched(scope, self.app.routes)

    def test_post_method_resolution(self) -> None:
        """POST methods resolve the same templated path as GET."""
        scope = _make_scope("/api/v1/items", method="POST")
        result = _get_route_name_patched(scope, self.app.routes)
        assert result == "/api/v1/items"


class TestApplyInstrumentatorPatch:
    """Tests for the idempotent monkey-patch application."""

    def test_patch_is_applied(self) -> None:
        """After calling apply_instrumentator_patch, the routing module is patched."""
        apply_instrumentator_patch()
        assert getattr(_pfi_routing, "_VALDRICS_PATCHED", False) is True
        assert _pfi_routing._get_route_name is _get_route_name_patched

    def test_patch_is_idempotent(self) -> None:
        """Calling apply_instrumentator_patch twice does not error."""
        apply_instrumentator_patch()
        apply_instrumentator_patch()
        assert _pfi_routing._get_route_name is _get_route_name_patched

    def test_original_is_preserved(self) -> None:
        """The original function is saved for reference."""
        apply_instrumentator_patch()
        assert hasattr(_pfi_routing, "_original_get_route_name")
        assert callable(_pfi_routing._original_get_route_name)
