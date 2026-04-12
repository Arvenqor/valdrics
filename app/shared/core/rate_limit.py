"""
Rate limiting for Valdrics.

The supported managed GCP runtime delegates public API throttling to Cloudflare
edge controls and keeps the in-app slowapi limiter disabled. Redis-backed
shared limiter state remains available only for explicit non-managed or
break-glass application-side limiter paths.
"""

import asyncio
import time
from typing import Any, Callable, Optional, cast
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
import hashlib
import structlog
from redis.asyncio import Redis, from_url
from redis.exceptions import RedisError

from app.shared.core.config import get_settings
from app.shared.core.proxy_headers import resolve_client_ip

__all__ = [
    "get_limiter",
    "reset_rate_limit_runtime",
    "setup_rate_limiting",
    "rate_limit",
    "global_rate_limit",
    "global_limit_key",
    "standard_limit",
    "auth_limit",
    "analysis_limit",
    "RateLimitExceeded",
    "_rate_limit_exceeded_handler",
]

logger = structlog.get_logger()

_limiter: Limiter | None = None
_redis_client: Redis | None = None
_redis_client_loop_marker: int | None = None
_redis_client_url: str | None = None
_limiter_storage_uri: str | None = None
_limiter_enabled: bool | None = None
TOKEN_HASH_FALLBACK_RECOVERABLE_EXCEPTIONS = (RuntimeError, TypeError, ValueError)
ANALYSIS_TIER_RESOLUTION_RECOVERABLE_EXCEPTIONS = (
    AttributeError,
    TypeError,
    ValueError,
    RuntimeError,
)
REMEDIATION_REDIS_RATE_LIMIT_RECOVERABLE_EXCEPTIONS = (
    RedisError,
    OSError,
    RuntimeError,
)


def _monotonic_time() -> float:
    return time.monotonic()


def _current_loop_marker() -> int | None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return None
    if loop.is_closed():
        return None
    return id(loop)


def _analysis_limit_mapping(settings: Any) -> dict[str, str]:
    return {
        "free": f"{int(getattr(settings, 'ANALYSIS_RATE_LIMIT_FREE_PER_HOUR', 1) or 1)}/hour",
        "starter": f"{int(getattr(settings, 'ANALYSIS_RATE_LIMIT_STARTER_PER_HOUR', 2) or 2)}/hour",
        "growth": f"{int(getattr(settings, 'ANALYSIS_RATE_LIMIT_GROWTH_PER_HOUR', 10) or 10)}/hour",
        "pro": f"{int(getattr(settings, 'ANALYSIS_RATE_LIMIT_PRO_PER_HOUR', 50) or 50)}/hour",
        "enterprise": f"{int(getattr(settings, 'ANALYSIS_RATE_LIMIT_ENTERPRISE_PER_HOUR', 200) or 200)}/hour",
    }


def _managed_cloudflare_edge_profile(settings: Any) -> bool:
    environment = str(getattr(settings, "ENVIRONMENT", "") or "").strip().lower()
    runtime_profile = (
        str(getattr(settings, "PLATFORM_RUNTIME_PROFILE", "gcp") or "gcp")
        .strip()
        .lower()
    )
    public_backend = (
        str(
            getattr(settings, "PUBLIC_API_RATE_LIMITING_BACKEND", "redis") or "redis"
        )
        .strip()
        .lower()
    )
    return (
        environment in {"production", "staging"}
        and runtime_profile == "gcp"
        and public_backend == "cloudflare"
    )


def context_aware_key(request: Request) -> str:
    """
    Identifies the requester for rate limiting.
    1. Uses tenant_id if user is authenticated (B2B fairness).
    2. Falls back to sub from JWT if auth hasn't run but token exists (Prevents NAT issues).
    3. Falls back to remote IP (Defense-in-depth).
    """
    # Try request state (already populated by get_current_user dependency)
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id:
        return f"tenant:{tenant_id}"

    # Fast check for Authorization header (no DB lookup)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
            return f"token:{token_hash}"
        except TOKEN_HASH_FALLBACK_RECOVERABLE_EXCEPTIONS:
            pass

    return resolve_client_ip(request, settings_obj=get_settings())


