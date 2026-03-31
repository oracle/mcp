"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any


def normalize_map_statement(stmt: str) -> str:
    trimmed = (stmt or "").strip()
    with_prefix = trimmed if trimmed.upper().startswith("MAP ") else f"MAP {trimmed}"
    return with_prefix if with_prefix.endswith(";") else f"{with_prefix};"


def _sq(val: str) -> str:
    return "'" + str(val).replace("'", "''") + "'"


def _join_cols(cols: list[str] | None) -> str:
    return ", ".join(cols or [])


def _append_clause(buf: str, clause: str) -> str:
    return f"{buf}, {clause}"


def build_map_statement(params: dict[str, Any]) -> str:
    source = params.get("source")
    options = params.get("options") or {}
    if not source:
        raise ValueError("source is required")
    if not source.get("schema"):
        raise ValueError("source.schema is required")
    if not source.get("table"):
        raise ValueError("source.table is required")
    if not source.get("targetTable"):
        raise ValueError("source.targetTable is required")
    if options.get("def") is not None and options.get("targetDef") is not None:
        raise ValueError("Options 'def' and 'targetDef' are mutually exclusive")

    qualified = ""
    if source.get("container") and str(source["container"]).strip():
        qualified += f"{source['container']}."
    qualified += f"{source['schema']}.{source['table']}"
    partition_ids = source.get("partitionObjIds")
    if partition_ids:
        qualified += f" PARTITIONOBJID {', '.join(str(x) for x in partition_ids)}"

    out = f"MAP {qualified}"
    out = _append_clause(out, f"TARGET {source['targetTable']}")

    if options.get("modCompareCols"):
        out = _append_clause(out, f"MOD_COMPARE_COLS({options['modCompareCols']})")
    if options.get("colMap"):
        out = _append_clause(out, f"COLMAP ({options['colMap']})")
    if options.get("compareCols"):
        out = _append_clause(out, f"COMPARECOLS ({options['compareCols']})")
    if options.get("coordinated"):
        out = _append_clause(out, "COORDINATED")
    if options.get("def"):
        out = _append_clause(out, f"DEF {options['def']}")
    if options.get("targetDef"):
        out = _append_clause(out, f"TARGETDEF {options['targetDef']}")
    if options.get("exceptionsOnly"):
        out = _append_clause(out, "EXCEPTIONSONLY")
    if options.get("exitParam") is not None:
        out = _append_clause(out, f"EXITPARAM {_sq(options['exitParam'])}")
    if options.get("eventActions"):
        out = _append_clause(out, f"EVENTACTIONS ({options['eventActions']})")
    if options.get("filter"):
        out = _append_clause(out, f"FILTER ({options['filter']})")
    if options.get("handleCollisions") is True:
        out = _append_clause(out, "HANDLECOLLISIONS")
    if options.get("handleCollisions") is False:
        out = _append_clause(out, "NOHANDLECOLLISIONS")
    if options.get("insertAllRecords"):
        out = _append_clause(out, "INSERTALLRECORDS")
    if options.get("insertAppend") is True:
        out = _append_clause(out, "INSERTAPPEND")
    if options.get("insertAppend") is False:
        out = _append_clause(out, "NOINSERTAPPEND")
    if options.get("keyCols"):
        out = _append_clause(out, f"KEYCOLS ({_join_cols(options['keyCols'])})")
    if options.get("mapAllColumns") is True:
        out = _append_clause(out, "MAPALLCOLUMNS")
    if options.get("mapAllColumns") is False:
        out = _append_clause(out, "NOMAPALLCOLUMNS")
    if options.get("mapException"):
        out = _append_clause(out, f"MAPEXCEPTION ({options['mapException']})")
    if options.get("mapInvisibleColumns") is True:
        out = _append_clause(out, "MAPINVISIBLECOLUMNS")
    if options.get("mapInvisibleColumns") is False:
        out = _append_clause(out, "NOMAPINVISIBLECOLUMNS")
    if options.get("repError"):
        out = _append_clause(out, f"REPERROR ({options['repError']})")
    if options.get("resolveConflict"):
        out = _append_clause(out, f"RESOLVECONFLICT ({options['resolveConflict']})")
    if options.get("sqlExec"):
        out = _append_clause(out, f"SQLEXEC ({options['sqlExec']})")
    if options.get("thread") is not None and str(options["thread"]).strip():
        out = _append_clause(out, f"THREAD ({options['thread']})")
    if options.get("threadRange"):
        out = _append_clause(out, f"THREADRANGE ({options['threadRange']})")
    if options.get("trimSpaces") is True:
        out = _append_clause(out, "TRIMSPACES")
    if options.get("trimSpaces") is False:
        out = _append_clause(out, "NOTRIMSPACES")
    if options.get("trimVarSpaces") is True:
        out = _append_clause(out, "TRIMVARSPACES")
    if options.get("trimVarSpaces") is False:
        out = _append_clause(out, "NOTRIMVARSPACES")
    if options.get("where"):
        out = _append_clause(out, f"WHERE ({options['where']})")

    return out if out.endswith(";") else f"{out};"
