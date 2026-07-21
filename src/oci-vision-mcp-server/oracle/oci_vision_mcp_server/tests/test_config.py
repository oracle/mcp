"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from oracle.oci_vision_mcp_server.config.settings import (
    McpConfigurationError,
    env_var_catalog,
    get_config_diagnostics,
    get_resolved_config,
)


def test_required_env_values_are_resolved_and_locked() -> None:
    config = get_resolved_config()

    assert config.profile == "OC1_ASH"
    assert config.region == "us-ashburn-1"
    assert config.default_compartment_id == "ocid1.compartment.oc1..example"
    assert config.locked_fields["profile"] is True
    assert config.locked_fields["region"] is True
    assert config.locked_fields["default_compartment_id"] is True


def test_missing_required_env_raises_clear_error(monkeypatch) -> None:
    monkeypatch.delenv("OCI_CONFIG_PROFILE", raising=False)

    with pytest.raises(McpConfigurationError) as exc_info:
        get_resolved_config()

    assert "OCI_CONFIG_PROFILE is required" in str(exc_info.value)
    assert "environment variable" in str(exc_info.value)


def test_config_diagnostics_reports_all_missing_required_values(monkeypatch) -> None:
    for name in ("OCI_CONFIG_PROFILE", "OCI_REGION", "OCI_VISION_DEFAULT_COMPARTMENT_ID"):
        monkeypatch.delenv(name, raising=False)

    status = get_config_diagnostics()

    assert status["valid"] is False
    assert status["missing_required_env_vars"] == [
        "OCI_CONFIG_PROFILE",
        "OCI_REGION",
        "OCI_VISION_DEFAULT_COMPARTMENT_ID",
    ]
    assert [error["code"] for error in status["errors"]] == [
        "MISSING_REQUIRED_ENV_VAR",
        "MISSING_REQUIRED_ENV_VAR",
        "MISSING_REQUIRED_ENV_VAR",
    ]
    assert status["values"]["profile"] == {
        "value": "",
        "source": "missing",
        "locked": False,
    }


def test_config_diagnostics_reports_invalid_optional_values_without_raising(monkeypatch) -> None:
    monkeypatch.setenv("MCP_MAX_IMAGE_BYTES", "not-an-int")

    status = get_config_diagnostics()

    assert status["valid"] is False
    assert status["missing_required_env_vars"] == []
    assert status["errors"] == [
        {
            "code": "INVALID_ENV_VAR",
            "env_var": "MCP_MAX_IMAGE_BYTES",
            "message": "MCP_MAX_IMAGE_BYTES must be a positive integer.",
            "retryable": False,
        }
    ]
    assert isinstance(status["values"]["max_image_bytes"]["value"], int)
    assert status["values"]["max_image_bytes"]["source"] == "default:invalid:MCP_MAX_IMAGE_BYTES"
    assert status["values"]["max_image_bytes"]["locked"] is False


def test_config_diagnostics_reports_invalid_image_base_path_without_raising(
    monkeypatch,
) -> None:
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", "~definitely_no_such_user_oci_vision/path")

    status = get_config_diagnostics()

    assert status["valid"] is False
    assert status["errors"][0]["env_var"] == "MCP_IMAGE_BASE_DIR"
    assert status["values"]["image_base_dir"]["source"] == (
        "default:invalid:MCP_IMAGE_BASE_DIR"
    )
    assert status["values"]["image_base_dir"]["locked"] is False


def test_config_diagnostics_marks_invalid_default_detail_as_fallback(monkeypatch) -> None:
    monkeypatch.setenv("OCI_VISION_DEFAULT_DETAIL", "everything")

    status = get_config_diagnostics()

    assert status["valid"] is False
    assert status["values"]["default_detail"] == {
        "value": "summary",
        "source": "default:invalid:OCI_VISION_DEFAULT_DETAIL",
        "locked": False,
    }


def test_auth_flags_default_to_public_repo_defaults() -> None:
    config = get_resolved_config()

    assert config.refresh_session is True
    assert config.auto_auth is False
    assert config.sources["refresh_session"] == "default"
    assert config.sources["auto_auth"] == "default"


def test_url_inputs_default_to_disabled() -> None:
    config = get_resolved_config()

    assert config.enable_url_inputs is False
    assert config.url_max_redirects == 3
    assert config.url_connect_timeout_seconds == 3.0
    assert config.url_read_timeout_seconds == 10.0
    assert config.sources["enable_url_inputs"] == "default"


