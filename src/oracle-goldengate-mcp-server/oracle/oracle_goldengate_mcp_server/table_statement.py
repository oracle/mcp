"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any


def normalize_table_statement(stmt: str) -> str:
    trimmed = (stmt or "").strip()
    with_prefix = trimmed if trimmed.upper().startswith("TABLE ") else f"TABLE {trimmed}"
    return with_prefix if with_prefix.endswith(";") else f"{with_prefix};"


def add_as_of_scn_to_table_statements(stmt: str, scn: int) -> str:
    """Add an Oracle flashback SQLPREDICATE to each raw TABLE statement."""
    normalized = normalize_table_statement(stmt)
    if "SQLPREDICATE" in normalized.upper():
        raise ValueError("'asOfScn' cannot be combined with a tableStatement that already contains SQLPREDICATE.")

    statements: list[str] = []
    current: list[str] = []
    in_quote = False
    index = 0
    while index < len(normalized):
        char = normalized[index]
        current.append(char)
        if char == "'":
            if in_quote and index + 1 < len(normalized) and normalized[index + 1] == "'":
                current.append(normalized[index + 1])
                index += 1
            else:
                in_quote = not in_quote
        if char == ";" and not in_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        index += 1

    remainder = "".join(current).strip()
    if remainder:
        statements.append(f"{remainder};")
    if not statements or any(not statement.upper().startswith("TABLE ") for statement in statements):
        raise ValueError("tableStatement must contain only TABLE statements when used with 'asOfScn'.")

    predicate = f"SQLPREDICATE 'AS OF SCN {scn}'"
    return "\n".join(f"{statement[:-1].rstrip()}, {predicate};" for statement in statements)


def _sq(val: str) -> str:
    return "'" + str(val).replace("'", "''") + "'"


def _join_cols(cols: list[str] | None) -> str:
    return ", ".join(cols or [])


def _append_clause(buf: str, clause: str) -> str:
    return f"{buf}, {clause}"


def _normalize_sql_predicate(predicate: str) -> str:
    """Preserve complete SQL selection clauses while supporting legacy bare conditions."""
    normalized = predicate.strip()
    clause_prefixes = ("WHERE ", "AS OF ", "ORDER BY ", "GROUP BY ", "HAVING ")
    if normalized.upper().startswith(clause_prefixes):
        return normalized
    return f"WHERE {normalized}"


def build_table_statement(params: dict[str, Any]) -> str:
    source = params.get("source")
    options = params.get("options") or {}
    if not source:
        raise ValueError("source is required")
    if not source.get("schema"):
        raise ValueError("source.schema is required")
    if not source.get("table"):
        raise ValueError("source.table is required")

    if options.get("cols") is not None and options.get("colsExcept") is not None:
        raise ValueError("Options 'cols' and 'colsExcept' are mutually exclusive")
    if options.get("def") is not None and options.get("targetDef") is not None:
        raise ValueError("Options 'def' and 'targetDef' are mutually exclusive")

    qualified = ""
    if source.get("container") and str(source["container"]).strip():
        qualified += f"{source['container']}."
    qualified += f"{source['schema']}.{source['table']}"

    partition_ids = source.get("partitionObjIds")
    if partition_ids:
        qualified += f" PARTITIONOBJID {', '.join(str(x) for x in partition_ids)}"

    out = f"TABLE {qualified}"
    if source.get("targetTable") and str(source["targetTable"]).strip():
        out = _append_clause(out, f"TARGET {source['targetTable']}")

    if options.get("attrCharset"):
        out = _append_clause(out, f"ATTRCHARSET ({options['attrCharset']})")
    if options.get("charset"):
        out = _append_clause(out, f"CHARSET {options['charset']}")
    if options.get("colCharset"):
        out = _append_clause(out, f"COLCHARSET {options['colCharset']}")
    if options.get("colMap"):
        out = _append_clause(out, f"COLMAP ({options['colMap']})")
    if options.get("cols"):
        out = _append_clause(out, f"COLS ({_join_cols(options['cols'])})")
    if options.get("colsExcept"):
        out = _append_clause(out, f"COLSEXCEPT ({_join_cols(options['colsExcept'])})")
    if options.get("def"):
        out = _append_clause(out, f"DEF {options['def']}")
    if options.get("targetDef"):
        out = _append_clause(out, f"TARGETDEF {options['targetDef']}")
    if options.get("eventActions"):
        out = _append_clause(out, f"EVENTACTIONS {options['eventActions']}")
    if options.get("exitParam") is not None:
        out = _append_clause(out, f"EXITPARAM {_sq(options['exitParam'])}")
    if options.get("fetchCols"):
        out = _append_clause(out, f"FETCHCOLS ({_join_cols(options['fetchCols'])})")
    if options.get("fetchColsExcept"):
        out = _append_clause(out, f"FETCHCOLSEXCEPT ({_join_cols(options['fetchColsExcept'])})")
    if options.get("fetchModCols"):
        out = _append_clause(out, f"FETCHMODCOLS ({_join_cols(options['fetchModCols'])})")
    if options.get("fetchModColsExcept"):
        out = _append_clause(out, f"FETCHMODCOLSEXCEPT ({_join_cols(options['fetchModColsExcept'])})")
    if options.get("fetchBeforeFilter"):
        out = _append_clause(out, "FETCHBEFOREFILTER")
    if options.get("filter"):
        out = _append_clause(out, f"FILTER ({options['filter']})")
    if options.get("getBeforeCols") is not None:
        gbc = options["getBeforeCols"]
        if gbc == "ALL":
            out = _append_clause(out, "GETBEFORECOLS (ALL)")
        else:
            out = _append_clause(out, f"GETBEFORECOLS ({_join_cols(gbc)})")
    if options.get("keyCols"):
        out = _append_clause(out, f"KEYCOLS ({_join_cols(options['keyCols'])})")
    if options.get("sqlExec"):
        out = _append_clause(out, f"SQLEXEC ({options['sqlExec']})")
    if options.get("sqlPredicate") and str(options["sqlPredicate"]).strip():
        out = _append_clause(out, f"SQLPREDICATE {_sq(_normalize_sql_predicate(options['sqlPredicate']))}")
    if options.get("tokens"):
        token_items = sorted(options["tokens"].items())
        token_expr = ", ".join([f"{k}={_sq(v)}" for k, v in token_items])
        out = _append_clause(out, f"TOKENS ({token_expr})")
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
