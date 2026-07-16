"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import base64
import json
from types import SimpleNamespace

import oci
import pytest

from oracle.oci_vision_mcp_server.authentication import auth
from oracle.oci_vision_mcp_server.authentication.session_signer import (
    session_auth_error_from_service_error,
)
from oracle.oci_vision_mcp_server.config.consts import (
    FEATURE_FACE_DETECTION,
    FEATURE_TEXT_DETECTION,
    TOOL_DETECT_TEXT,
)
from oracle.oci_vision_mcp_server.config.schemas import (
    ImageAnalysisFeature,
    ImageInput,
    ImageSourceType,
    OciObjectInput,
    ParallelAnalyzeImageInput,
    ParallelAnalyzeImageItem,
    ResponseDetail,
    ToolOptions,
    VisionJobOutputInput,
    VisionToolInput,
)
from oracle.oci_vision_mcp_server.io.image_loader import ImageResolver, ImageResolverError
from oracle.oci_vision_mcp_server.oci_mapper.vision_results import render_response_dict, summary_text
from oracle.oci_vision_mcp_server.responses import errors as response_errors
from oracle.oci_vision_mcp_server import server as server_module
from oracle.oci_vision_mcp_server.tools.object_storage_tools import upload_image_to_object_storage as upload_tool
from oracle.oci_vision_mcp_server.tools.vision_api_tools import analyze_image as analyze_image_tool
from oracle.oci_vision_mcp_server.tools.vision_api_tools import image_jobs
from oracle.oci_vision_mcp_server.tools.vision_api_tools import parallel_analyze_image as parallel_tool
from oracle.oci_vision_mcp_server.tools.vision_api_tools import runner


def _jwt(payload: dict) -> str:
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii").rstrip("=")
    return f"header.{encoded}.signature"


def test_auth_helpers_cover_invalid_tokens_and_missing_config(monkeypatch, tmp_path) -> None:
    missing = auth.SessionConfig(profile="DEFAULT", region="us-ashburn-1", security_token_file=None)
    absent = auth.SessionConfig(profile="DEFAULT", region="us-ashburn-1", security_token_file=str(tmp_path / "token"))
    malformed = tmp_path / "malformed"
    malformed.write_text("not-a-jwt", encoding="utf-8")
    no_exp = tmp_path / "no-exp"
    no_exp.write_text(_jwt({"sub": "user"}), encoding="utf-8")

    assert auth._session_is_current(missing, skew_seconds=300) is False
    assert auth._session_is_current(absent, skew_seconds=300) is False
    assert auth._session_is_current(
        auth.SessionConfig("DEFAULT", "us-ashburn-1", str(malformed)),
        skew_seconds=300,
    ) is False
    assert auth._session_is_current(
        auth.SessionConfig("DEFAULT", "us-ashburn-1", str(no_exp)),
        skew_seconds=300,
    ) is False
    assert auth._jwt_expiry("bad-token") is None

    monkeypatch.setattr(auth.oci.config, "from_file", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("bad")))
    loaded = auth._load_session_config(
        SimpleNamespace(profile="DEFAULT", region="us-phoenix-1")
    )

    assert loaded.profile == "DEFAULT"
    assert loaded.region == "us-phoenix-1"
    assert loaded.security_token_file is None


def test_server_main_runs_shared_mcp_app(monkeypatch) -> None:
    called = []
    monkeypatch.setattr(server_module.mcp, "run", lambda: called.append("run"))

    server_module.main()

    assert called == ["run"]


