"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import json
from typing import Any

import oci

from ..authentication.session_signer import session_config


def create_vision_client(*, profile: str | None = None, region: str | None = None):
    config, signer, _context = session_config(profile=profile, region=region)
    return oci.ai_vision.AIServiceVisionClient(config=config, signer=signer)


def call_analyze_image(
    client: Any,
    *,
    feature: Any,
    image_details: Any,
    compartment_id: str,
    request_id: str | None = None,
):
    return call_analyze_image_features(
        client,
        features=[feature],
        image_details=image_details,
        compartment_id=compartment_id,
        request_id=request_id,
    )


def call_analyze_image_features(
    client: Any,
    *,
    features: list[Any],
    image_details: Any,
    compartment_id: str,
    request_id: str | None = None,
):
    details = oci.ai_vision.models.AnalyzeImageDetails(
        features=features,
        image=image_details,
        compartment_id=compartment_id,
    )
    return client.analyze_image(
        analyze_image_details=details,
        opc_request_id=request_id,
    )


def call_create_image_job(
    client: Any,
    *,
    input_location: Any,
    features: list[Any],
    output_location: Any,
    compartment_id: str,
    display_name: str | None = None,
    is_zip_output_enabled: bool = False,
    request_id: str | None = None,
):
    details = _create_image_job_details(
        input_location=input_location,
        features=features,
        output_location=output_location,
        compartment_id=compartment_id,
        display_name=display_name,
        is_zip_output_enabled=is_zip_output_enabled,
    )
    return client.create_image_job(create_image_job_details=details, opc_request_id=request_id)


def create_image_job_payload_size(
    *,
    input_location: Any,
    features: list[Any],
    output_location: Any,
    compartment_id: str,
    display_name: str | None = None,
    is_zip_output_enabled: bool = False,
) -> int:
    """Return a conservative serialized request-body size for OCI limit checks."""
    details = _create_image_job_details(
        input_location=input_location,
        features=features,
        output_location=output_location,
        compartment_id=compartment_id,
        display_name=display_name,
        is_zip_output_enabled=is_zip_output_enabled,
    )
    # Match the SDK's conservative JSON defaults: separators include spaces and
    # non-ASCII characters are escaped. Compact UTF-8 JSON would undercount the
    # actual body near OCI Vision's 500 KB service limit.
    payload = json.dumps(oci.util.to_dict(details)).encode("utf-8")
    return len(payload)


def _create_image_job_details(
    *,
    input_location: Any,
    features: list[Any],
    output_location: Any,
    compartment_id: str,
    display_name: str | None,
    is_zip_output_enabled: bool,
):
    return oci.ai_vision.models.CreateImageJobDetails(
        input_location=input_location,
        features=features,
        output_location=output_location,
        compartment_id=compartment_id,
        display_name=display_name,
        is_zip_output_enabled=is_zip_output_enabled,
    )


def call_get_image_job(client: Any, *, job_id: str, request_id: str | None = None):
    return client.get_image_job(image_job_id=job_id, opc_request_id=request_id)


def call_cancel_image_job(client: Any, *, job_id: str, request_id: str | None = None):
    return client.cancel_image_job(image_job_id=job_id, opc_request_id=request_id)
