"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from ..config.consts import DEFAULT_RESULT_TTL_SECONDS


LOGGER = logging.getLogger(__name__)
RESULT_SCHEMA_VERSION = 2
_INDEX_THREAD_LOCK = RLock()


class ResultStoreError(ValueError):
    code = "REQUEST_RESULT_NOT_FOUND"
    retryable = False


class ResultStoreLookupError(ResultStoreError):
    """Raised when a requested stored result cannot be loaded."""


class ResultStoreWriteError(ResultStoreError):
    """Raised when result persistence fails after an operation."""

    code = "RESULT_PERSISTENCE_FAILED"


def generate_request_id() -> str:
    return f"mcp_{uuid4().hex}"


def safe_request_key(request_id: str) -> str:
    return hashlib.sha256(request_id.encode("utf-8")).hexdigest()


def store_analysis_result(
    *,
    result_store_dir: str,
    request_id: str,
    tool: str,
    feature_type: str,
    region: str,
    compartment_id: str,
    detail_options: dict[str, Any],
    raw_result: dict[str, Any],
    oci_request_id: str | None,
    model_versions: dict[str, Any],
    client_request_id: str | None = None,
    image_info: dict[str, Any] | None = None,
    ttl_seconds: int = DEFAULT_RESULT_TTL_SECONDS,
) -> dict[str, Any]:
    return store_tool_result(
        result_store_dir=result_store_dir,
        mcp_request_id=request_id,
        client_request_id=client_request_id,
        tool=tool,
        provider="oci_vision",
        raw_result=raw_result,
        oci_request_id=oci_request_id,
        oci_request_ids=[oci_request_id] if oci_request_id else [],
        region=region,
        feature_type=feature_type,
        compartment_id=compartment_id,
        detail_options=detail_options,
        model_versions=model_versions,
        image_info=image_info,
        object_storage_info=None,
        result_kind="vision_single",
        ttl_seconds=ttl_seconds,
    )


def store_tool_result(
    *,
    result_store_dir: str,
    mcp_request_id: str,
    tool: str,
    provider: str,
    raw_result: dict[str, Any],
    oci_request_id: str | None,
    oci_request_ids: list[str] | None,
    region: str | None,
    client_request_id: str | None = None,
    feature_type: str | None = None,
    compartment_id: str | None = None,
    detail_options: dict[str, Any] | None = None,
    model_versions: dict[str, Any] | None = None,
    image_info: dict[str, Any] | None = None,
    object_storage_info: dict[str, Any] | None = None,
    result_kind: str | None = None,
    operation_status: str | None = None,
    ttl_seconds: int = DEFAULT_RESULT_TTL_SECONDS,
) -> dict[str, Any]:
    base_dir = _ensure_store_dir(result_store_dir)
    # Hash request ids before using them as filenames to prevent path injection.
    request_key = safe_request_key(mcp_request_id)
    raw_path = base_dir / f"{request_key}.raw.json"
    meta_path = base_dir / f"{request_key}.meta.json"
    now = datetime.now(timezone.utc).isoformat()
    selected_result_kind = result_kind or _infer_result_kind(
        tool=tool,
        provider=provider,
        feature_type=feature_type,
    )
    metadata = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "result_kind": selected_result_kind,
        "operation_status": operation_status or _infer_operation_status(raw_result),
        "mcp_request_id": mcp_request_id,
        "request_id": mcp_request_id,
        "client_request_id": client_request_id,
        "tool": tool,
        "provider": provider,
        "feature_type": feature_type,
        "feature_types": _feature_types(feature_type, raw_result, selected_result_kind),
        "created_at": now,
        "region": region,
        "compartment_id": compartment_id,
        "detail_options": detail_options or {},
        "raw_result_path": str(raw_path),
        "metadata_path": str(meta_path),
        "oci_request_id": oci_request_id,
        "oci_request_ids": list(oci_request_ids or []),
        "model_versions": model_versions or {},
        "image": image_info,
        "object_storage": object_storage_info,
    }

    previous_files = _snapshot_result_files(raw_path, meta_path)
    try:
        _write_json(raw_path, raw_result)
        _write_json(meta_path, metadata)
        _append_tool_call_index(
            base_dir,
            _tool_call_index_entry(metadata),
            ttl_seconds=ttl_seconds,
        )
    except ResultStoreError:
        _restore_result_files(previous_files)
        raise
    return metadata


