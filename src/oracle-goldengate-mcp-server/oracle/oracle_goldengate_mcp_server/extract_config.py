"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any


def _normalize_boolean(value: str | int | bool) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return str(value)


def _build_integrated_params_clause(spec: Any) -> str | None:
    if not spec:
        return None
    if isinstance(spec, str):
        inner = spec.strip()
        return f"INTEGRATEDPARAMS ({inner})" if inner else None
    if isinstance(spec, list):
        cleaned = [s.strip() for s in spec if str(s).strip()]
        return f"INTEGRATEDPARAMS ({', '.join(cleaned)})" if cleaned else None

    entries: list[str] = []
    if spec.get("entries"):
        entries.extend([e.strip() for e in spec["entries"] if str(e).strip()])
    key_values = spec.get("keyValues") or spec.get("key_values")
    if key_values:
        for key, value in key_values.items():
            entries.append(f"{key} {_normalize_boolean(value)}")
    return f"INTEGRATEDPARAMS ({', '.join(entries)})" if entries else None


def _build_tranlog_options_clause(spec: Any) -> str | None:
    if not spec:
        return None
    if isinstance(spec, str):
        trimmed = spec.strip()
        return f"TRANLOGOPTIONS {trimmed}" if trimmed else None

    parts: list[str] = []
    if isinstance(spec, list):
        joined = " ".join([s.strip() for s in spec if str(s).strip()])
        if joined:
            parts.append(joined)
    else:
        clauses = spec.get("clauses")
        if clauses:
            clause = " ".join([s.strip() for s in clauses if str(s).strip()])
            if clause:
                parts.append(clause)
        integrated = _build_integrated_params_clause(spec.get("integratedParams") or spec.get("integrated_params"))
        if integrated:
            parts.append(integrated)
        additional = spec.get("additional")
        if additional:
            add = " ".join([s.strip() for s in additional if str(s).strip()])
            if add:
                parts.append(add)

    statement = " ".join([p for p in parts if p])
    return f"TRANLOGOPTIONS {statement}" if statement else None


def _build_report_count_clause(spec: dict[str, Any] | None) -> str | None:
    if not spec:
        return None
    tokens: list[str] = []
    every = spec.get("every")
    if every:
        if isinstance(every, str):
            trimmed = every.strip()
            if trimmed:
                tokens.append(f"EVERY {trimmed}")
        else:
            tokens.append(f"EVERY {every['value']} {every['unit']}")
    if spec.get("records") is not None:
        tokens.append(f"{spec['records']} RECORDS")
    if spec.get("rate"):
        tokens.append("RATE")
    if spec.get("additional"):
        tokens.extend([s.strip() for s in spec["additional"] if str(s).strip()])
    if not tokens:
        return None
    first, *rest = tokens
    clause = f"REPORTCOUNT {first}"
    if rest:
        clause += "".join([f", {token}" for token in rest])
    return clause


def _build_bounded_recovery_clause(spec: dict[str, Any] | None) -> str | None:
    if not spec:
        return None
    tokens: list[str] = []
    if spec.get("interval"):
        tokens.append(f"BRINTERVAL {spec['interval']}")
    if spec.get("dir"):
        tokens.append(f"BRDIR {spec['dir']}")
    if spec.get("additional"):
        tokens.extend([s.strip() for s in spec["additional"] if str(s).strip()])
    return f"BR {', '.join(tokens)}" if tokens else None


def _build_db_options_clause(spec: Any) -> str | None:
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


def build_advanced_extract_parameters(spec: dict[str, Any] | None) -> list[str]:
    if not spec:
        return []
    lines: list[str] = []
    if spec.get("disableHeartbeatTable") is True or spec.get("disable_heartbeat_table") is True:
        lines.append("DISABLE_HEARTBEAT_TABLE")
    tranlog = _build_tranlog_options_clause(spec.get("tranlogOptions") or spec.get("tranlog_options"))
    if tranlog:
        lines.append(tranlog)
    report_count = _build_report_count_clause(spec.get("reportCount") or spec.get("report_count"))
    if report_count:
        lines.append(report_count)
    bounded_recovery = _build_bounded_recovery_clause(spec.get("boundedRecovery") or spec.get("bounded_recovery"))
    if bounded_recovery:
        lines.append(bounded_recovery)
    db_options = _build_db_options_clause(spec.get("dbOptions") or spec.get("db_options"))
    if db_options:
        lines.append(db_options)
    source_catalog = spec.get("sourceCatalog") or spec.get("source_catalog")
    if source_catalog and str(source_catalog).strip():
        lines.append(f"SOURCECATALOG {str(source_catalog).strip()}")
    ddl = spec.get("ddl")
    if ddl:
        values = [ddl] if isinstance(ddl, str) else ddl
        for value in values:
            trimmed = str(value).strip()
            if trimmed:
                lines.append(f"DDL {trimmed}")
    additional = spec.get("additionalParameters") or spec.get("additional_parameters")
    if additional:
        lines.extend([s.strip() for s in additional if str(s).strip()])
    return lines
