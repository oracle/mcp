"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import oci
import pytest

from oracle.oci_vision_mcp_server.authentication.session_signer import (
    SessionAuthenticationError,
    session_auth_error_from_service_error,
)
from oracle.oci_vision_mcp_server.oci_clients.object_storage import (
    call_get_object,
    call_list_objects,
    call_put_object,
    create_object_storage_client,
)
from oracle.oci_vision_mcp_server.oci_clients.vision import (
    call_analyze_image,
    call_analyze_image_features,
    call_cancel_image_job,
    call_create_image_job,
    call_get_image_job,
    create_vision_client,
)


class FakeVisionClient:
    def __init__(self) -> None:
        self.kwargs = None

    def analyze_image(self, **kwargs):
        self.kwargs = kwargs
        return object()

    def create_image_job(self, **kwargs):
        self.kwargs = kwargs
        return object()

    def get_image_job(self, **kwargs):
        self.kwargs = kwargs
        return object()

    def cancel_image_job(self, **kwargs):
        self.kwargs = kwargs
        return object()


class FakeObjectStorageClient:
    def __init__(self) -> None:
        self.kwargs = None

    def put_object(self, **kwargs):
        self.kwargs = kwargs
        return object()

    def list_objects(self, **kwargs):
        self.kwargs = kwargs
        return object()

    def get_object(self, **kwargs):
        self.kwargs = kwargs
        return object()


def test_call_analyze_image_maps_details_and_request_id() -> None:
    client = FakeVisionClient()
    feature = oci.ai_vision.models.ImageClassificationFeature(
        feature_type="IMAGE_CLASSIFICATION",
        max_results=5,
    )
    image_details = oci.ai_vision.models.InlineImageDetails(
        source="INLINE",
        data="aGVsbG8=",
    )

    call_analyze_image(
        client,
        feature=feature,
        image_details=image_details,
        compartment_id="ocid1.compartment.oc1..example",
        request_id="REQ123",
    )

    assert client.kwargs["opc_request_id"] == "REQ123"
    details = client.kwargs["analyze_image_details"]
    assert details.compartment_id == "ocid1.compartment.oc1..example"
    assert details.features == [feature]
    assert details.image == image_details


def test_call_analyze_image_features_maps_multiple_features() -> None:
    client = FakeVisionClient()
    features = [
        oci.ai_vision.models.ImageClassificationFeature(feature_type="IMAGE_CLASSIFICATION"),
        oci.ai_vision.models.ImageTextDetectionFeature(feature_type="TEXT_DETECTION"),
    ]
    image_details = oci.ai_vision.models.InlineImageDetails(
        source="INLINE",
        data="aGVsbG8=",
    )

    call_analyze_image_features(
        client,
        features=features,
        image_details=image_details,
        compartment_id="ocid1.compartment.oc1..example",
        request_id="REQ123",
    )

    assert client.kwargs["opc_request_id"] == "REQ123"
    details = client.kwargs["analyze_image_details"]
    assert details.features == features
    assert details.image == image_details


def test_call_create_image_job_maps_details_and_request_id() -> None:
    client = FakeVisionClient()
    input_location = object()
    output_location = object()
    features = [oci.ai_vision.models.ImageTextDetectionFeature(feature_type="TEXT_DETECTION")]

    call_create_image_job(
        client,
        input_location=input_location,
        features=features,
        output_location=output_location,
        compartment_id="ocid1.compartment.oc1..example",
        display_name="review-job",
        is_zip_output_enabled=True,
        request_id="REQ123",
    )

    assert client.kwargs["opc_request_id"] == "REQ123"
    details = client.kwargs["create_image_job_details"]
    assert details.input_location is input_location
    assert details.output_location is output_location
    assert details.features == features
    assert details.compartment_id == "ocid1.compartment.oc1..example"
    assert details.display_name == "review-job"
    assert details.is_zip_output_enabled is True


def test_call_get_and_cancel_image_job_map_job_id() -> None:
    client = FakeVisionClient()

    call_get_image_job(client, job_id="job_ocid", request_id="GET_REQ")
    assert client.kwargs == {"image_job_id": "job_ocid", "opc_request_id": "GET_REQ"}

    call_cancel_image_job(client, job_id="job_ocid", request_id="CANCEL_REQ")
    assert client.kwargs == {"image_job_id": "job_ocid", "opc_request_id": "CANCEL_REQ"}


def test_call_put_object_maps_no_overwrite_upload_kwargs() -> None:
    client = FakeObjectStorageClient()

    call_put_object(
        client,
        namespace="ns",
        bucket="bucket",
        object_name="images/photo.png",
        body=b"image",
        content_length=5,
        content_type="image/png",
        metadata={"source": "mcp"},
        request_id="REQ123",
        overwrite=False,
    )

    assert client.kwargs == {
        "namespace_name": "ns",
        "bucket_name": "bucket",
        "object_name": "images/photo.png",
        "put_object_body": b"image",
        "content_length": 5,
        "content_type": "image/png",
        "opc_meta": {"source": "mcp"},
        "opc_client_request_id": "REQ123",
        "if_none_match": "*",
    }


