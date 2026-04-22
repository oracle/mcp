"""Connection management with circuit breaker pattern."""

from __future__ import annotations

import logging
import time
from enum import StrEnum

logger = logging.getLogger(__name__)


class CircuitState(StrEnum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures when Kafka is unavailable.

    - CLOSED: Normal operation, requests pass through.
    - OPEN: Too many failures, requests are rejected immediately.
    - HALF_OPEN: After cooldown, allow one test request through.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: float = 30.0,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._cooldown_seconds = cooldown_seconds
        self._failure_count = 0
        self._last_failure_time: float = 0
        self._state = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for cooldown expiry."""
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self._cooldown_seconds:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def allow_request(self) -> bool:
        """Check if a request should be allowed through."""
        current_state = self.state
        if current_state == CircuitState.CLOSED:
            return True
        if current_state == CircuitState.HALF_OPEN:
            return True  # Allow one test request
        return False

    def record_success(self) -> None:
        """Record a successful operation."""
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def reset(self) -> None:
        """Reset the circuit breaker to closed state (e.g., after reconfiguration)."""
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time = 0

    def record_failure(self) -> None:
        """Record a failed operation."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker OPEN after %d failures. "
                "Requests will be rejected for %.0f seconds.",
                self._failure_count,
                self._cooldown_seconds,
            )