def get_limiter() -> Limiter:
    """Lazy initialization of the Limiter instance.

    Supported production postures are:
    - explicit shared application limiter state via REDIS_URL
    - managed GCP profile with Cloudflare edge throttling and the app limiter disabled
    """
    global _limiter, _limiter_storage_uri, _limiter_enabled
    settings = get_settings()
    enabled = getattr(settings, "RATELIMIT_ENABLED", True) and not getattr(
        settings, "TESTING", False
    )
    storage_uri = settings.REDIS_URL or "memory://"
    is_production_like = settings.ENVIRONMENT.lower() in ("production", "staging")
    managed_cloudflare_profile = _managed_cloudflare_edge_profile(settings)
    if not enabled:
        storage_uri = "memory://"
        if managed_cloudflare_profile:
            logger.info(
                "rate_limiting_delegated_to_cloudflare_edge",
                msg="Cloudflare edge rate limiting is the supported public API throttle for the managed GCP profile.",
            )
    if (
        enabled
        and
        is_production_like
        and not settings.REDIS_URL
        and not settings.ALLOW_IN_MEMORY_RATE_LIMITS
    ):
        raise RuntimeError(
            "REDIS_URL is required only when RATELIMIT_ENABLED=true in staging/production "
            "for the shared application limiter. The supported managed GCP profile uses "
            "PUBLIC_API_RATE_LIMITING_BACKEND=cloudflare with RATELIMIT_ENABLED=false. "
            "Set ALLOW_IN_MEMORY_RATE_LIMITS=true only for temporary break-glass usage."
        )
    if enabled and is_production_like and not settings.REDIS_URL:
        logger.warning(
            "rate_limiting_in_memory_break_glass",
            msg="REDIS_URL is not set. The shared application limiter is running with "
            "instance-local in-memory state via ALLOW_IN_MEMORY_RATE_LIMITS and should "
            "be temporary.",
        )

    if (
        _limiter is None
        or _limiter_storage_uri != storage_uri
        or _limiter_enabled != bool(enabled)
    ):
        _limiter = Limiter(
            key_func=context_aware_key,
            storage_uri=storage_uri,
            strategy="fixed-window",
            enabled=enabled,
        )
        _limiter_storage_uri = storage_uri
        _limiter_enabled = bool(enabled)
    return _limiter


def get_redis_client() -> Redis | None:
    """Lazy initialization of the optional Redis client for shared rate-limit state."""
    global _redis_client, _redis_client_loop_marker, _redis_client_url
    settings = get_settings()
    # Tests should use in-memory fallback by default to avoid external network coupling
    # and unclosed transport warnings from ephemeral event loops.
    if getattr(settings, "TESTING", False) is True and not getattr(
        settings, "ALLOW_REDIS_IN_TESTS", False
    ):
        _redis_client = None
        return None
    if not settings.REDIS_URL:
        _redis_client = None
        _redis_client_loop_marker = None
        _redis_client_url = None
        return None

    current_loop_marker = _current_loop_marker()

    # Keep lifecycle tracking in module state rather than reading Redis client internals.
    if _redis_client is not None:
        loop_mismatch = (
            current_loop_marker is not None
            and _redis_client_loop_marker is not None
            and current_loop_marker != _redis_client_loop_marker
        )
        url_mismatch = _redis_client_url != settings.REDIS_URL
        if loop_mismatch or url_mismatch:
            _redis_client = None
            _redis_client_loop_marker = None
            _redis_client_url = None

    if _redis_client is None:
        redis_from_url = cast(Callable[..., Redis], from_url)
        _redis_client = redis_from_url(settings.REDIS_URL, decode_responses=True)
        _redis_client_loop_marker = current_loop_marker
        _redis_client_url = settings.REDIS_URL
    return _redis_client