def load_analysis_result(
    *,
    result_store_dir: str,
    request_id: str,
    ttl_seconds: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        base_dir = Path(result_store_dir).expanduser().resolve()
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise ResultStoreLookupError("Stored result directory is unavailable.") from exc
    request_key = safe_request_key(request_id)
    raw_path = base_dir / f"{request_key}.raw.json"
    meta_path = base_dir / f"{request_key}.meta.json"
    if (
        raw_path.is_symlink()
        or meta_path.is_symlink()
        or not raw_path.is_file()
        or not meta_path.is_file()
    ):
        raise ResultStoreLookupError(f"No stored OCI Vision result exists for request_id {request_id}.")

    metadata = _read_json(meta_path)
    if metadata.get("request_id") != request_id or metadata.get("mcp_request_id", request_id) != request_id:
        raise ResultStoreLookupError(f"Stored OCI Vision result metadata is invalid for request_id {request_id}.")
    if _is_expired(str(metadata.get("created_at") or ""), ttl_seconds):
        _remove_expired_result(base_dir, request_id=request_id, ttl_seconds=ttl_seconds)
        raise ResultStoreLookupError(f"Stored OCI Vision result expired for request_id {request_id}.")
    raw_result = _read_json(raw_path)
    metadata = dict(metadata)
    metadata["raw_result_path"] = str(raw_path)
    metadata["metadata_path"] = str(meta_path)
    return raw_result, _metadata_with_compatibility_defaults(metadata, raw_result)


def raw_payload_reference(
    *,
    raw_result: dict[str, Any],
    raw_path: str | None,
    max_inline_response_bytes: int,
) -> dict[str, Any]:
    encoded = json.dumps(raw_result, separators=(",", ":"), sort_keys=True)
    if len(encoded.encode("utf-8")) <= max_inline_response_bytes:
        return {
            "raw_result_available": True,
            "raw_result_inline": raw_result,
            "raw_result_path": raw_path or None,
        }
    if not raw_path:
        return {
            "raw_result_available": False,
            "raw_result_inline": None,
            "raw_result_path": None,
        }
    return {
        "raw_result_available": True,
        "raw_result_inline": None,
        "raw_result_path": raw_path,
    }


def _ensure_store_dir(result_store_dir: str) -> Path:
    try:
        base_dir = Path(result_store_dir).expanduser().resolve()
        base_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise ResultStoreWriteError("Stored result directory could not be created.") from exc
    try:
        base_dir.chmod(0o700)
    except OSError:
        pass
    return base_dir


def _snapshot_result_files(*paths: Path) -> dict[Path, bytes | None]:
    snapshots: dict[Path, bytes | None] = {}
    try:
        for path in paths:
            if path.is_symlink():
                raise ResultStoreWriteError(
                    "Stored result paths must not be symbolic links."
                )
            snapshots[path] = path.read_bytes() if path.exists() else None
    except ResultStoreWriteError:
        raise
    except OSError as exc:
        raise ResultStoreWriteError("Existing stored result could not be read safely.") from exc
    return snapshots


def _restore_result_files(snapshots: dict[Path, bytes | None]) -> None:
    """Best-effort rollback for raw/metadata files when a store transaction fails."""
    for path, previous in snapshots.items():
        try:
            if previous is None:
                path.unlink(missing_ok=True)
                continue
            temp_path = path.with_name(f".{path.name}.{uuid4().hex}.rollback.tmp")
            temp_path.write_bytes(previous)
            temp_path.chmod(0o600)
            temp_path.replace(path)
        except OSError as exc:
            LOGGER.error("Could not roll back failed stored-result artifact %s: %s", path.name, exc)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    temp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temp_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        try:
            temp_path.chmod(0o600)
        except OSError:
            pass
        temp_path.replace(path)
    except (OSError, TypeError, ValueError) as exc:
        try:
            temp_path.unlink()
        except OSError:
            pass
        raise ResultStoreWriteError("Stored OCI Vision result could not be written.") from exc
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _append_tool_call_index(
    base_dir: Path,
    entry: dict[str, Any],
    *,
    ttl_seconds: int,
) -> None:
    index_path = base_dir / "tool_calls.json"
    with _index_lock(base_dir):
        existing = _load_or_rebuild_index(base_dir, index_path)
        request_id = entry.get("mcp_request_id") or entry.get("request_id")
        existing = [
            item
            for item in existing
            if not isinstance(item, dict)
            or (item.get("mcp_request_id") or item.get("request_id")) != request_id
        ]
        existing = _prune_expired_entries(base_dir, existing, ttl_seconds=ttl_seconds)
        existing.append(entry)
        _write_json_list(index_path, existing)


def _write_json_list(path: Path, data: list[Any]) -> None:
    temp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temp_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        try:
            temp_path.chmod(0o600)
        except OSError:
            pass
        temp_path.replace(path)
    except (OSError, TypeError, ValueError) as exc:
        try:
            temp_path.unlink()
        except OSError:
            pass
        raise ResultStoreWriteError("Stored tool-call index could not be written.") from exc
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _tool_call_index_entry(metadata: dict[str, Any]) -> dict[str, Any]:
    image = metadata.get("image") if isinstance(metadata.get("image"), dict) else {}
    object_storage = metadata.get("object_storage") if isinstance(metadata.get("object_storage"), dict) else {}
    return {
        "created_at": metadata.get("created_at"),
        "mcp_request_id": metadata.get("mcp_request_id"),
        "request_id": metadata.get("request_id"),
        "client_request_id": metadata.get("client_request_id"),
        "oci_request_id": metadata.get("oci_request_id"),
        "oci_request_ids": metadata.get("oci_request_ids") or [],
        "tool": metadata.get("tool"),
        "provider": metadata.get("provider"),
        "image_path": image.get("path"),
        "image_object_name": image.get("object_name") or object_storage.get("object_name"),
        "raw_result_path": metadata.get("raw_result_path"),
        "metadata_path": metadata.get("metadata_path"),
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResultStoreLookupError("Stored OCI Vision result is unavailable or invalid.") from exc
    if not isinstance(data, dict):
        raise ResultStoreLookupError("Stored OCI Vision result is invalid.")
    return data


def _is_expired(created_at: str, ttl_seconds: int) -> bool:
    try:
        created = datetime.fromisoformat(created_at)
    except ValueError:
        return True
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - created
    return age.total_seconds() > ttl_seconds


@contextmanager
def _index_lock(base_dir: Path):
    """Serialize index updates across threads and POSIX processes."""

    lock_path = base_dir / ".tool_calls.lock"
    with _INDEX_THREAD_LOCK:
        try:
            with lock_path.open("a+", encoding="utf-8") as lock_file:
                try:
                    lock_path.chmod(0o600)
                except OSError:
                    pass
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        except ResultStoreError:
            raise
        except OSError as exc:
            raise ResultStoreWriteError("Stored tool-call index could not be locked.") from exc


def _load_or_rebuild_index(base_dir: Path, index_path: Path) -> list[dict[str, Any]]:
    if not index_path.is_file():
        return _rebuild_tool_call_index(base_dir)
    try:
        loaded = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        LOGGER.warning("Stored tool-call index is invalid; rebuilding it from result metadata.")
        return _rebuild_tool_call_index(base_dir)
    if not isinstance(loaded, list) or any(not isinstance(item, dict) for item in loaded):
        LOGGER.warning("Stored tool-call index has an invalid shape; rebuilding it from result metadata.")
        return _rebuild_tool_call_index(base_dir)
    return loaded


def _rebuild_tool_call_index(base_dir: Path) -> list[dict[str, Any]]:
    rebuilt: list[dict[str, Any]] = []
    for meta_path in base_dir.glob("*.meta.json"):
        if meta_path.is_symlink():
            continue
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(metadata, dict):
            continue
        request_id = metadata.get("mcp_request_id") or metadata.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            continue
        raw_path, expected_meta_path = _canonical_result_paths(base_dir, request_id)
        if (
            meta_path != expected_meta_path
            or raw_path.is_symlink()
            or not raw_path.is_file()
        ):
            continue
        recovered = dict(metadata)
        recovered["raw_result_path"] = str(raw_path)
        recovered["metadata_path"] = str(expected_meta_path)
        rebuilt.append(_tool_call_index_entry(recovered))
    rebuilt.sort(key=lambda item: str(item.get("created_at") or ""))
    return rebuilt


def _prune_expired_entries(
    base_dir: Path,
    entries: list[dict[str, Any]],
    *,
    ttl_seconds: int,
) -> list[dict[str, Any]]:
    retained: list[dict[str, Any]] = []
    for entry in entries:
        if not _is_expired(str(entry.get("created_at") or ""), ttl_seconds):
            retained.append(entry)
            continue
        request_id = entry.get("mcp_request_id") or entry.get("request_id")
        if isinstance(request_id, str) and request_id:
            _delete_result_files(base_dir, request_id)
    return retained


def _remove_expired_result(base_dir: Path, *, request_id: str, ttl_seconds: int) -> None:
    try:
        with _index_lock(base_dir):
            _delete_result_files(base_dir, request_id)
            index_path = base_dir / "tool_calls.json"
            entries = _load_or_rebuild_index(base_dir, index_path)
            entries = _prune_expired_entries(base_dir, entries, ttl_seconds=ttl_seconds)
            entries = [
                entry
                for entry in entries
                if (entry.get("mcp_request_id") or entry.get("request_id")) != request_id
            ]
            _write_json_list(index_path, entries)
    except ResultStoreError as exc:
        # Expiration remains authoritative even if best-effort cleanup fails.
        LOGGER.warning("Expired stored result cleanup failed: %s", exc)


def _delete_result_files(base_dir: Path, request_id: str) -> None:
    for path in _canonical_result_paths(base_dir, request_id):
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            LOGGER.warning("Could not delete expired stored-result artifact %s: %s", path.name, exc)


def _canonical_result_paths(base_dir: Path, request_id: str) -> tuple[Path, Path]:
    request_key = safe_request_key(request_id)
    return (
        base_dir / f"{request_key}.raw.json",
        base_dir / f"{request_key}.meta.json",
    )


def _infer_result_kind(*, tool: str, provider: str, feature_type: str | None) -> str:
    if provider == "oci_object_storage":
        return "object_storage"
    if tool == "parallel_analyze_image" or feature_type == "parallel_analyze_image":
        return "vision_parallel"
    if tool in {"create_image_job", "get_image_job", "cancel_image_job"} or feature_type == "image_job":
        return "vision_image_job"
    if feature_type and "," in feature_type:
        return "vision_combined"
    return "vision_single"


def _infer_operation_status(raw_result: dict[str, Any]) -> str:
    succeeded = raw_result.get("succeeded_count")
    failed = raw_result.get("failed_count")
    if isinstance(succeeded, int) and isinstance(failed, int):
        if succeeded > 0 and failed > 0:
            return "partial_failure"
        if failed > 0 and succeeded == 0:
            return "failed"
    if raw_result.get("errors"):
        return "failed"
    return "succeeded"


def _feature_types(
    feature_type: str | None,
    raw_result: dict[str, Any],
    result_kind: str,
) -> list[str]:
    if result_kind == "vision_parallel":
        values: list[str] = []
        for item in raw_result.get("items") or []:
            if not isinstance(item, dict):
                continue
            for value in item.get("feature_types") or []:
                if isinstance(value, str) and value not in values:
                    values.append(value)
        return values
    return [value for value in (feature_type or "").split(",") if value]


def _metadata_with_compatibility_defaults(
    metadata: dict[str, Any],
    raw_result: dict[str, Any],
) -> dict[str, Any]:
    """Add in-memory defaults for metadata written before schema version 2."""

    compatible = dict(metadata)
    result_kind = compatible.get("result_kind")
    if not isinstance(result_kind, str) or not result_kind:
        result_kind = _infer_result_kind(
            tool=str(compatible.get("tool") or ""),
            provider=str(compatible.get("provider") or "oci_vision"),
            feature_type=compatible.get("feature_type"),
        )
        compatible["result_kind"] = result_kind
    compatible.setdefault("schema_version", 1)
    compatible.setdefault("operation_status", _infer_operation_status(raw_result))
    compatible.setdefault(
        "feature_types",
        _feature_types(compatible.get("feature_type"), raw_result, result_kind),
    )
    compatible.setdefault("detail_options", {})
    return compatible