def test_call_put_object_omits_if_none_match_when_overwrite_is_allowed() -> None:
    client = FakeObjectStorageClient()

    call_put_object(
        client,
        namespace="ns",
        bucket="bucket",
        object_name="images/photo.png",
        body=b"image",
        content_length=5,
        content_type=None,
        overwrite=True,
    )

    assert "if_none_match" not in client.kwargs
    assert "content_type" not in client.kwargs


def test_call_list_objects_maps_list_kwargs() -> None:
    client = FakeObjectStorageClient()

    call_list_objects(
        client,
        namespace="ns",
        bucket="bucket",
        prefix="tmp/",
        delimiter="/",
        fields="name,size,timeModified",
        start="tmp/a.jpg",
        limit=500,
        request_id="REQ123",
    )

    assert client.kwargs == {
        "namespace_name": "ns",
        "bucket_name": "bucket",
        "prefix": "tmp/",
        "delimiter": "/",
        "fields": "name,size,timeModified",
        "start": "tmp/a.jpg",
        "limit": 500,
        "opc_client_request_id": "REQ123",
    }


def test_call_get_object_maps_get_kwargs() -> None:
    client = FakeObjectStorageClient()

    call_get_object(
        client,
        namespace="ns",
        bucket="bucket",
        object_name="images/photo.png",
        request_id="REQ123",
    )

    assert client.kwargs == {
        "namespace_name": "ns",
        "bucket_name": "bucket",
        "object_name": "images/photo.png",
        "opc_client_request_id": "REQ123",
    }


def test_create_vision_client_rejects_non_session_profile(monkeypatch) -> None:
    monkeypatch.setattr(
        oci.config,
        "from_file",
        lambda profile_name: {"region": "us-ashburn-1"},
    )

    with pytest.raises(SessionAuthenticationError) as exc_info:
        create_vision_client(profile="OC1_ASH")

    assert exc_info.value.retryable is True
    assert exc_info.value.code == "OCI_SESSION_AUTH_REQUIRED"
    assert (
        "oci session authenticate --profile-name OC1_ASH --region us-ashburn-1"
        in str(exc_info.value)
    )


def test_create_vision_client_uses_session_token_signer(monkeypatch, tmp_path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("session-token", encoding="utf-8")
    key_file = tmp_path / "key.pem"
    key_file.write_text("session-key", encoding="utf-8")

    captured = {}

    monkeypatch.setattr(
        oci.config,
        "from_file",
        lambda profile_name: {
            "region": "us-ashburn-1",
            "security_token_file": str(token_file),
            "key_file": str(key_file),
        },
    )
    monkeypatch.setattr(oci.signer, "load_private_key_from_file", lambda path: f"key:{path}")
    monkeypatch.setattr(
        oci.auth.signers,
        "SecurityTokenSigner",
        lambda token, private_key: {"token": token, "private_key": private_key},
    )

    def fake_client(*, config, signer):
        captured["config"] = config
        captured["signer"] = signer
        return "vision-client"

    monkeypatch.setattr(oci.ai_vision, "AIServiceVisionClient", fake_client)

    client = create_vision_client(profile="OC1_ASH", region="us-phoenix-1")

    assert client == "vision-client"
    assert captured["config"]["region"] == "us-phoenix-1"
    assert captured["config"]["additional_user_agent"] == "oci-vision-mcp/0.1.0"
    assert captured["signer"] == {
        "token": "session-token",
        "private_key": f"key:{key_file}",
    }


def test_create_object_storage_client_uses_session_token_signer(monkeypatch, tmp_path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("session-token", encoding="utf-8")
    key_file = tmp_path / "key.pem"
    key_file.write_text("session-key", encoding="utf-8")

    captured = {}

    monkeypatch.setattr(
        oci.config,
        "from_file",
        lambda profile_name: {
            "region": "us-ashburn-1",
            "security_token_file": str(token_file),
            "key_file": str(key_file),
        },
    )
    monkeypatch.setattr(oci.signer, "load_private_key_from_file", lambda path: f"key:{path}")
    monkeypatch.setattr(
        oci.auth.signers,
        "SecurityTokenSigner",
        lambda token, private_key: {"token": token, "private_key": private_key},
    )

    def fake_client(*, config, signer):
        captured["config"] = config
        captured["signer"] = signer
        return "object-storage-client"

    monkeypatch.setattr(oci.object_storage, "ObjectStorageClient", fake_client)

    client = create_object_storage_client(profile="OC1_ASH", region="us-phoenix-1")

    assert client == "object-storage-client"
    assert captured["config"]["region"] == "us-phoenix-1"
    assert captured["config"]["additional_user_agent"] == "oci-vision-mcp/0.1.0"
    assert captured["signer"] == {
        "token": "session-token",
        "private_key": f"key:{key_file}",
    }


def test_service_401_maps_to_session_auth_error() -> None:
    service_error = oci.exceptions.ServiceError(
        status=401,
        code="NotAuthenticated",
        headers={},
        message="session expired",
    )

    auth_error = session_auth_error_from_service_error(
        service_error,
        profile="OC1_ASH",
        region="us-ashburn-1",
    )

    assert auth_error is not None
    assert auth_error.retryable is True
    assert (
        "oci session authenticate --profile-name OC1_ASH --region us-ashburn-1"
        in str(auth_error)
    )
