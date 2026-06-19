"""Compatibility shim for prometheus-fastapi-instrumentator with FastAPI ≥0.137.

FastAPI 0.137 replaced the flat list of ``APIRoute`` objects produced by
``include_router()`` with a deferred ``_IncludedRouter`` wrapper.  These objects
expose ``matches()`` and ``include_context`` but lack a ``.path`` attribute,
which causes an ``AttributeError`` in the upstream
``prometheus_fastapi_instrumentator.routing._get_route_name`` function.

This module **monkey-patches** that function to gracefully handle both the old
``Route``/``Mount`` types *and* the newer ``_IncludedRouter`` type so that
Prometheus metrics continue to group requests by their templated path.

**Import this module before calling** ``Instrumentator().instrument(app)``.

References
----------
- https://github.com/trallnag/prometheus-fastapi-instrumentator/issues/XXX
- FastAPI 0.137 changelog: ``_IncludedRouter`` introduced.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from starlette.routing import Match, Mount, Route
from starlette.types import Scope

import prometheus_fastapi_instrumentator.routing as _pfi_routing

logger = logging.getLogger(__name__)


def _get_route_name_patched(
    scope: Scope,
    routes: List[Route],
    route_name: Optional[str] = None,
) -> Optional[str]:
    """Drop-in replacement for ``_pfi_routing._get_route_name``.

    Handles three route types:
    1. ``Route`` / ``APIRoute`` – has ``.path`` and ``.matches()``.
    2. ``Mount`` – has ``.path``, ``.routes``, and ``.matches()``.
    3. ``_IncludedRouter`` (FastAPI ≥ 0.137) – has ``.matches()`` and
       ``.include_context.prefix`` but **no** ``.path``.  Sub-routes live in
       ``.original_router.routes``.
    """

    for route in routes:
        match, child_scope = route.matches(scope)

        if match == Match.FULL:
            if hasattr(route, "path"):
                # Standard Route / Mount path
                route_name = route.path
                child_scope = {**scope, **child_scope}

                if isinstance(route, Mount) and route.routes:
                    child_route_name = _get_route_name_patched(
                        child_scope, route.routes, route_name
                    )
                    if child_route_name is None:
                        route_name = None
                    else:
                        route_name += child_route_name
                return route_name

            # FastAPI ≥ 0.137 _IncludedRouter: resolve prefix + recurse.
            include_ctx = getattr(route, "include_context", None)
            prefix: str = getattr(include_ctx, "prefix", "") or ""
            original_router = getattr(route, "original_router", None)
            sub_routes = getattr(original_router, "routes", None)

            if sub_routes:
                inner_scope = dict(scope)
                current_path: str = inner_scope.get("path", "")
                if prefix and current_path.startswith(prefix):
                    inner_scope["path"] = current_path[len(prefix) :] or "/"

                child_route_name = _get_route_name_patched(inner_scope, sub_routes)
                if child_route_name is not None:
                    return prefix + child_route_name

            # Fallback: use prefix alone (still better than crashing).
            return prefix or scope.get("path", "")

        elif match == Match.PARTIAL and route_name is None:
            if hasattr(route, "path"):
                route_name = route.path

    return None


def apply_instrumentator_patch() -> None:
    """Apply the monkey-patch.  Idempotent – safe to call multiple times."""

    if getattr(_pfi_routing, "_VALDRICS_PATCHED", False):
        return

    _pfi_routing._original_get_route_name = _pfi_routing._get_route_name  # type: ignore[attr-defined]
    _pfi_routing._get_route_name = _get_route_name_patched
    _pfi_routing._VALDRICS_PATCHED = True  # type: ignore[attr-defined]

    logger.info(
        "prometheus_compat: patched _get_route_name to handle FastAPI ≥0.137 _IncludedRouter"
    )
