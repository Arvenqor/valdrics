"""
Circuit Breaker for LLM Providers - Per-Provider Isolation

Prevents cascading failures by isolating LLM provider failures.
When one provider fails repeatedly, the circuit "opens" and requests
are routed to the next provider immediately.

Pattern: Half-Open Circuit Breaker
- CLOSED: Normal operation, requests pass through
- OPEN: Provider is failing, skip to next provider
- HALF-OPEN: After recovery time, try one request to test

Usage:
    breaker = LLMCircuitBreaker()

    try:
        with breaker.protect("groq"):
            response = await groq_client.chat(...)
            breaker.record_success("groq")
    except RuntimeError as e:
        breaker.record_failure("groq")
        # Fall back to next provider
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from enum import Enum

import structlog

from app.shared.core.exceptions import ValdricsException

logger = structlog.get_logger()
FATAL_EXCEPTIONS = (SystemExit, KeyboardInterrupt, GeneratorExit)


def _monotonic_time() -> float:
    return time.monotonic()


class CircuitState(str, Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, skip requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class ProviderCircuit:
    """State for a single provider's circuit breaker."""

    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None
    last_failure_monotonic: float | None = None
    last_success_monotonic: float | None = None
    probe_in_flight: bool = False

    failure_threshold: int = 3
    success_threshold: int = 2
    recovery_timeout: int = 60