def test_object_storage_upload_defaults_are_optional(monkeypatch) -> None:
    monkeypatch.delenv("OCI_OBJECT_STORAGE_NAMESPACE", raising=False)
    monkeypatch.delenv("OCI_OBJECT_STORAGE_BUCKET", raising=False)
    monkeypatch.delenv("OCI_OBJECT_STORAGE_OVERWRITE", raising=False)
    monkeypatch.delenv("OCI_VISION_JOB_OUTPUT_NAMESPACE", raising=False)
    monkeypatch.delenv("OCI_VISION_JOB_OUTPUT_BUCKET", raising=False)

    config = get_resolved_config()

    assert config.object_storage_namespace is None
    assert config.object_storage_bucket is None
    assert config.job_output_namespace is None
    assert config.job_output_bucket is None
    assert config.object_storage_overwrite is False
    assert config.locked_fields["object_storage_namespace"] is False
    assert config.locked_fields["object_storage_bucket"] is False
    assert config.locked_fields["job_output_namespace"] is False
    assert config.locked_fields["job_output_bucket"] is False
    assert config.locked_fields["object_storage_overwrite"] is False


def test_image_base_defaults_to_current_directory(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("MCP_IMAGE_BASE_DIR", raising=False)
    monkeypatch.chdir(tmp_path)

    config = get_resolved_config()

    assert config.image_base_dir == str(tmp_path.resolve())
    assert config.sources["image_base_dir"] == "default:cwd"


def test_optional_env_values_override_defaults(monkeypatch) -> None:
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", "/tmp/images")
    monkeypatch.setenv("MCP_MAX_IMAGE_BYTES", "1234")
    monkeypatch.setenv("OCI_MCP_REFRESH_SESSION", "0")
    monkeypatch.setenv("OCI_MCP_AUTO_AUTH", "0")
    monkeypatch.setenv("OCI_MCP_TOKEN_EXPIRY_SKEW_SECONDS", "60")
    monkeypatch.setenv("OCI_SESSION_AUTH_COMMAND", "ossh")
    monkeypatch.setenv("OCI_VISION_LOG_DIR", "/tmp/oci-vision-logs")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "bucket")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_OVERWRITE", "1")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_DOWNLOAD_DIR", "/tmp/oci-downloads")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_FETCH_MAX_BYTES", "4321")
    monkeypatch.setenv("OCI_VISION_ENABLE_URL_INPUTS", "true")
    monkeypatch.setenv("OCI_VISION_URL_MAX_REDIRECTS", "2")
    monkeypatch.setenv("OCI_VISION_URL_CONNECT_TIMEOUT_SECONDS", "1.5")
    monkeypatch.setenv("OCI_VISION_URL_READ_TIMEOUT_SECONDS", "4.5")

    config = get_resolved_config()

    assert config.image_base_dir == "/tmp/images"
    assert config.max_image_bytes == 1234
    assert config.refresh_session is False
    assert config.auto_auth is False
    assert config.token_expiry_skew_seconds == 60
    assert config.session_auth_command == "ossh"
    assert config.log_dir == "/tmp/oci-vision-logs"
    assert config.object_storage_namespace == "ns"
    assert config.object_storage_bucket == "bucket"
    assert config.job_output_namespace == "ns"
    assert config.job_output_bucket == "bucket"
    assert config.object_storage_overwrite is True
    assert config.object_storage_download_dir == str(Path("/tmp/oci-downloads").resolve(strict=False))
    assert config.object_storage_fetch_max_bytes == 4321
    assert config.enable_url_inputs is True
    assert config.url_max_redirects == 2
    assert config.url_connect_timeout_seconds == 1.5
    assert config.url_read_timeout_seconds == 4.5


def test_job_output_env_overrides_object_storage_defaults(monkeypatch) -> None:
    monkeypatch.setenv("OCI_OBJECT_STORAGE_NAMESPACE", "object_ns")
    monkeypatch.setenv("OCI_OBJECT_STORAGE_BUCKET", "object_bucket")
    monkeypatch.setenv("OCI_VISION_JOB_OUTPUT_NAMESPACE", "job_ns")
    monkeypatch.setenv("OCI_VISION_JOB_OUTPUT_BUCKET", "job_bucket")

    config = get_resolved_config()

    assert config.object_storage_namespace == "object_ns"
    assert config.object_storage_bucket == "object_bucket"
    assert config.job_output_namespace == "job_ns"
    assert config.job_output_bucket == "job_bucket"
    assert config.locked_fields["job_output_namespace"] is True
    assert config.locked_fields["job_output_bucket"] is True


