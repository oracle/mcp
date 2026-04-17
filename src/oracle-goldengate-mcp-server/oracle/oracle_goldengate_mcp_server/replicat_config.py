"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any


def _build_db_options(spec: Any) -> str | None:
    if not spec:
        return None
    if isinstance(spec, str):
        trimmed = spec.strip()
        return f"DBOPTIONS {trimmed}" if trimmed else None
    if isinstance(spec, list):
        cleaned = [s.strip() for s in spec if str(s).strip()]
        return f"DBOPTIONS {', '.join(cleaned)}" if cleaned else None
    parts: list[str] = []
    if spec.get("entries"):
        parts.extend([s.strip() for s in spec["entries"] if str(s).strip()])
    if spec.get("additional"):
        parts.extend([s.strip() for s in spec["additional"] if str(s).strip()])
    return f"DBOPTIONS {', '.join(parts)}" if parts else None


def _build_batch_sql(spec: Any) -> list[str]:
    if not spec:
        return []
    values = spec if isinstance(spec, list) else [spec]
    out: list[str] = []
    for value in values:
        trimmed = str(value).strip()
        if trimmed:
            out.append(f"BATCHSQL {trimmed}")
    return out


def build_advanced_replicat_parameters(spec: dict[str, Any] | None) -> dict[str, Any]:
    if not spec:
        return {"lines": [], "mode": {"type": "nonintegrated", "parallel": True}}

    if spec.get("applyParallelism") is not None and (
        spec.get("minApplyParallelism") is not None or spec.get("maxApplyParallelism") is not None
    ):
        raise ValueError("Options 'applyParallelism' and 'minApplyParallelism/maxApplyParallelism' are mutually exclusive")

    if spec.get("modeType") == "parallel" and spec.get("mapParallelism") is not None:
        raise ValueError("'mapParallelism' is not supported when modeType is 'parallel'")

    lines: list[str] = []
    credential_lines: list[str] = []

    credential = spec.get("credential")
    if credential:
        values = credential if isinstance(credential, list) else [credential]
        for value in values:
            trimmed = str(value).strip()
            if trimmed:
                credential_lines.append(trimmed)

    if spec.get("applyParallelism") is not None:
        lines.append(f"APPLY_PARALLELISM {spec['applyParallelism']}")

    db_options = _build_db_options(spec.get("dbOptions"))
    if db_options:
        lines.append(db_options)

    lines.extend(_build_batch_sql(spec.get("batchSql")))

    for key, prefix in [
        ("ddlError", "DDLERROR"),
        ("repError", "REPERROR"),
        ("ddlOptions", "DDLOPTIONS"),
        ("sourceCatalog", "SOURCECATALOG"),
        ("obey", "OBEY"),
    ]:
        value = spec.get(key)
        if value and str(value).strip():
            lines.append(f"{prefix} {str(value).strip()}")

    numeric_map = {
        "mapParallelism": "MAP_PARALLELISM",
        "minApplyParallelism": "MIN_APPLY_PARALLELISM",
        "maxApplyParallelism": "MAX_APPLY_PARALLELISM",
        "splitTransRecs": "SPLIT_TRANS_RECS",
        "lookAheadTransactions": "LOOK_AHEAD_TRANSACTIONS",
        "chunkSize": "CHUNK_SIZE",
    }
    for key, prefix in numeric_map.items():
        if spec.get(key) is not None:
            lines.append(f"{prefix} {spec[key]}")

    additional = spec.get("additionalParameters")
    if additional:
        lines.extend([s.strip() for s in additional if str(s).strip()])

    checkpoint_table = spec.get("checkpointTable")
    if checkpoint_table and str(checkpoint_table).strip():
        lines.append(f"CHECKPOINTTABLE {str(checkpoint_table).strip()}")

    mode = None
    if spec.get("modeType"):
        mode = {"type": spec["modeType"]}
        if spec.get("modeParallel") is not None:
            mode["parallel"] = spec["modeParallel"]

    return {
        "lines": lines,
        "credentialLines": credential_lines if credential_lines else None,
        "mode": mode or {"type": "nonintegrated", "parallel": True},
        "checkpointTable": str(checkpoint_table).strip() if checkpoint_table else None,
    }
