# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""Bound orchestration for all exposed OCI Language pretrained operations."""

from __future__ import annotations

import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Protocol

import oci
import structlog

from .auth import OciAuthenticationError
from .config import LanguageMcpSettings
from .models import (
    AnyToolRequest,
    BaseToolResult,
    DetectPiiEntitiesRequest,
    RelexifyRule,
)
from .parser import (
    extract_service_error_oci_request_id,
    failure_result,
    parse_oci_response,
)

logger = structlog.get_logger(component="language_service")

_CAPABILITY_NAMES = {
    "detect_dominant_language": "language detection",
    "detect_language_text_classification": "text classification",
    "detect_language_entities": "entity detection",
    "detect_language_key_phrases": "key phrase extraction",
    "detect_language_sentiments": "sentiment analysis",
    "detect_language_pii_entities": "PII processing",
    "translate_language_text": "translation",
}


class LanguageProvider(Protocol):
    def detect_dominant_language(self, request: Any, **kwargs: Any) -> object: ...
    def classify_text(self, request: Any, **kwargs: Any) -> object: ...
    def detect_entities(self, request: Any, **kwargs: Any) -> object: ...
    def extract_key_phrases(self, request: Any, **kwargs: Any) -> object: ...
    def analyze_sentiment(self, request: Any, **kwargs: Any) -> object: ...
    def detect_pii_entities(self, request: Any, **kwargs: Any) -> object: ...
    def translate_text(self, request: Any, **kwargs: Any) -> object: ...


class LanguageService:
    """Execute only statically registered provider operations under bounded capacity."""

    def __init__(self, *, provider: LanguageProvider, settings: LanguageMcpSettings) -> None:
        self._provider = provider
        self._settings = settings
        self._capacity = asyncio.Semaphore(settings.max_inflight_requests)
        self._executor = ThreadPoolExecutor(
            max_workers=settings.max_inflight_requests,
            thread_name_prefix="oci-language",
        )
        self._in_flight = 0

    @property
    def is_ready(self) -> bool:
        return self._in_flight < self._settings.max_inflight_requests

    @property
    def tool_timeout_seconds(self) -> float:
        return self._settings.tool_timeout_seconds

    async def execute(self, tool: str, request: AnyToolRequest) -> BaseToolResult:
        provider_method = self._provider_method(tool)
        request_id = uuid.uuid4().hex
        client_opc_request_id = request.options.opc_request_id or request_id
        submitted = len(request.documents)
        compartment_id = request.compartment_id or self._settings.compartment_id
        capability = _CAPABILITY_NAMES[tool]
        if not compartment_id:
            return failure_result(
                tool=tool,
                request_id=request_id,
                client_opc_request_id=client_opc_request_id,
                submitted=submitted,
                code="INVALID_REQUEST",
                message=f"An OCI compartment is required for {capability}.",
                retryable=False,
            )
        try:
            await asyncio.wait_for(
                self._capacity.acquire(),
                timeout=self._settings.capacity_acquire_timeout_seconds,
            )
        except TimeoutError:
            return failure_result(
                tool=tool,
                request_id=request_id,
                client_opc_request_id=client_opc_request_id,
                submitted=submitted,
                code="BUSY",
                message="OCI Language processing is at capacity. Retry shortly.",
                retryable=True,
            )

        started = time.perf_counter()
        self._in_flight += 1
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(
            self._executor,
            partial(
                provider_method,
                request,
                compartment_id=compartment_id,
                opc_request_id=client_opc_request_id,
            ),
        )

        def release_capacity(_future: asyncio.Future[object]) -> None:
            self._in_flight -= 1
            self._capacity.release()

        future.add_done_callback(release_capacity)
        try:
            response = await asyncio.shield(future)
            result = parse_oci_response(
                response,
                tool=tool,
                request=request,
                request_id=request_id,
                client_opc_request_id=client_opc_request_id,
            )
        except asyncio.CancelledError:
            await logger.awarning(
                "language_request_cancelled",
                tool=tool,
                request_id=request_id,
                client_opc_request_id=client_opc_request_id,
            )
            raise
        except OciAuthenticationError:
            result = failure_result(
                tool=tool,
                request_id=request_id,
                client_opc_request_id=client_opc_request_id,
                submitted=submitted,
                code="AUTHENTICATION_FAILED",
                message=(
                    "OCI authentication is unavailable. "
                    "Refresh the configured identity and retry."
                ),
                retryable=False,
            )
        except oci.exceptions.ServiceError as exc:
            status = int(getattr(exc, "status", 0) or 0)
            code, message, retryable = _public_service_error(status, capability)
            if code == "UPSTREAM_UNAVAILABLE" and _uses_relexify(request):
                message = (
                    "OCI Language could not complete PII relexification. "
                    "Retry later and use the OCI request ID for support correlation."
                )
            result = failure_result(
                tool=tool,
                request_id=request_id,
                client_opc_request_id=client_opc_request_id,
                submitted=submitted,
                code=code,
                message=message,
                retryable=retryable,
                oci_request_id=extract_service_error_oci_request_id(exc),
            )
        except Exception as exc:
            timed_out = _is_timeout(exc)
            circuit_open = _is_circuit_open(exc)
            result = failure_result(
                tool=tool,
                request_id=request_id,
                client_opc_request_id=client_opc_request_id,
                submitted=submitted,
                code=(
                    "UPSTREAM_TIMEOUT"
                    if timed_out
                    else "UPSTREAM_UNAVAILABLE"
                    if circuit_open
                    else "INTERNAL_ERROR"
                ),
                message=(
                    f"OCI Language {capability} timed out. Retry shortly."
                    if timed_out
                    else f"OCI Language {capability} failed unexpectedly."
                ),
                retryable=timed_out or circuit_open,
            )
        await logger.ainfo(
            "language_request_completed",
            tool=tool,
            request_id=result.request_id,
            client_opc_request_id=result.client_opc_request_id,
            oci_request_id=result.oci_request_id,
            status=result.status,
            error_code=result.errors[0].code if result.errors else None,
            retryable=any(error.retryable for error in result.errors),
            submitted=result.summary.submitted,
            succeeded=result.summary.succeeded,
            failed=result.summary.failed,
            items_found=result.summary.items_found,
            duration_ms=round((time.perf_counter() - started) * 1000, 2),
        )
        return result

    def _provider_method(self, tool: str) -> Any:
        methods = {
            "detect_dominant_language": self._provider.detect_dominant_language,
            "detect_language_text_classification": self._provider.classify_text,
            "detect_language_entities": self._provider.detect_entities,
            "detect_language_key_phrases": self._provider.extract_key_phrases,
            "detect_language_sentiments": self._provider.analyze_sentiment,
            "detect_language_pii_entities": self._provider.detect_pii_entities,
            "translate_language_text": self._provider.translate_text,
        }
        return methods[tool]

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)