def test_object_storage_download_dir_defaults_under_runtime_dir(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.delenv("OCI_OBJECT_STORAGE_DOWNLOAD_DIR", raising=False)

    config = get_resolved_config()

    assert config.object_storage_download_dir == str((Path.home() / ".oci-vision-mcp" / "obj_results").resolve())


def test_relative_object_storage_download_dir_resolves_under_image_base(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MCP_IMAGE_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("OCI_OBJECT_STORAGE_DOWNLOAD_DIR", "downloads")

    config = get_resolved_config()

    assert config.object_storage_download_dir == str(tmp_path / "downloads")


def test_invalid_integer_env_raises_configuration_error(monkeypatch) -> None:
    monkeypatch.setenv("MCP_MAX_IMAGE_BYTES", "not-an-int")

    with pytest.raises(McpConfigurationError) as exc_info:
        get_resolved_config()

    assert "MCP_MAX_IMAGE_BYTES must be a positive integer" in str(exc_info.value)


def test_invalid_boolean_env_raises_configuration_error(monkeypatch) -> None:
    monkeypatch.setenv("OCI_MCP_AUTO_AUTH", "maybe")

    with pytest.raises(McpConfigurationError) as exc_info:
        get_resolved_config()

    assert "OCI_MCP_AUTO_AUTH must be a boolean value" in str(exc_info.value)


def test_invalid_float_env_raises_configuration_error(monkeypatch) -> None:
    monkeypatch.setenv("OCI_VISION_URL_CONNECT_TIMEOUT_SECONDS", "slow")

    with pytest.raises(McpConfigurationError) as exc_info:
        get_resolved_config()

    assert "OCI_VISION_URL_CONNECT_TIMEOUT_SECONDS must be a positive number" in str(exc_info.value)


def test_runtime_dirs_default_to_client_neutral_directory(monkeypatch) -> None:
    monkeypatch.delenv("OCI_VISION_RESULT_STORE_DIR", raising=False)
    monkeypatch.delenv("OCI_VISION_LOG_DIR", raising=False)

    config = get_resolved_config()
    runtime_dir = Path.home() / ".oci-vision-mcp"

    assert config.result_store_dir == str(runtime_dir / "results")
    assert config.log_dir == str(runtime_dir / "logs")


def test_env_var_catalog_lists_required_and_optional_vars() -> None:
    catalog = env_var_catalog()
    names = {item["name"] for item in catalog}

    assert {
        "OCI_CONFIG_PROFILE",
        "OCI_REGION",
        "OCI_VISION_DEFAULT_COMPARTMENT_ID",
        "MCP_IMAGE_BASE_DIR",
        "MCP_MAX_IMAGE_BYTES",
        "OCI_MCP_REFRESH_SESSION",
        "OCI_MCP_AUTO_AUTH",
        "OCI_MCP_TOKEN_EXPIRY_SKEW_SECONDS",
        "OCI_SESSION_AUTH_COMMAND",
        "OCI_VISION_RESULT_STORE_DIR",
        "OCI_VISION_LOG_DIR",
        "OCI_VISION_RESULT_TTL_SECONDS",
        "OCI_VISION_MAX_INLINE_RESPONSE_BYTES",
            "OCI_VISION_DEFAULT_DETAIL",
            "OCI_VISION_JOB_OUTPUT_NAMESPACE",
            "OCI_VISION_JOB_OUTPUT_BUCKET",
            "OCI_OBJECT_STORAGE_NAMESPACE",
            "OCI_OBJECT_STORAGE_BUCKET",
            "OCI_OBJECT_STORAGE_OVERWRITE",
            "OCI_OBJECT_STORAGE_DOWNLOAD_DIR",
            "OCI_OBJECT_STORAGE_FETCH_MAX_BYTES",
            "OCI_VISION_ENABLE_URL_INPUTS",
            "OCI_VISION_URL_MAX_REDIRECTS",
            "OCI_VISION_URL_CONNECT_TIMEOUT_SECONDS",
            "OCI_VISION_URL_READ_TIMEOUT_SECONDS",
        } <= names


def test_session_auth_command_defaults_to_oci() -> None:
    config = get_resolved_config()

    assert config.session_auth_command == "oci"
    assert config.sources["session_auth_command"] == "default"