def test_image_resolver_rejects_unsafe_or_invalid_inputs(tmp_path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    txt = base / "not-image.txt"
    txt.write_text("hello", encoding="utf-8")
    empty = base / "empty.png"
    empty.write_bytes(b"")
    big = base / "big.png"
    big.write_bytes(b"too-large")
    text_image = base / "text-image.txt"
    text_image.write_text("not actually an image", encoding="utf-8")
    resolver = ImageResolver(base_dir=str(base), max_image_bytes=4)

    with pytest.raises(ImageResolverError, match="stay under"):
        resolver.resolve_local_file(ImageInput(source_type=ImageSourceType.FILE_PATH, path="../x.png"))
    with pytest.raises(ImageResolverError, match="regular file"):
        resolver.resolve_local_file(ImageInput(source_type=ImageSourceType.FILE_PATH, path="missing.png"))
    with pytest.raises(ImageResolverError, match="extension"):
        resolver.resolve_local_file(ImageInput(source_type=ImageSourceType.FILE_PATH, path="not-image.txt"))
    with pytest.raises(ImageResolverError, match="empty"):
        resolver.resolve_local_file(ImageInput(source_type=ImageSourceType.FILE_PATH, path="empty.png"))
    with pytest.raises(ImageResolverError, match="MCP_MAX_IMAGE_BYTES"):
        resolver.resolve_local_file(ImageInput(source_type=ImageSourceType.FILE_PATH, path="big.png"))
    with pytest.raises(ImageResolverError, match="oci_object is required"):
        ImageResolver._object_storage(SimpleNamespace(oci_object=None))
    with pytest.raises(ImageResolverError, match="Unsupported image source type"):
        resolver.resolve(SimpleNamespace(source_type="bad"))
    with pytest.raises(ImageResolverError, match="supported image type"):
        ImageResolver(base_dir=str(base), allowed_extensions={".txt"}).resolve_local_file(
            ImageInput(source_type=ImageSourceType.FILE_PATH, path="text-image.txt")
        )


def test_ensure_session_auth_reports_auto_auth_and_manual_auth_paths(monkeypatch) -> None:
    auto_config = SimpleNamespace(
        profile="DEFAULT",
        region=None,
        token_expiry_skew_seconds=300,
        refresh_session=False,
        auto_auth=True,
        session_auth_command="oci",
    )
    manual_config = SimpleNamespace(
        profile="DEFAULT",
        region="us-ashburn-1",
        token_expiry_skew_seconds=300,
        refresh_session=False,
        auto_auth=False,
        session_auth_command="oci",
    )

    monkeypatch.setattr(auth, "_load_session_config", lambda _resolved: auth.SessionConfig("DEFAULT", None, None))
    monkeypatch.setattr(auth, "get_resolved_config", lambda **_kwargs: auto_config)
    with pytest.raises(RuntimeError, match="OCI region is required"):
        auth.ensure_session_auth()

    monkeypatch.setattr(auth, "get_resolved_config", lambda **_kwargs: manual_config)
    with pytest.raises(RuntimeError, match="oci session authenticate"):
        auth.ensure_session_auth()


def test_response_rendering_covers_text_faces_and_summary_variants() -> None:
    text_boxes = render_response_dict(
        {"image_text": {"text": "full", "lines": ["line one", {"text": "line two"}, None]}},
        tool=TOOL_DETECT_TEXT,
        feature_type=FEATURE_TEXT_DETECTION,
        request_id="REQ_TEXT",
        detail=ResponseDetail.BOXES,
        max_items=5,
        include_debug_metadata=False,
        include_full_text=True,
    )
    faces_standard = render_response_dict(
        {"detected_faces": [{"confidence": 0.7, "landmarks": []}]},
        tool="detect_faces",
        feature_type=FEATURE_FACE_DETECTION,
        request_id="REQ_FACE",
        detail=ResponseDetail.STANDARD,
        max_items=5,
        include_debug_metadata=True,
    )
    no_labels = render_response_dict(
        {"labels": []},
        tool="classify_image",
        feature_type="IMAGE_CLASSIFICATION",
        request_id="REQ_LABELS",
        detail=ResponseDetail.SUMMARY,
        max_items=5,
        include_debug_metadata=False,
    )

    assert text_boxes.detail == ResponseDetail.STANDARD
    assert text_boxes.results["text"]["lines"] == ["line one", {"text": "line two"}, None]
    assert text_boxes.warnings[0].code == "DETAIL_FALLBACK"
    assert faces_standard.results["faces"] == [{"confidence": 0.7}]
    assert "model_versions" not in faces_standard.debug_metadata
    assert summary_text(no_labels) == "Detected 0 labels."
    assert summary_text(faces_standard) == "Detected 1 faces."
    assert summary_text(text_boxes) == "Detected text with 3 lines."


def test_service_error_helpers_cover_auth_existing_and_header_paths() -> None:
    auth_error = oci.exceptions.ServiceError(
        status=401,
        code="NotAuthenticated",
        headers={},
        message="expired",
    )
    conflict = oci.exceptions.ServiceError(
        status=409,
        code="Other",
        headers={"opc-request-id": "REQ_HEADER"},
        message="conflict",
    )
    existing = oci.exceptions.ServiceError(
        status=412,
        code="PreconditionFailed",
        headers={},
        message="exists",
    )

    assert session_auth_error_from_service_error(RuntimeError("nope")) is None
    assert response_errors.upload_service_error_envelope(
        auth_error,
        profile="DEFAULT",
        region="us-ashburn-1",
        request_id="REQ",
    ).errors[0].code == "OCI_SESSION_AUTH_REQUIRED"
    assert response_errors.upload_service_error_envelope(existing, profile=None, region=None).errors[0].code == (
        "OBJECT_ALREADY_EXISTS"
    )
    assert response_errors.list_service_error_envelope(conflict, profile=None, region=None).errors[0].code == "Other"
    assert response_errors.response_request_id(SimpleNamespace(headers={"Opc-Request-Id": "REQ_HEADER"})) == "REQ_HEADER"
    assert response_errors.response_header(SimpleNamespace(headers={}), "opc-request-id") is None


def test_runner_handles_service_and_generic_exceptions(monkeypatch) -> None:
    monkeypatch.setattr(runner, "generate_request_id", lambda: "MCP_REQ")
    monkeypatch.setattr(runner, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(runner, "create_vision_client", lambda **_kwargs: object())

    def service_failure(*_args, **_kwargs):
        raise oci.exceptions.ServiceError(
            status=500,
            code="InternalError",
            headers={},
            message="service failed",
        )

    monkeypatch.setattr(runner, "call_analyze_image", service_failure)
    service_result = runner.run_vision_tool(
        tool="classify_image",
            feature_type="IMAGE_CLASSIFICATION",
            input_model=VisionToolInput,
            raw_args={
                "image": {"source_type": "base64", "data": "iVBORw0KGgpleGFtcGxl"},
                "compartment_id": "ocid1.compartment.oc1..example",
                "options": {"region": "us-chicago-1"},
            },
        feature_factory=lambda _args: object(),
    )

    monkeypatch.setattr(runner, "call_analyze_image", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    generic_result = runner.run_vision_tool(
        tool="classify_image",
            feature_type="IMAGE_CLASSIFICATION",
            input_model=VisionToolInput,
            raw_args={
                "image": {"source_type": "base64", "data": "iVBORw0KGgpleGFtcGxl"},
                "compartment_id": "ocid1.compartment.oc1..example",
            },
        feature_factory=lambda _args: object(),
    )

    assert service_result.isError is True
    assert service_result.structuredContent["errors"][0]["code"] == "InternalError"
    assert generic_result.isError is True
    assert generic_result.structuredContent["errors"][0]["code"] == "RuntimeError"


def test_public_tool_wrappers_forward_structured_arguments(monkeypatch) -> None:
    calls: list[tuple[str, dict, str]] = []
    sentinel = object()
    image = ImageInput(source_type=ImageSourceType.BASE64, data="iVBORw0KGgpleGFtcGxl")
    options = ToolOptions(detail=ResponseDetail.STANDARD)
    feature = ImageAnalysisFeature.TEXT_DETECTION
    obj = OciObjectInput(namespace="ns", bucket="bucket", object_name="image.png")
    output = VisionJobOutputInput(namespace="out_ns", bucket="out_bucket", prefix="results")

    monkeypatch.setattr(
        analyze_image_tool,
        "run_analyze_image_tool",
        lambda raw_args, *, tool: calls.append(("analyze", raw_args, tool)) or sentinel,
    )
    monkeypatch.setattr(
        image_jobs,
        "run_create_image_job_tool",
        lambda raw_args, *, tool: calls.append(("create_job", raw_args, tool)) or sentinel,
    )
    monkeypatch.setattr(
        image_jobs,
        "run_get_image_job_tool",
        lambda raw_args, *, tool: calls.append(("get_job", raw_args, tool)) or sentinel,
    )
    monkeypatch.setattr(
        image_jobs,
        "run_cancel_image_job_tool",
        lambda raw_args, *, tool: calls.append(("cancel_job", raw_args, tool)) or sentinel,
    )
    monkeypatch.setattr(
        parallel_tool,
        "run_parallel_analyze_image_tool",
        lambda raw_args, *, tool: calls.append(("parallel", raw_args, tool)) or sentinel,
    )

    assert analyze_image_tool.analyze_image(
        image=image,
        features=[feature],
        compartment_id="compartment",
        max_results=3,
        min_confidence=0.75,
        should_return_landmarks=True,
        include_full_text=False,
        options=options,
    ) is sentinel
    assert analyze_image_tool.analyze_image(image=image) is sentinel
    assert image_jobs.create_image_job(
        objects=[obj],
        features=[feature],
        output_location=output,
        compartment_id="compartment",
        display_name="job",
        is_zip_output_enabled=True,
        max_results=5,
        should_return_landmarks=True,
        options=options,
    ) is sentinel
    assert image_jobs.create_image_job(objects=[obj]) is sentinel
    assert image_jobs.get_image_job("ocid1.aivisionimagejob.oc1..example", options=options) is sentinel
    assert image_jobs.cancel_image_job(
        "ocid1.aivisionimagejob.oc1..example",
        confirm=True,
        options=options,
    ) is sentinel
    assert parallel_tool.parallel_analyze_image(
        items=[ParallelAnalyzeImageItem(image=image, features=[feature])],
        compartment_id="compartment",
        max_parallel=1,
        options=options,
    ) is sentinel

    assert calls[0] == (
        "analyze",
        {
            "image": image,
            "compartment_id": "compartment",
            "max_results": 3,
            "min_confidence": 0.75,
            "should_return_landmarks": True,
            "include_full_text": False,
            "options": options,
            "features": [feature],
        },
        "analyze_image",
    )
    assert "features" not in calls[1][1]
    assert calls[2][1]["objects"] == [obj]
    assert calls[2][1]["output_location"] == output
    assert calls[2][1]["features"] == [feature]
    assert "features" not in calls[3][1]
    assert calls[4][1] == {"job_id": "ocid1.aivisionimagejob.oc1..example", "options": options}
    assert calls[5][1] == {
        "job_id": "ocid1.aivisionimagejob.oc1..example",
        "confirm": True,
        "options": options,
    }
    assert calls[6][1]["max_parallel"] == 1
    assert calls[6][1]["items"][0].features == [feature]


def test_object_storage_upload_wrapper_and_helpers(monkeypatch) -> None:
    calls: list[dict[str, object]] = []
    sentinel = object()
    image = ImageInput(source_type=ImageSourceType.FILE_PATH, path="image.png")
    destination = upload_tool.ObjectStorageDestinationInput(
        namespace="ns",
        bucket="bucket",
        object_name="images/image.png",
    )
    options = upload_tool.ObjectStorageUploadOptions(detail=ResponseDetail.RAW)
    monkeypatch.setattr(upload_tool, "run_upload_tool", lambda raw_args: calls.append(raw_args) or sentinel)

    assert upload_tool.upload_image_to_object_storage(
        image=image,
        images=[image],
        destination=destination,
        destination_prefix="prefix",
        overwrite=True,
        content_type="image/png",
        metadata={"k": "v"},
        options=options,
    ) is sentinel

    assert calls[0]["image"] == image
    assert calls[0]["images"] == [image]
    assert calls[0]["destination"] == destination
    assert calls[0]["destination_prefix"] == "prefix"
    assert calls[0]["overwrite"] is True
    assert calls[0]["metadata"] == {"k": "v"}
    assert calls[0]["options"] == options

    assert upload_tool._bulk_object_name(None, "image.png") == "image.png"
    assert upload_tool._bulk_object_name("safe/prefix", "image.png") == "safe/prefix/image.png"
    with pytest.raises(ValueError, match="safe relative"):
        upload_tool._bulk_object_name("../bad", "image.png")
    assert upload_tool._selected_content_type(None, "image/png") == "image/png"
    with pytest.raises(ValueError, match="does not match"):
        upload_tool._selected_content_type("image/jpeg", "image/png")
    with pytest.raises(ValueError, match="unique"):
        upload_tool._reject_duplicate_upload_targets(["a.png", "a.png"])
    failed = upload_tool._failed_upload_item(
        image=image,
        error=upload_tool._error_detail(RuntimeError("boom")),
    )
    assert upload_tool._bulk_errors([failed])[0].code == "RuntimeError"


def test_parallel_item_error_paths_return_failed_items(monkeypatch) -> None:
    image = ImageInput(source_type=ImageSourceType.BASE64, data="iVBORw0KGgpleGFtcGxl")
    args = ParallelAnalyzeImageInput.model_validate(
        {
            "items": [{"image": image, "features": ["text_detection"]}],
            "compartment_id": "ocid1.compartment.oc1..example",
            "options": {"request_id": "CLIENT_REQ"},
        }
    )
    config = SimpleNamespace(
        profile="DEFAULT",
        default_compartment_id="ocid1.compartment.oc1..example",
    )

    class ResolverRaises:
        def resolve(self, _image):
            raise ValueError("bad image")

        def image_info(self, _image):
            return {"source_type": "base64"}

    monkeypatch.setattr(parallel_tool, "image_resolver_from_config", lambda _config: ResolverRaises())
    value_error_result = parallel_tool._analyze_one_item(
        index=0,
        item=args.items[0],
        args=args,
        resolved_config=config,
        region="us-phoenix-1",
        mcp_request_id="MCP_REQ",
    )

    class ResolverSucceeds:
        def resolve(self, _image):
            return object()

        def image_info(self, _image):
            return {"source_type": "base64"}

    monkeypatch.setattr(parallel_tool, "image_resolver_from_config", lambda _config: ResolverSucceeds())
    monkeypatch.setattr(parallel_tool, "create_vision_client", lambda **_kwargs: object())
    monkeypatch.setattr(
        parallel_tool,
        "call_analyze_image_features",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    runtime_error_result = parallel_tool._analyze_one_item(
        index=0,
        item=args.items[0],
        args=args,
        resolved_config=config,
        region="us-phoenix-1",
        mcp_request_id="MCP_REQ",
    )

    assert value_error_result["status"] == "failed"
    assert value_error_result["errors"][0].code == "ValueError"
    assert runtime_error_result["status"] == "failed"
    assert runtime_error_result["errors"][0].code == "RuntimeError"


def test_image_job_runner_success_and_error_paths(monkeypatch, tmp_path) -> None:
    config = SimpleNamespace(
        profile="DEFAULT",
        region="us-phoenix-1",
        default_compartment_id="ocid1.compartment.oc1..example",
        default_detail="summary",
        job_output_namespace="out_ns",
        job_output_bucket="out_bucket",
        result_store_dir=str(tmp_path),
        result_ttl_seconds=60,
        max_inline_response_bytes=20_000,
    )
    monkeypatch.setattr(runner, "generate_request_id", lambda: "JOB_REQ")
    monkeypatch.setattr(runner, "get_resolved_config", lambda **_kwargs: config)
    monkeypatch.setattr(runner, "ensure_session_auth", lambda: None)
    monkeypatch.setattr(runner, "create_vision_client", lambda **_kwargs: object())
    monkeypatch.setattr(runner, "create_image_job_payload_size", lambda **_kwargs: 100)
    monkeypatch.setattr(
        runner,
        "call_create_image_job",
        lambda *_args, **_kwargs: SimpleNamespace(
            data={
                "id": "ocid1.aivisionimagejob.oc1..example",
                "lifecycle_state": "ACCEPTED",
            },
            headers={"opc-request-id": "OCI_REQ", "opc-work-request-id": "WORK_REQ"},
            opc_request_id="OCI_REQ",
        ),
    )

    create_result = runner.run_create_image_job_tool(
        {
            "objects": [{"namespace": "in_ns", "bucket": "in_bucket", "object_name": "image.png"}],
            "features": ["text_detection"],
        },
        tool="create_image_job",
    )

    monkeypatch.setattr(
        runner,
        "call_get_image_job",
        lambda **_kwargs: SimpleNamespace(
            data={"id": "ocid1.aivisionimagejob.oc1..example", "lifecycle_state": "SUCCEEDED"},
            headers={"opc-request-id": "GET_REQ"},
        ),
    )
    get_result = runner.run_get_image_job_tool(
        {"job_id": "ocid1.aivisionimagejob.oc1..example", "options": {"request_id": "CLIENT_REQ"}},
        tool="get_image_job",
    )

    def service_failure(**_kwargs):
        raise oci.exceptions.ServiceError(
            status=500,
            code="InternalError",
            headers={},
            message="service failed",
        )

    monkeypatch.setattr(runner, "call_get_image_job", service_failure)
    service_result = runner.run_get_image_job_tool(
        {"job_id": "ocid1.aivisionimagejob.oc1..example"},
        tool="get_image_job",
    )

    monkeypatch.setattr(
        runner,
        "call_get_image_job",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    generic_result = runner.run_get_image_job_tool(
        {"job_id": "ocid1.aivisionimagejob.oc1..example"},
        tool="get_image_job",
    )

    no_output_config = SimpleNamespace(**{**config.__dict__, "job_output_namespace": None})
    monkeypatch.setattr(runner, "get_resolved_config", lambda **_kwargs: no_output_config)
    missing_namespace = runner.run_create_image_job_tool(
        {"objects": [{"namespace": "in_ns", "bucket": "in_bucket", "object_name": "image.png"}]},
        tool="create_image_job",
    )
    no_bucket_config = SimpleNamespace(**{**config.__dict__, "job_output_bucket": None})
    monkeypatch.setattr(runner, "get_resolved_config", lambda **_kwargs: no_bucket_config)
    missing_bucket = runner.run_create_image_job_tool(
        {
            "objects": [{"namespace": "in_ns", "bucket": "in_bucket", "object_name": "image.png"}],
            "output_location": {"namespace": "out_ns"},
        },
        tool="create_image_job",
    )

    assert create_result.isError is False
    assert create_result.structuredContent["results"]["summary"]["id"] == "ocid1.aivisionimagejob.oc1..example"
    assert create_result.structuredContent["request_id"] == "JOB_REQ"
    assert get_result.isError is False
    assert get_result.structuredContent["results"]["summary"]["lifecycle_state"] == "SUCCEEDED"
    assert service_result.isError is True
    assert service_result.structuredContent["errors"][0]["code"] == "InternalError"
    assert generic_result.isError is True
    assert generic_result.structuredContent["errors"][0]["code"] == "RuntimeError"
    assert missing_namespace.isError is True
    assert "output namespace" in missing_namespace.structuredContent["errors"][0]["message"]
    assert missing_bucket.isError is True
    assert "output bucket" in missing_bucket.structuredContent["errors"][0]["message"]
