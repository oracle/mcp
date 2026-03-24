"""Tests for the circuit breaker."""

import time

from oracle.oci_kafka_mcp_server.kafka.connection import CircuitBreaker, CircuitState


class TestCircuitBreaker:
    """Test circuit breaker state transitions."""

    def test_starts_closed(self) -> None:
        """Circuit breaker should start in CLOSED state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request()

    def test_stays_closed_below_threshold(self) -> None:
        """Should stay closed if failures are below threshold."""
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request()

    def test_opens_at_threshold(self) -> None:
        """Should open when failure count reaches threshold."""
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert not cb.allow_request()

    def test_success_resets_count(self) -> None:
        """A success should reset the failure count."""
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_after_cooldown(self) -> None:
        """Should transition to HALF_OPEN after cooldown expires."""
        cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0.05)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        time.sleep(0.06)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.allow_request()

    def test_half_open_success_closes(self) -> None:
        """A success in HALF_OPEN state should close the circuit."""
        cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0.05)
        cb.record_failure()
        time.sleep(0.06)
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED
