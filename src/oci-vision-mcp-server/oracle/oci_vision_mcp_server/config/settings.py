"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Environment configuration for the OCI Vision MCP server.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .consts import (
    DEFAULT_AUTO_AUTH,
    DEFAULT_DETAIL,
    DEFAULT_ENABLE_URL_INPUTS,
    DEFAULT_EXPIRY_SKEW_SECONDS,
    DEFAULT_LOG_DIR,
    DEFAULT_MAX_IMAGE_BYTES,
    DEFAULT_MAX_INLINE_RESPONSE_BYTES,
    DEFAULT_OBJECT_STORAGE_DOWNLOAD_DIR,
    DEFAULT_OBJECT_STORAGE_FETCH_MAX_BYTES,
    DEFAULT_OBJECT_STORAGE_OVERWRITE,
    DEFAULT_REFRESH_SESSION,
    DEFAULT_RESULT_STORE_DIR,
    DEFAULT_RESULT_TTL_SECONDS,
    DEFAULT_SESSION_AUTH_COMMAND,
    DEFAULT_URL_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_URL_MAX_REDIRECTS,
    DEFAULT_URL_READ_TIMEOUT_SECONDS,
    SESSION_AUTH_COMMAND_ENV,
)

ENV_PROFILE = "OCI_CONFIG_PROFILE"
ENV_REGION = "OCI_REGION"
ENV_DEFAULT_COMPARTMENT_ID = "OCI_VISION_DEFAULT_COMPARTMENT_ID"
ENV_IMAGE_BASE_DIR = "MCP_IMAGE_BASE_DIR"
ENV_MAX_IMAGE_BYTES = "MCP_MAX_IMAGE_BYTES"
ENV_REFRESH_SESSION = "OCI_MCP_REFRESH_SESSION"
ENV_AUTO_AUTH = "OCI_MCP_AUTO_AUTH"
ENV_EXPIRY_SKEW_SECONDS = "OCI_MCP_TOKEN_EXPIRY_SKEW_SECONDS"
ENV_RESULT_STORE_DIR = "OCI_VISION_RESULT_STORE_DIR"
ENV_LOG_DIR = "OCI_VISION_LOG_DIR"
ENV_RESULT_TTL_SECONDS = "OCI_VISION_RESULT_TTL_SECONDS"
ENV_MAX_INLINE_RESPONSE_BYTES = "OCI_VISION_MAX_INLINE_RESPONSE_BYTES"
ENV_DEFAULT_DETAIL = "OCI_VISION_DEFAULT_DETAIL"
ENV_JOB_OUTPUT_NAMESPACE = "OCI_VISION_JOB_OUTPUT_NAMESPACE"
ENV_JOB_OUTPUT_BUCKET = "OCI_VISION_JOB_OUTPUT_BUCKET"
ENV_OBJECT_STORAGE_NAMESPACE = "OCI_OBJECT_STORAGE_NAMESPACE"
ENV_OBJECT_STORAGE_BUCKET = "OCI_OBJECT_STORAGE_BUCKET"
ENV_OBJECT_STORAGE_OVERWRITE = "OCI_OBJECT_STORAGE_OVERWRITE"
ENV_OBJECT_STORAGE_DOWNLOAD_DIR = "OCI_OBJECT_STORAGE_DOWNLOAD_DIR"
ENV_OBJECT_STORAGE_FETCH_MAX_BYTES = "OCI_OBJECT_STORAGE_FETCH_MAX_BYTES"
ENV_ENABLE_URL_INPUTS = "OCI_VISION_ENABLE_URL_INPUTS"
ENV_URL_MAX_REDIRECTS = "OCI_VISION_URL_MAX_REDIRECTS"
ENV_URL_CONNECT_TIMEOUT_SECONDS = "OCI_VISION_URL_CONNECT_TIMEOUT_SECONDS"
ENV_URL_READ_TIMEOUT_SECONDS = "OCI_VISION_URL_READ_TIMEOUT_SECONDS"


class McpConfigurationError(RuntimeError):
    """Raised when required MCP environment configuration is missing."""


@dataclass(frozen=True)
class EnvVarInfo:
    name: str
    purpose: str
    required: bool
    default: str
    used_in: str
    effect: str


@dataclass(frozen=True)
class ResolvedMcpConfig:
    profile: str
    region: str
    default_compartment_id: str
    image_base_dir: str
    max_image_bytes: int
    refresh_session: bool
    auto_auth: bool
    token_expiry_skew_seconds: int
    session_auth_command: str
    result_store_dir: str
    log_dir: str
    result_ttl_seconds: int
    max_inline_response_bytes: int
    default_detail: str
    job_output_namespace: str | None
    job_output_bucket: str | None
    object_storage_namespace: str | None
    object_storage_bucket: str | None
    object_storage_overwrite: bool
    object_storage_download_dir: str
    object_storage_fetch_max_bytes: int
    enable_url_inputs: bool
    url_max_redirects: int
    url_connect_timeout_seconds: float
    url_read_timeout_seconds: float
    sources: dict[str, str]
    locked_fields: dict[str, bool]

    def status(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "profile": self.profile,
            "region": self.region,
            "default_compartment_id": self.default_compartment_id,
            "image_base_dir": self.image_base_dir,
            "max_image_bytes": self.max_image_bytes,
            "refresh_session": self.refresh_session,
            "auto_auth": self.auto_auth,
            "token_expiry_skew_seconds": self.token_expiry_skew_seconds,
            "session_auth_command": self.session_auth_command,
            "result_store_dir": self.result_store_dir,
            "log_dir": self.log_dir,
            "result_ttl_seconds": self.result_ttl_seconds,
            "max_inline_response_bytes": self.max_inline_response_bytes,
            "default_detail": self.default_detail,
            "job_output_namespace": self.job_output_namespace,
            "job_output_bucket": self.job_output_bucket,
            "object_storage_namespace": self.object_storage_namespace,
            "object_storage_bucket": self.object_storage_bucket,
            "object_storage_overwrite": self.object_storage_overwrite,
            "object_storage_download_dir": self.object_storage_download_dir,
            "object_storage_fetch_max_bytes": self.object_storage_fetch_max_bytes,
            "enable_url_inputs": self.enable_url_inputs,
            "url_max_redirects": self.url_max_redirects,
            "url_connect_timeout_seconds": self.url_connect_timeout_seconds,
            "url_read_timeout_seconds": self.url_read_timeout_seconds,
        }
        return {
            "configuration_source": "process_environment",
            "values": {
                key: {
                    "value": value,
                    "source": self.sources.get(key, "unknown"),
                    "locked": self.locked_fields.get(key, False),
                }
                for key, value in values.items()
            },
            "required_env_vars": [
                ENV_PROFILE,
                ENV_REGION,
                ENV_DEFAULT_COMPARTMENT_ID,
            ],
            "note": (
                "Required values must be provided as environment variables by the MCP client "
                "configuration, a runner script, or the launching shell."
            ),
        }


ENV_VAR_CATALOG: tuple[EnvVarInfo, ...] = (
    EnvVarInfo(
        name=ENV_PROFILE,
        purpose="OCI CLI profile used for session-token auth.",
        required=True,
        default="none",
        used_in="config/settings.py, authentication/auth.py, authentication/session_signer.py, oci_clients/vision.py, oci_clients/object_storage.py",
        effect="Selects the OCI profile read from ~/.oci/config.",
    ),
    EnvVarInfo(
        name=ENV_REGION,
        purpose="OCI region for session authentication and Vision endpoint.",
        required=True,
        default="none",
        used_in="config/settings.py, authentication/auth.py, authentication/session_signer.py, oci_clients/vision.py, oci_clients/object_storage.py",
        effect="Sets the region for session auth and AIServiceVisionClient.",
    ),
    EnvVarInfo(
        name=ENV_DEFAULT_COMPARTMENT_ID,
        purpose="Default compartment OCID for Vision tool calls.",
        required=True,
        default="none",
        used_in="config/settings.py, tools/vision_api_tools/runner.py",
        effect="Used when a tool call does not provide compartment_id.",
    ),
    EnvVarInfo(
        name=ENV_IMAGE_BASE_DIR,
        purpose="Filesystem sandbox for file_path image inputs.",
        required=False,
        default="current working directory",
        used_in="config/settings.py, tools/vision_api_tools/runner.py, tools/object_storage_tools/upload_image_to_object_storage.py, io/image_loader.py",
        effect="Only files under this directory can be read for file_path images.",
    ),
    EnvVarInfo(
        name=ENV_MAX_IMAGE_BYTES,
        purpose="Maximum accepted image size in bytes.",
        required=False,
        default=str(DEFAULT_MAX_IMAGE_BYTES),
        used_in="config/settings.py, io/image_loader.py",
        effect="Images larger than this are rejected before OCI calls.",
    ),
    EnvVarInfo(
        name=ENV_REFRESH_SESSION,
        purpose="Allow startup to refresh expired OCI session tokens.",
        required=False,
        default="true",
        used_in="config/settings.py, authentication/auth.py",
        effect=(
            "When true, startup and tool calls may run "
            "`<session_auth_command> session refresh --profile <profile>`."
        ),
    ),
    EnvVarInfo(
        name=ENV_AUTO_AUTH,
        purpose="Allow startup to run browser-based session authentication.",
        required=False,
        default="true",
        used_in="config/settings.py, authentication/auth.py",
        effect=(
            "When true, startup and tool calls may run "
            "`<session_auth_command> session authenticate` if refresh is insufficient."
        ),
    ),
    EnvVarInfo(
        name=ENV_EXPIRY_SKEW_SECONDS,
        purpose="Seconds before token expiry to treat the session as stale.",
        required=False,
        default=str(DEFAULT_EXPIRY_SKEW_SECONDS),
        used_in="config/settings.py, authentication/auth.py",
        effect="Controls how early startup and tool calls refresh/authenticate.",
    ),
    EnvVarInfo(
        name=SESSION_AUTH_COMMAND_ENV,
        purpose="CLI executable used for OCI session commands.",
        required=False,
        default=DEFAULT_SESSION_AUTH_COMMAND,
        used_in="config/settings.py, authentication/auth.py, authentication/session_signer.py",
        effect="Defaults to `oci`; set to another compatible executable only when the environment requires it.",
    ),
    EnvVarInfo(
        name=ENV_RESULT_STORE_DIR,
        purpose="Directory for stored OCI Vision analysis results.",
        required=False,
        default="~/.oci-vision-mcp/results",
        used_in="config/settings.py, io/result_store.py, tools/vision_api_tools/runner.py, tools/support_tools/get_analysis_result.py",
        effect="Controls where raw and metadata result files are written.",
    ),
    EnvVarInfo(
        name=ENV_LOG_DIR,
        purpose="Directory for MCP server diagnostic logs.",
        required=False,
        default="~/.oci-vision-mcp/logs",
        used_in="config/settings.py, observability/stderr.py, runtime/launcher.py",
        effect="Controls where launcher/server stderr is mirrored for diagnostics.",
    ),
    EnvVarInfo(
        name=ENV_RESULT_TTL_SECONDS,
        purpose="Seconds to keep locally stored analysis results.",
        required=False,
        default=str(DEFAULT_RESULT_TTL_SECONDS),
        used_in="config/settings.py, io/result_store.py",
        effect="Expired results are treated as unavailable and may be cleaned up.",
    ),
    EnvVarInfo(
        name=ENV_MAX_INLINE_RESPONSE_BYTES,
        purpose="Maximum bytes allowed for inline raw result responses.",
        required=False,
        default=str(DEFAULT_MAX_INLINE_RESPONSE_BYTES),
        used_in="config/settings.py, oci_mapper/vision_results.py, io/result_store.py",
        effect="Large raw responses return a filesystem path instead of inline JSON.",
    ),
    EnvVarInfo(
        name=ENV_DEFAULT_DETAIL,
        purpose="Default response detail mode for Vision tools.",
        required=False,
        default=DEFAULT_DETAIL,
        used_in="config/settings.py, tools/vision_api_tools/runner.py, oci_mapper/vision_results.py",
        effect="Controls the detail mode when a tool call omits options.detail.",
    ),
    EnvVarInfo(
        name=ENV_JOB_OUTPUT_NAMESPACE,
        purpose="Default Object Storage namespace for async image job outputs.",
        required=False,
        default=f"same as {ENV_OBJECT_STORAGE_NAMESPACE}",
        used_in="config/settings.py, tools/vision_api_tools/image_jobs.py",
        effect="Used by create_image_job when output_location.namespace is omitted.",
    ),
    EnvVarInfo(
        name=ENV_JOB_OUTPUT_BUCKET,
        purpose="Default Object Storage bucket for async image job outputs.",
        required=False,
        default=f"same as {ENV_OBJECT_STORAGE_BUCKET}",
        used_in="config/settings.py, tools/vision_api_tools/image_jobs.py",
        effect="Used by create_image_job when output_location.bucket is omitted.",
    ),
    EnvVarInfo(
        name=ENV_OBJECT_STORAGE_NAMESPACE,
        purpose="Default Object Storage namespace for upload, list, fetch, and image job output.",
        required=False,
        default="none",
        used_in="config/settings.py, tools/object_storage_tools/upload_image_to_object_storage.py, tools/object_storage_tools/list_object_storage_objects.py, tools/object_storage_tools/fetch_object_storage_object.py",
        effect="Used when Object Storage tools omit namespace.",
    ),
    EnvVarInfo(
        name=ENV_OBJECT_STORAGE_BUCKET,
        purpose="Default Object Storage bucket for upload, list, fetch, and image job output.",
        required=False,
        default="none",
        used_in="config/settings.py, tools/object_storage_tools/upload_image_to_object_storage.py, tools/object_storage_tools/list_object_storage_objects.py, tools/object_storage_tools/fetch_object_storage_object.py",
        effect="Used when Object Storage tools omit bucket.",
    ),
    EnvVarInfo(
        name=ENV_OBJECT_STORAGE_OVERWRITE,
        purpose="Default overwrite behavior for image uploads.",
        required=False,
        default="false",
        used_in="config/settings.py, tools/object_storage_tools/upload_image_to_object_storage.py, oci_clients/object_storage.py",
        effect="When true and a tool call omits overwrite, uploads may replace existing objects.",
    ),
    EnvVarInfo(
        name=ENV_OBJECT_STORAGE_DOWNLOAD_DIR,
        purpose="Local directory for fetched Object Storage objects.",
        required=False,
        default="~/.oci-vision-mcp/obj_results",
        used_in="config/settings.py, tools/object_storage_tools/fetch_object_storage_object.py",
        effect="Fetched objects are saved under this directory. It may be outside MCP_IMAGE_BASE_DIR.",
    ),
    EnvVarInfo(
        name=ENV_OBJECT_STORAGE_FETCH_MAX_BYTES,
        purpose="Maximum object size that fetch_object_storage_object will download.",
        required=False,
        default=str(DEFAULT_OBJECT_STORAGE_FETCH_MAX_BYTES),
        used_in="config/settings.py, tools/object_storage_tools/fetch_object_storage_object.py",
        effect="Objects larger than this are rejected or interrupted during download.",
    ),
    EnvVarInfo(
        name=ENV_ENABLE_URL_INPUTS,
        purpose="Enable HTTPS URL image inputs.",
        required=False,
        default=str(DEFAULT_ENABLE_URL_INPUTS).lower(),
        used_in="config/settings.py, io/image_loader.py, io/url_image_loader.py",
        effect="When false, source_type=url image inputs are rejected before network access.",
    ),
    EnvVarInfo(
        name=ENV_URL_MAX_REDIRECTS,
        purpose="Maximum redirects followed for HTTPS URL image inputs.",
        required=False,
        default=str(DEFAULT_URL_MAX_REDIRECTS),
        used_in="config/settings.py, io/url_image_loader.py",
        effect="Every redirect target is validated with the same SSRF protections.",
    ),
    EnvVarInfo(
        name=ENV_URL_CONNECT_TIMEOUT_SECONDS,
        purpose="Connect timeout for HTTPS URL image inputs.",
        required=False,
        default=str(DEFAULT_URL_CONNECT_TIMEOUT_SECONDS),
        used_in="config/settings.py, io/url_image_loader.py",
        effect="Limits how long the server waits while opening a URL connection.",
    ),
    EnvVarInfo(
        name=ENV_URL_READ_TIMEOUT_SECONDS,
        purpose="Read timeout for HTTPS URL image inputs.",
        required=False,
        default=str(DEFAULT_URL_READ_TIMEOUT_SECONDS),
        used_in="config/settings.py, io/url_image_loader.py",
        effect="Limits how long the server waits while reading URL image bytes.",
    ),
)