def _public_service_error(status: int, capability: str) -> tuple[str, str, bool]:
    if status == 401:
        return "AUTHENTICATION_FAILED", "OCI authentication failed.", False
    if status == 403:
        return "FORBIDDEN", f"The configured OCI identity cannot perform {capability}.", False
    if status == 429:
        return "RATE_LIMITED", f"OCI Language {capability} is temporarily rate limited.", True
    if 400 <= status < 500:
        return "INVALID_REQUEST", f"The {capability} request was not accepted.", False
    if status >= 500:
        return "UPSTREAM_UNAVAILABLE", "OCI Language is temporarily unavailable.", True
    return "UPSTREAM_UNAVAILABLE", f"OCI Language {capability} could not be completed.", False


def _uses_relexify(request: AnyToolRequest) -> bool:
    return bool(
        isinstance(request, DetectPiiEntitiesRequest)
        and request.masking
        and any(isinstance(rule, RelexifyRule) for rule in request.masking.values())
    )


def _exception_chain(exc: BaseException) -> tuple[BaseException, ...]:
    """Return a bounded exception chain without following arbitrary object attributes."""

    chain: list[BaseException] = []
    current: BaseException | None = exc
    while current is not None and len(chain) < 8 and current not in chain:
        chain.append(current)
        current = current.__cause__ or current.__context__
    return tuple(chain)


def _is_timeout(exc: BaseException) -> bool:
    return any(
        isinstance(item, (oci.exceptions.ConnectTimeout,))
        or type(item).__name__ in {"ReadTimeout", "ConnectTimeout", "BaseConnectTimeout"}
        for item in _exception_chain(exc)
    )


def _is_circuit_open(exc: BaseException) -> bool:
    return any("circuit" in type(item).__name__.lower() for item in _exception_chain(exc))
