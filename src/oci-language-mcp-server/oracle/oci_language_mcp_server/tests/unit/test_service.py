# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import time
from types import SimpleNamespace

import oci
import pytest

from oracle.oci_language_mcp_server.config import LanguageMcpSettings
from oracle.oci_language_mcp_server.models import REQUEST_MODELS
from oracle.oci_language_mcp_server.service import (
    LanguageService,
    _is_circuit_open,
    _is_timeout,
    _public_service_error,
)


class CapturingProvider:
    def __init__(self) -> None:
        self.tool = None
        self.compartment_id = None
        self.opc_request_id = None

    def __getattr__(self, tool):
        def invoke(request, *, compartment_id, opc_request_id):
            self.tool = tool
            self.compartment_id = compartment_id
            self.opc_request_id = opc_request_id
            return SimpleNamespace(
                headers={"opc-request-id": f"{opc_request_id}/OCI"},
                data={
                    "documents": [
                        {
                            "key": request.documents[0].key,
                            "languages": [{"name": "English", "code": "en", "score": 1}],
                        }
                    ],
                    "errors": [],
                },
            )

        return invoke


class FailingProvider(CapturingProvider):
    def __getattr__(self, tool):
        def invoke(request, *, compartment_id, opc_request_id):
            raise oci.exceptions.ServiceError(
                403,
                "Forbidden",
                {"opc-request-id": "OCI_FAILED"},
                "internal policy details",
            )

        return invoke


class StatusFailingProvider(CapturingProvider):
    def __init__(self, status: int) -> None:
        super().__init__()
        self.status = status

    def __getattr__(self, tool):
        def invoke(request, *, compartment_id, opc_request_id):
            raise oci.exceptions.ServiceError(
                self.status,
                "UpstreamCode",
                {"opc-request-id": "OCI_STATUS_FAILED"},
                "raw upstream implementation details",
            )

        return invoke


class SlowProvider(CapturingProvider):
    def __getattr__(self, tool):
        parent = super().__getattr__(tool)

        def invoke(*args, **kwargs):
            time.sleep(0.2)
            return parent(*args, **kwargs)

        return invoke


async def test_service_forwards_safe_client_id_and_returns_oci_id() -> None:
    provider = CapturingProvider()
    service = LanguageService(
        provider=provider,
        settings=LanguageMcpSettings(compartment_id="configured-compartment"),
    )
    try:
        result = await service.execute(
            "detect_dominant_language",
            REQUEST_MODELS["detect_dominant_language"].model_validate(
                {
                    "documents": [{"key": "one", "text": "hello"}],
                    "options": {"opc_request_id": "CLIENT"},
                }
            ),
        )
    finally:
        service.shutdown()
    assert result.status == "succeeded"
    assert provider.tool == "detect_dominant_language"
    assert provider.compartment_id == "configured-compartment"
    assert provider.opc_request_id == "CLIENT"
    assert result.oci_request_id == "CLIENT/OCI"


async def test_service_returns_safe_missing_compartment_and_forbidden_errors() -> None:
    request = REQUEST_MODELS["detect_dominant_language"].model_validate(
        {"documents": [{"key": "one", "text": "secret input"}]}
    )
    service = LanguageService(provider=CapturingProvider(), settings=LanguageMcpSettings())
    try:
        missing = await service.execute("detect_dominant_language", request)
    finally:
        service.shutdown()
    assert missing.errors[0].code == "INVALID_REQUEST"
    assert "secret input" not in str(missing)

    service = LanguageService(
        provider=FailingProvider(),
        settings=LanguageMcpSettings(compartment_id="configured"),
    )
    try:
        forbidden = await service.execute("detect_dominant_language", request)
    finally:
        service.shutdown()
    assert forbidden.errors[0].code == "FORBIDDEN"
    assert forbidden.oci_request_id == "OCI_FAILED"
    assert "internal policy" not in str(forbidden)


async def test_service_rejects_when_shared_capacity_is_busy() -> None:
    import asyncio

    service = LanguageService(
        provider=SlowProvider(),
        settings=LanguageMcpSettings(
            compartment_id="configured",
            max_inflight_requests=1,
            capacity_acquire_timeout_seconds=0.01,
        ),
    )
    request = REQUEST_MODELS["detect_dominant_language"].model_validate(
        {"documents": [{"key": "one", "text": "hello"}]}
    )
    try:
        first = asyncio.create_task(service.execute("detect_dominant_language", request))
        await asyncio.sleep(0.02)
        second = await service.execute("detect_dominant_language", request)
        await first
    finally:
        service.shutdown()
    assert second.errors[0].code == "BUSY"


@pytest.mark.parametrize("status", [400, 404, 409, 422])
def test_public_service_error_maps_other_client_errors_to_invalid_request(
    status: int,
) -> None:
    code, message, retryable = _public_service_error(status, "translation")
    assert code == "INVALID_REQUEST"
    assert message == "The translation request was not accepted."
    assert retryable is False


@pytest.mark.parametrize(
    ("status", "expected_code", "expected_retryable"),
    [
        (401, "AUTHENTICATION_FAILED", False),
        (403, "FORBIDDEN", False),
        (429, "RATE_LIMITED", True),
        (500, "UPSTREAM_UNAVAILABLE", True),
        (503, "UPSTREAM_UNAVAILABLE", True),
    ],
)
def test_public_service_error_preserves_special_status_mappings(
    status: int, expected_code: str, expected_retryable: bool
) -> None:
    code, _message, retryable = _public_service_error(status, "translation")
    assert code == expected_code
    assert retryable is expected_retryable


def test_timeout_and_circuit_detection_follow_safe_exception_chains() -> None:
    class ReadTimeout(Exception):
        pass

    class CircuitBreakerOpen(Exception):
        pass

    wrapped_timeout = oci.exceptions.RequestException("request failed")
    wrapped_timeout.__cause__ = ReadTimeout("read timed out")
    assert _is_timeout(wrapped_timeout) is True
    assert _is_circuit_open(CircuitBreakerOpen("open")) is True


async def test_service_returns_invalid_request_for_unsupported_translation() -> None:
    service = LanguageService(
        provider=StatusFailingProvider(422),
        settings=LanguageMcpSettings(compartment_id="configured"),
    )
    request = REQUEST_MODELS["translate_language_text"].model_validate(
        {
            "documents": [{"key": "one", "text": "hello"}],
            "target_language_code": "zz",
        }
    )
    try:
        result = await service.execute("translate_language_text", request)
    finally:
        service.shutdown()
    assert result.errors[0].code == "INVALID_REQUEST"
    assert result.errors[0].retryable is False
    assert result.oci_request_id == "OCI_STATUS_FAILED"
    assert result.text.startswith("Translation failed.")
    assert "raw upstream" not in str(result)


async def test_service_returns_safe_relexify_specific_upstream_error() -> None:
    service = LanguageService(
        provider=StatusFailingProvider(503),
        settings=LanguageMcpSettings(compartment_id="configured"),
    )
    request = REQUEST_MODELS["detect_language_pii_entities"].model_validate(
        {
            "documents": [{"key": "one", "text": "Date 2026-07-24"}],
            "masking": {"DATE_TIME": {"mode": "RELEXIFY"}},
        }
    )
    try:
        result = await service.execute("detect_language_pii_entities", request)
    finally:
        service.shutdown()
    assert result.errors[0].code == "UPSTREAM_UNAVAILABLE"
    assert result.errors[0].retryable is True
    assert "could not complete PII relexification" in result.text
    assert "OCI request ID: OCI_STATUS_FAILED." in result.text
    assert "raw upstream" not in str(result)