def get_resolved_config(
    *,
    persist_generated_profile: bool = False,
    _allow_missing_required: bool = False,
    _diagnostic_errors: list[dict[str, Any]] | None = None,
) -> ResolvedMcpConfig:
    # Kept for compatibility with older launcher calls; config now comes only
    # from process environment variables and code defaults.
    del persist_generated_profile
    sources: dict[str, str] = {}
    locked: dict[str, bool] = {}

    profile = _required_env(
        ENV_PROFILE,
        "profile",
        sources,
        locked,
        allow_missing=_allow_missing_required,
    )
    region = _required_env(
        ENV_REGION,
        "region",
        sources,
        locked,
        allow_missing=_allow_missing_required,
    )
    default_compartment_id = _required_env(
        ENV_DEFAULT_COMPARTMENT_ID,
        "default_compartment_id",
        sources,
        locked,
        allow_missing=_allow_missing_required,
    )
    image_base_dir = _resolve_image_base_dir(
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    max_image_bytes = _resolve_int(
        "max_image_bytes",
        env_name=ENV_MAX_IMAGE_BYTES,
        default=DEFAULT_MAX_IMAGE_BYTES,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    refresh_session = _resolve_bool(
        "refresh_session",
        env_name=ENV_REFRESH_SESSION,
        default=DEFAULT_REFRESH_SESSION,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    auto_auth = _resolve_bool(
        "auto_auth",
        env_name=ENV_AUTO_AUTH,
        default=DEFAULT_AUTO_AUTH,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    token_expiry_skew_seconds = _resolve_int(
        "token_expiry_skew_seconds",
        env_name=ENV_EXPIRY_SKEW_SECONDS,
        default=DEFAULT_EXPIRY_SKEW_SECONDS,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    session_auth_command = _resolve_string(
        "session_auth_command",
        env_name=SESSION_AUTH_COMMAND_ENV,
        sources=sources,
        locked=locked,
        default=DEFAULT_SESSION_AUTH_COMMAND,
        default_source="default",
    )
    result_store_dir = _resolve_string(
        "result_store_dir",
        env_name=ENV_RESULT_STORE_DIR,
        sources=sources,
        locked=locked,
        default=str(DEFAULT_RESULT_STORE_DIR),
        default_source="default",
    )
    log_dir = _resolve_string(
        "log_dir",
        env_name=ENV_LOG_DIR,
        sources=sources,
        locked=locked,
        default=str(DEFAULT_LOG_DIR),
        default_source="default",
    )
    result_ttl_seconds = _resolve_int(
        "result_ttl_seconds",
        env_name=ENV_RESULT_TTL_SECONDS,
        default=DEFAULT_RESULT_TTL_SECONDS,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    max_inline_response_bytes = _resolve_int(
        "max_inline_response_bytes",
        env_name=ENV_MAX_INLINE_RESPONSE_BYTES,
        default=DEFAULT_MAX_INLINE_RESPONSE_BYTES,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    default_detail = _resolve_string(
        "default_detail",
        env_name=ENV_DEFAULT_DETAIL,
        sources=sources,
        locked=locked,
        default=DEFAULT_DETAIL,
        default_source="default",
    )
    if default_detail not in {"summary", "standard", "boxes", "raw"}:
        if _diagnostic_errors is not None:
            _diagnostic_errors.append(
                _configuration_error(
                    ENV_DEFAULT_DETAIL,
                    f"{ENV_DEFAULT_DETAIL} must be one of summary, standard, boxes, or raw.",
                )
            )
        default_detail = DEFAULT_DETAIL
        sources["default_detail"] = f"default:invalid:{ENV_DEFAULT_DETAIL}"
        locked["default_detail"] = False
    object_storage_namespace = _resolve_optional_string(
        "object_storage_namespace",
        env_name=ENV_OBJECT_STORAGE_NAMESPACE,
        sources=sources,
        locked=locked,
    )
    object_storage_bucket = _resolve_optional_string(
        "object_storage_bucket",
        env_name=ENV_OBJECT_STORAGE_BUCKET,
        sources=sources,
        locked=locked,
    )
    job_output_namespace = _resolve_optional_with_fallback(
        "job_output_namespace",
        env_name=ENV_JOB_OUTPUT_NAMESPACE,
        fallback=object_storage_namespace,
        fallback_source="default:object_storage_namespace",
        sources=sources,
        locked=locked,
    )
    job_output_bucket = _resolve_optional_with_fallback(
        "job_output_bucket",
        env_name=ENV_JOB_OUTPUT_BUCKET,
        fallback=object_storage_bucket,
        fallback_source="default:object_storage_bucket",
        sources=sources,
        locked=locked,
    )
    object_storage_overwrite = _resolve_bool(
        "object_storage_overwrite",
        env_name=ENV_OBJECT_STORAGE_OVERWRITE,
        default=DEFAULT_OBJECT_STORAGE_OVERWRITE,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    object_storage_download_dir = _resolve_download_dir(
        image_base_dir=image_base_dir,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    object_storage_fetch_max_bytes = _resolve_int(
        "object_storage_fetch_max_bytes",
        env_name=ENV_OBJECT_STORAGE_FETCH_MAX_BYTES,
        default=DEFAULT_OBJECT_STORAGE_FETCH_MAX_BYTES,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    enable_url_inputs = _resolve_bool(
        "enable_url_inputs",
        env_name=ENV_ENABLE_URL_INPUTS,
        default=DEFAULT_ENABLE_URL_INPUTS,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    url_max_redirects = _resolve_int(
        "url_max_redirects",
        env_name=ENV_URL_MAX_REDIRECTS,
        default=DEFAULT_URL_MAX_REDIRECTS,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    url_connect_timeout_seconds = _resolve_float(
        "url_connect_timeout_seconds",
        env_name=ENV_URL_CONNECT_TIMEOUT_SECONDS,
        default=DEFAULT_URL_CONNECT_TIMEOUT_SECONDS,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )
    url_read_timeout_seconds = _resolve_float(
        "url_read_timeout_seconds",
        env_name=ENV_URL_READ_TIMEOUT_SECONDS,
        default=DEFAULT_URL_READ_TIMEOUT_SECONDS,
        sources=sources,
        locked=locked,
        diagnostic_errors=_diagnostic_errors,
    )

    return ResolvedMcpConfig(
        profile=profile,
        region=region,
        default_compartment_id=default_compartment_id,
        image_base_dir=image_base_dir,
        max_image_bytes=max_image_bytes,
        refresh_session=refresh_session,
        auto_auth=auto_auth,
        token_expiry_skew_seconds=token_expiry_skew_seconds,
        session_auth_command=session_auth_command,
        result_store_dir=result_store_dir,
        log_dir=log_dir,
        result_ttl_seconds=result_ttl_seconds,
        max_inline_response_bytes=max_inline_response_bytes,
        default_detail=default_detail,
        job_output_namespace=job_output_namespace,
        job_output_bucket=job_output_bucket,
        object_storage_namespace=object_storage_namespace,
        object_storage_bucket=object_storage_bucket,
        object_storage_overwrite=object_storage_overwrite,
        object_storage_download_dir=object_storage_download_dir,
        object_storage_fetch_max_bytes=object_storage_fetch_max_bytes,
        enable_url_inputs=enable_url_inputs,
        url_max_redirects=url_max_redirects,
        url_connect_timeout_seconds=url_connect_timeout_seconds,
        url_read_timeout_seconds=url_read_timeout_seconds,
        sources=sources,
        locked_fields=locked,
    )


def get_config_diagnostics() -> dict[str, Any]:
    """Return a complete, non-secret config report without requiring valid config."""

    validation_errors: list[dict[str, Any]] = []
    config = get_resolved_config(
        persist_generated_profile=True,
        _allow_missing_required=True,
        _diagnostic_errors=validation_errors,
    )
    required_env_vars = [ENV_PROFILE, ENV_REGION, ENV_DEFAULT_COMPARTMENT_ID]
    missing_required_env_vars = [name for name in required_env_vars if _env_value(name) is None]
    missing_errors = [
        _configuration_error(
            name,
            (
                f"{name} is required. Set it in your MCP client environment, "
                "runner script, or launching shell."
            ),
            code="MISSING_REQUIRED_ENV_VAR",
        )
        for name in missing_required_env_vars
    ]

    status = config.status()
    status.update(
        {
            "valid": not missing_errors and not validation_errors,
            "missing_required_env_vars": missing_required_env_vars,
            "errors": [*missing_errors, *validation_errors],
        }
    )
    return status


def env_var_catalog() -> list[dict[str, Any]]:
    return [
        {
            "name": item.name,
            "purpose": item.purpose,
            "required": item.required,
            "default": item.default,
            "used_in": item.used_in,
            "effect": item.effect,
        }
        for item in ENV_VAR_CATALOG
    ]


def _required_env(
    name: str,
    field: str,
    sources: dict[str, str],
    locked: dict[str, bool],
    *,
    allow_missing: bool = False,
) -> str:
    value, source = _configured_value(name)
    if not value:
        if allow_missing:
            sources[field] = "missing"
            locked[field] = False
            return ""
        raise McpConfigurationError(
            f"{name} is required. Set it as an environment variable in your MCP client "
            "configuration, runner script, or launching shell, then restart the MCP server."
        )
    sources[field] = source
    locked[field] = True
    return value


def _resolve_string(
    field: str,
    *,
    env_name: str,
    sources: dict[str, str],
    locked: dict[str, bool],
    default: str,
    default_source: str,
) -> str:
    configured, source = _configured_value(env_name)
    if configured:
        sources[field] = source
        locked[field] = True
        return configured
    sources[field] = default_source
    locked[field] = False
    return default


def _resolve_image_base_dir(
    *,
    sources: dict[str, str],
    locked: dict[str, bool],
    diagnostic_errors: list[dict[str, Any]] | None = None,
) -> str:
    configured, source = _configured_value(ENV_IMAGE_BASE_DIR)
    selected = configured or str(Path.cwd())
    try:
        expanded = Path(selected).expanduser()
        resolved = expanded if expanded.is_absolute() else Path.cwd() / expanded
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        message = f"{ENV_IMAGE_BASE_DIR} must be a valid filesystem path: {exc}"
        if diagnostic_errors is None:
            raise McpConfigurationError(message) from exc
        diagnostic_errors.append(_configuration_error(ENV_IMAGE_BASE_DIR, message))
        sources["image_base_dir"] = f"default:invalid:{ENV_IMAGE_BASE_DIR}"
        locked["image_base_dir"] = False
        return str(Path.cwd().resolve(strict=False))
    sources["image_base_dir"] = source if configured else "default:cwd"
    locked["image_base_dir"] = bool(configured)
    return str(resolved)


def _resolve_optional_string(
    field: str,
    *,
    env_name: str,
    sources: dict[str, str],
    locked: dict[str, bool],
) -> str | None:
    configured, source = _configured_value(env_name)
    if configured:
        sources[field] = source
        locked[field] = True
        return configured
    sources[field] = "default"
    locked[field] = False
    return None


def _resolve_optional_with_fallback(
    field: str,
    *,
    env_name: str,
    fallback: str | None,
    fallback_source: str,
    sources: dict[str, str],
    locked: dict[str, bool],
) -> str | None:
    configured, source = _configured_value(env_name)
    if configured:
        sources[field] = source
        locked[field] = True
        return configured
    sources[field] = fallback_source if fallback else "default"
    locked[field] = False
    return fallback


def _resolve_int(
    field: str,
    *,
    env_name: str,
    default: int,
    sources: dict[str, str],
    locked: dict[str, bool],
    diagnostic_errors: list[dict[str, Any]] | None = None,
) -> int:
    configured, source = _configured_value(env_name)
    if configured:
        sources[field] = source
        locked[field] = True
        try:
            return _int_value(configured, env_name=env_name)
        except McpConfigurationError as exc:
            if diagnostic_errors is None:
                raise
            diagnostic_errors.append(_configuration_error(env_name, str(exc)))
            sources[field] = f"default:invalid:{env_name}"
            locked[field] = False
            return default
    sources[field] = "default"
    locked[field] = False
    return default


def _resolve_float(
    field: str,
    *,
    env_name: str,
    default: float,
    sources: dict[str, str],
    locked: dict[str, bool],
    diagnostic_errors: list[dict[str, Any]] | None = None,
) -> float:
    configured, source = _configured_value(env_name)
    if configured:
        sources[field] = source
        locked[field] = True
        try:
            return _float_value(configured, env_name=env_name)
        except McpConfigurationError as exc:
            if diagnostic_errors is None:
                raise
            diagnostic_errors.append(_configuration_error(env_name, str(exc)))
            sources[field] = f"default:invalid:{env_name}"
            locked[field] = False
            return default
    sources[field] = "default"
    locked[field] = False
    return default


def _resolve_bool(
    field: str,
    *,
    env_name: str,
    default: bool,
    sources: dict[str, str],
    locked: dict[str, bool],
    diagnostic_errors: list[dict[str, Any]] | None = None,
) -> bool:
    configured, source = _configured_value(env_name)
    if configured is not None:
        sources[field] = source
        locked[field] = True
        try:
            return _bool_value(configured, env_name=env_name)
        except McpConfigurationError as exc:
            if diagnostic_errors is None:
                raise
            diagnostic_errors.append(_configuration_error(env_name, str(exc)))
            sources[field] = f"default:invalid:{env_name}"
            locked[field] = False
            return default
    sources[field] = "default"
    locked[field] = False
    return default


def _resolve_download_dir(
    *,
    image_base_dir: str,
    sources: dict[str, str],
    locked: dict[str, bool],
    diagnostic_errors: list[dict[str, Any]] | None = None,
) -> str:
    configured, source = _configured_value(ENV_OBJECT_STORAGE_DOWNLOAD_DIR)
    try:
        base_dir = Path(image_base_dir).expanduser().resolve(strict=False)
        if configured:
            candidate = Path(configured).expanduser()
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            resolved = candidate.resolve(strict=False)
            sources["object_storage_download_dir"] = source
            locked["object_storage_download_dir"] = True
            return str(resolved)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        message = f"{ENV_OBJECT_STORAGE_DOWNLOAD_DIR} must be a valid filesystem path: {exc}"
        if diagnostic_errors is None:
            raise McpConfigurationError(message) from exc
        diagnostic_errors.append(
            _configuration_error(ENV_OBJECT_STORAGE_DOWNLOAD_DIR, message)
        )
        sources["object_storage_download_dir"] = (
            f"default:invalid:{ENV_OBJECT_STORAGE_DOWNLOAD_DIR}"
        )
        locked["object_storage_download_dir"] = False
        return str(Path.cwd().resolve(strict=False))

    sources["object_storage_download_dir"] = "default"
    locked["object_storage_download_dir"] = False
    return str(DEFAULT_OBJECT_STORAGE_DOWNLOAD_DIR.expanduser().resolve(strict=False))


def _env_value(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _configured_value(name: str) -> tuple[str | None, str]:
    env = _env_value(name)
    if env is not None:
        return env, f"env:{name}"
    return None, "default"


def _configuration_error(
    env_var: str,
    message: str,
    *,
    code: str = "INVALID_ENV_VAR",
) -> dict[str, Any]:
    return {
        "code": code,
        "env_var": env_var,
        "message": message,
        "retryable": False,
    }


def _int_value(value: Any, *, env_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise McpConfigurationError(f"{env_name} must be a positive integer.") from None
    if parsed <= 0:
        raise McpConfigurationError(f"{env_name} must be a positive integer.")
    return parsed


def _float_value(value: Any, *, env_name: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise McpConfigurationError(f"{env_name} must be a positive number.") from None
    if parsed <= 0:
        raise McpConfigurationError(f"{env_name} must be a positive number.")
    return parsed


def _bool_value(value: Any, *, env_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        raise McpConfigurationError(f"{env_name} must be a boolean value.")
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise McpConfigurationError(f"{env_name} must be a boolean value.")