async def reset_rate_limit_runtime() -> None:
    global _limiter, _redis_client, _redis_client_loop_marker, _redis_client_url
    global _limiter_storage_uri, _limiter_enabled
    redis_client = _redis_client
    _limiter = None
    _redis_client = None
    _redis_client_loop_marker = None
    _redis_client_url = None
    _limiter_storage_uri = None
    _limiter_enabled = None
    if redis_client is not None:
        await redis_client.aclose()


def setup_rate_limiting(app: FastAPI) -> None:
    """
    Configure rate limiting for the FastAPI application.
    """
    limiter = get_limiter()
    # Add rate limit exceeded handler
    app.state.limiter = limiter

    def _rate_limit_handler(request: Request, exc: Exception) -> Any:
        return _rate_limit_exceeded_handler(request, cast(RateLimitExceeded, exc))

    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    logger.info("rate_limiting_configured")


# Rate limit decorators for use in routes
def rate_limit(
    limit: str | Callable[[Request], str] = "100/minute",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to apply rate limiting to an endpoint."""
    # Finding #L3: If we bypass the decorator here based on settings.TESTING,
    # it captures the state at import time. Instead, we always return the
    # limiter's decorator, which internally checks its 'enabled' status
    # during each request.
    return cast(
        Callable[[Callable[..., Any]], Callable[..., Any]], get_limiter().limit(limit)
    )


def global_limit_key(namespace: str) -> Callable[[Request], str]:
    """
    Build a stable cross-tenant limiter key for shared fairness controls.
    """

    safe_namespace = "".join(
        ch if (ch.isalnum() or ch in {"_", "-", ".", ":"}) else "_"
        for ch in str(namespace or "").strip().lower()
    )
    if not safe_namespace:
        safe_namespace = "global"
    key = f"global:{safe_namespace}"

    def _key(request: Request | None = None) -> str:
        del request
        return key

    return _key


def global_rate_limit(
    limit: str | Callable[[Request], str] = "1000/minute",
    *,
    namespace: str = "default",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Apply a route-level global throttle shared across tenants.
    """

    return cast(
        Callable[[Callable[..., Any]], Callable[..., Any]],
        get_limiter().limit(limit, key_func=global_limit_key(namespace)),
    )


# Pre-configured rate limits (now using strings for delay)
# Route handlers can use @rate_limit("100/minute") or these helpers
STANDARD_LIMIT = "100/minute"
AUTH_LIMIT = "30/minute"


def get_analysis_limit(request: Optional[Request] = None) -> str:
    """
    BE-LLM-4: Dynamic rate limiting based on tenant tier.
    Protects LLM operational costs while rewarding higher tiers.
    """
    if not request:
        return "1/hour"

    try:
        raw_tier = getattr(request.state, "tier", "starter")
        if hasattr(raw_tier, "value"):
            tier = str(getattr(raw_tier, "value")).strip().lower()
        elif isinstance(raw_tier, str):
            tier = raw_tier.strip().lower()
        else:
            tier = "starter"
        if not tier:
            tier = "starter"
    except ANALYSIS_TIER_RESOLUTION_RECOVERABLE_EXCEPTIONS:
        tier = "starter"

    limits = _analysis_limit_mapping(get_settings())

    return limits.get(tier, "1/hour")


def standard_limit(func: Callable[..., Any]) -> Callable[..., Any]:
    """Apply the standard API limit decorator."""
    return rate_limit(STANDARD_LIMIT)(func)


def auth_limit(func: Callable[..., Any]) -> Callable[..., Any]:
    """Apply the authenticated-route API limit decorator."""
    return rate_limit(AUTH_LIMIT)(func)


# Dynamic analysis limit decorator
def analysis_limit(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that applies a dynamic analysis limit based on tenant tier."""
    if get_settings().TESTING:
        return func
    # Pass the callable (not its result) so it's evaluated per-request
    decorated = get_limiter().limit(get_analysis_limit)(func)
    return cast(Callable[..., Any], decorated)


# Remediation-specific rate limiting (BE-SEC-3)
REMEDIATION_LIMIT_PER_HOUR = 50  # Max remediations per tenant per hour

_remediation_counts: dict[
    str, dict[str, float | int]
] = {}  # In-memory fallback when Redis unavailable
_remediation_last_cleanup_at: float = 0.0
_REMEDIATION_WINDOW_SECONDS = 3600
_REMEDIATION_STALE_RETENTION_SECONDS = _REMEDIATION_WINDOW_SECONDS * 2
_REMEDIATION_CLEANUP_INTERVAL_SECONDS = 300


def _cleanup_stale_remediation_counts(current_time: float) -> None:
    """
    Prevent unbounded growth for local in-memory fallback rate-limit state.
    """
    global _remediation_last_cleanup_at
    if (
        current_time - _remediation_last_cleanup_at
        < _REMEDIATION_CLEANUP_INTERVAL_SECONDS
    ):
        return

    stale_before = current_time - _REMEDIATION_STALE_RETENTION_SECONDS
    stale_keys = [
        key
        for key, value in _remediation_counts.items()
        if float(value.get("window_start", 0.0)) < stale_before
    ]
    for key in stale_keys:
        _remediation_counts.pop(key, None)
    _remediation_last_cleanup_at = current_time


async def check_remediation_rate_limit(
    tenant_id: Any, action: str, limit: int = REMEDIATION_LIMIT_PER_HOUR
) -> bool:
    """
    Check if a remediation action is allowed under rate limits.

    Returns True if allowed, False if rate limited.
    Uses Redis-backed shared state when configured. Falls back to instance-local
    state only for local runtimes, the managed Cloudflare-fronted profile, or
    explicit break-glass operation.
    """
    from uuid import UUID

    tenant_key = str(tenant_id) if isinstance(tenant_id, UUID) else tenant_id
    redis = get_redis_client()

    settings = get_settings()
    is_production_like = settings.ENVIRONMENT.lower() in ("production", "staging")
    allow_instance_local_fallback = (
        not is_production_like
        or _managed_cloudflare_edge_profile(settings)
        or bool(getattr(settings, "ALLOW_IN_MEMORY_RATE_LIMITS", False))
    )

    if redis:
        try:
            # Use Redis for distributed rate limiting
            key = f"remediation_rate:{tenant_key}:{action}"
            current = await redis.incr(key)
            if current == 1:
                # Set expiry on first increment (1 hour window)
                await redis.expire(key, 3600)

            if current > limit:
                logger.warning(
                    "remediation_rate_limited",
                    tenant_id=tenant_key,
                    action=action,
                    current=current,
                    limit=limit,
                )
                return False
            return True
        except REMEDIATION_REDIS_RATE_LIMIT_RECOVERABLE_EXCEPTIONS as e:
            if not allow_instance_local_fallback:
                logger.error(
                    "remediation_rate_limit_redis_error",
                    error=str(e),
                    tenant_id=tenant_key,
                    action=action,
                )
                return False
            logger.warning(
                "remediation_rate_limit_redis_error",
                error=str(e),
                tenant_id=tenant_key,
                action=action,
            )

    if redis is None and is_production_like:
        if not allow_instance_local_fallback:
            logger.error(
                "remediation_rate_limit_shared_state_unavailable",
                tenant_id=tenant_key,
                action=action,
            )
            return False
        logger.warning(
            "remediation_rate_limit_in_memory_fallback",
            tenant_id=tenant_key,
            action=action,
            msg="Redis-backed shared rate-limit state is unavailable; using instance-local fallback state.",
        )

    # Memory fallback for local/single-instance deployments
    current_time = _monotonic_time()
    window_key = f"{tenant_key}:{action}"
    _cleanup_stale_remediation_counts(current_time)

    if window_key not in _remediation_counts:
        _remediation_counts[window_key] = {"count": 0, "window_start": current_time}

    entry = _remediation_counts[window_key]

    # Reset window if expired (1 hour)
    if current_time - entry["window_start"] > _REMEDIATION_WINDOW_SECONDS:
        entry["count"] = 0
        entry["window_start"] = current_time

    if entry["count"] >= limit:
        logger.warning(
            "remediation_rate_limited",
            tenant_id=tenant_key,
            action=action,
            current=entry["count"],
            limit=limit,
        )
        return False

    entry["count"] += 1
    return True