class LLMCircuitBreaker:
    """
    Per-provider circuit breaker for LLM resilience.

    Isolates failures so that:
    - Groq failing doesn't affect Gemini
    - Each provider has independent failure tracking
    - Automatic recovery testing after timeout
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        success_threshold: int = 2,
        recovery_timeout: int = 60,
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.recovery_timeout = recovery_timeout
        self._circuits: dict[str, ProviderCircuit] = {}
        self._lock = RLock()

    def _get_circuit(self, provider: str) -> ProviderCircuit:
        """Get or create circuit for provider."""
        with self._lock:
            if provider not in self._circuits:
                self._circuits[provider] = ProviderCircuit(
                    name=provider,
                    failure_threshold=self.failure_threshold,
                    success_threshold=self.success_threshold,
                    recovery_timeout=self.recovery_timeout,
                )
            return self._circuits[provider]

    def is_available(self, provider: str) -> bool:
        """Check if provider is available for requests."""
        with self._lock:
            circuit = self._get_circuit(provider)
            now = datetime.now(timezone.utc)

            if circuit.state == CircuitState.CLOSED:
                return True

            if circuit.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if circuit.last_failure_monotonic is not None:
                    elapsed = _monotonic_time() - circuit.last_failure_monotonic
                    if elapsed >= circuit.recovery_timeout:
                        # Transition to half-open
                        circuit.state = CircuitState.HALF_OPEN
                        logger.info(
                            "circuit_half_open",
                            provider=provider,
                            message="Testing recovery",
                        )
                        return True
                elif circuit.last_failure_time:
                    elapsed = (now - circuit.last_failure_time).total_seconds()
                    if elapsed >= circuit.recovery_timeout:
                        # Transition to half-open
                        circuit.state = CircuitState.HALF_OPEN
                        logger.info(
                            "circuit_half_open",
                            provider=provider,
                            message="Testing recovery",
                        )
                        return True
                return False

            if circuit.state == CircuitState.HALF_OPEN:
                return True

            return False

    def _try_acquire_probe(self, provider: str) -> bool:
        """Acquire the single half-open probe slot for a provider."""
        with self._lock:
            circuit = self._get_circuit(provider)
            now = datetime.now(timezone.utc)

            if circuit.state == CircuitState.CLOSED:
                return True

            if circuit.state == CircuitState.OPEN:
                if (
                    circuit.last_failure_monotonic is None
                    and circuit.last_failure_time is None
                ):
                    return False
                if circuit.last_failure_monotonic is not None:
                    elapsed = _monotonic_time() - circuit.last_failure_monotonic
                else:
                    if circuit.last_failure_time is None:
                        return False
                    elapsed = (now - circuit.last_failure_time).total_seconds()
                if elapsed < circuit.recovery_timeout:
                    return False
                circuit.state = CircuitState.HALF_OPEN
                circuit.probe_in_flight = True
                logger.info(
                    "circuit_half_open",
                    provider=provider,
                    message="Testing recovery",
                )
                return True

            if circuit.state == CircuitState.HALF_OPEN:
                if circuit.probe_in_flight:
                    return False
                circuit.probe_in_flight = True
                return True

            return False

    def record_success(self, provider: str) -> None:
        """Record successful request to provider."""
        with self._lock:
            circuit = self._get_circuit(provider)
            circuit.success_count += 1
            circuit.last_success_time = datetime.now(timezone.utc)
            circuit.last_success_monotonic = _monotonic_time()

            if circuit.state == CircuitState.HALF_OPEN:
                if circuit.success_count >= circuit.success_threshold:
                    # Recovery confirmed, close circuit
                    circuit.state = CircuitState.CLOSED
                    circuit.failure_count = 0
                    circuit.success_count = 0
                    circuit.probe_in_flight = False
                    logger.info(
                        "circuit_closed", provider=provider, message="Provider recovered"
                    )
                else:
                    circuit.probe_in_flight = False

            elif circuit.state == CircuitState.CLOSED:
                # Reset failure count on success
                circuit.failure_count = 0
                circuit.probe_in_flight = False

    def record_failure(self, provider: str, error: str | None = None) -> None:
        """Record failed request to provider."""
        with self._lock:
            circuit = self._get_circuit(provider)
            circuit.failure_count += 1
            circuit.last_failure_time = datetime.now(timezone.utc)
            circuit.last_failure_monotonic = _monotonic_time()
            circuit.success_count = 0  # Reset success count
            circuit.probe_in_flight = False

            logger.warning(
                "llm_provider_failure",
                provider=provider,
                failure_count=circuit.failure_count,
                threshold=circuit.failure_threshold,
                error=error,
            )

            if circuit.state == CircuitState.HALF_OPEN:
                # Failed during recovery test, reopen circuit
                circuit.state = CircuitState.OPEN
                logger.warning(
                    "circuit_reopened", provider=provider, message="Recovery failed"
                )

            elif circuit.state == CircuitState.CLOSED:
                if circuit.failure_count >= circuit.failure_threshold:
                    # Too many failures, open circuit
                    circuit.state = CircuitState.OPEN
                    logger.error(
                        "circuit_opened",
                        provider=provider,
                        failure_count=circuit.failure_count,
                        message="Provider marked unavailable",
                    )

    @contextmanager
    def protect(self, provider: str) -> Any:
        """
        Context manager for protected provider calls.

        Usage:
            with breaker.protect("groq"):
                response = await client.chat(...)
        """
        if not self._try_acquire_probe(provider):
            raise CircuitOpenError(f"Circuit open for {provider}")

        try:
            yield
        except FATAL_EXCEPTIONS:
            raise
        except Exception as exc:
            self.record_failure(provider, str(exc))
            raise

    def get_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all circuits for monitoring."""
        with self._lock:
            return {
                name: {
                    "state": circuit.state.value,
                    "failure_count": circuit.failure_count,
                    "success_count": circuit.success_count,
                    "last_failure": circuit.last_failure_time.isoformat()
                    if circuit.last_failure_time
                    else None,
                    "last_success": circuit.last_success_time.isoformat()
                    if circuit.last_success_time
                    else None,
                }
                for name, circuit in self._circuits.items()
            }

    def reset(self, provider: str) -> None:
        """Manually reset a circuit (for admin use)."""
        with self._lock:
            if provider in self._circuits:
                self._circuits[provider] = ProviderCircuit(
                    name=provider,
                    failure_threshold=self.failure_threshold,
                    success_threshold=self.success_threshold,
                    recovery_timeout=self.recovery_timeout,
                )
                logger.info("circuit_reset", provider=provider)


class CircuitOpenError(ValdricsException):
    """Raised when circuit is open and request should be skipped."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message,
            code="circuit_open",
            status_code=503,
            details=details,
        )


# Singleton instance for app-wide use
_circuit_breaker: LLMCircuitBreaker | None = None


def get_circuit_breaker() -> LLMCircuitBreaker:
    """Get or create the global circuit breaker instance."""
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = LLMCircuitBreaker()
    return _circuit_breaker
