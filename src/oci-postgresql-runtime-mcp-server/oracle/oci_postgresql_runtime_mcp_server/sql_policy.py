"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from dataclasses import dataclass
from typing import Any, Optional

from pglast import ast, parse_sql, parser

_BLOCKED_FUNCTION_NAMES = {"pg_sleep", "pg_sleep_for", "pg_sleep_until", "sleep"}


@dataclass(frozen=True)
class _PreparedStatement:
    sql: str
    params: Optional[list[Any]]
    kind: str
    server_cursor_compatible: bool = False


def _ast_classes(*names: str) -> tuple[type[Any], ...]:
    return tuple(
        ast_class
        for name in names
        if isinstance((ast_class := getattr(ast, name, None)), type)
    )


_READ_AST_TYPES = _ast_classes("SelectStmt", "VariableShowStmt")
_DML_AST_TYPES = _ast_classes("InsertStmt", "UpdateStmt")
_BLOCKED_AST_TYPES = _ast_classes(
    "AlterOwnerStmt",
    "AlterSystemStmt",
    "CallStmt",
    "ClusterStmt",
    "CopyStmt",
    "DeallocateStmt",
    "DeleteStmt",
    "DiscardStmt",
    "DoStmt",
    "DropStmt",
    "ExecuteStmt",
    "GrantStmt",
    "ListenStmt",
    "LoadStmt",
    "MergeStmt",
    "NotifyStmt",
    "PrepareStmt",
    "ReassignOwnedStmt",
    "RefreshMatViewStmt",
    "ReindexStmt",
    "TransactionStmt",
    "TruncateStmt",
    "UnlistenStmt",
    "VacuumStmt",
    "VariableSetStmt",
)


def _split_sql_statements(sql: str) -> list[str]:
    return list(parser.split(sql, with_parser=False))


def _replace_psycopg_placeholders(sql: str) -> str:
    pieces: list[str] = []
    cursor = 0
    param_index = 1

    while (index := sql.find("%", cursor)) != -1:
        pieces.append(sql[cursor:index])
        if index + 1 == len(sql) or sql[index + 1] == "\n":
            pieces.append("%")
            cursor = index + 1
            continue

        placeholder_type = sql[index + 1]
        if placeholder_type == "%":
            pieces.append("%")
        elif placeholder_type in {"s", "b", "t"}:
            pieces.append(f"${param_index}")
            param_index += 1
        elif placeholder_type == "(":
            raise ValueError(
                "Named query placeholders are not supported; use positional "
                "%s, %b, or %t placeholders"
            )
        else:
            raise ValueError(
                "Only %s, %b, %t, and %% are valid query placeholder sequences"
            )
        cursor = index + 2

    pieces.append(sql[cursor:])
    return "".join(pieces)


def _parse_statement(sql: str, params: Optional[list[Any]]) -> Any:
    try:
        validation_sql = _replace_psycopg_placeholders(sql) if params is not None else sql
        parsed = parse_sql(validation_sql)
    except parser.ParseError as exc:
        raise ValueError(f"SQL could not be parsed: {exc}") from exc
    if len(parsed) != 1:
        raise ValueError("SQL statement parsing did not produce exactly one statement")
    return parsed[0].stmt


def _iter_ast_nodes(node: Any):
    if isinstance(node, ast.Node):
        yield node
        for member in node:
            try:
                value = getattr(node, member)
            except AttributeError:
                continue
            yield from _iter_ast_nodes(value)
    elif isinstance(node, tuple):
        for item in node:
            yield from _iter_ast_nodes(item)


def _iter_descendant_nodes(node: ast.Node):
    iterator = _iter_ast_nodes(node)
    next(iterator, None)
    yield from iterator


def _has_blocked_descendants(node: ast.Node) -> bool:
    return any(
        isinstance(descendant, _BLOCKED_AST_TYPES) for descendant in _iter_ast_nodes(node)
    )


def _has_mutating_cte(node: ast.Node) -> bool:
    for descendant in _iter_descendant_nodes(node):
        if isinstance(descendant, _DML_AST_TYPES):
            return True
    return False


def _func_call_name(node: ast.FuncCall) -> str:
    return ".".join(
        str(part.sval).lower()
        for part in (node.funcname or ())
        if getattr(part, "sval", None)
    )


def _has_blocked_function_call(node: ast.Node) -> bool:
    for descendant in _iter_ast_nodes(node):
        if isinstance(descendant, ast.FuncCall):
            function_name = _func_call_name(descendant)
            if function_name.split(".")[-1] in _BLOCKED_FUNCTION_NAMES:
                return True
    return False


def _has_locking_select(node: ast.Node) -> bool:
    return any(
        isinstance(descendant, ast.SelectStmt) and descendant.lockingClause
        for descendant in _iter_ast_nodes(node)
    )


def _is_explain_analyze(node: ast.ExplainStmt) -> bool:
    return any(
        getattr(option, "defname", "").lower() == "analyze"
        for option in (node.options or ())
    )


def _is_safe_read_statement(node: ast.Node) -> bool:
    if isinstance(node, ast.ExplainStmt):
        return not _is_explain_analyze(node) and _is_safe_read_statement(node.query)
    if not isinstance(node, _READ_AST_TYPES):
        return False
    if isinstance(node, ast.SelectStmt):
        if node.intoClause or _has_locking_select(node):
            return False
    return not _has_mutating_cte(node)


def _validate_statement(
    sql: str,
    params: Optional[list[Any]],
) -> _PreparedStatement:
    node = _parse_statement(sql, params)
    node_name = node.__class__.__name__

    if isinstance(node, _BLOCKED_AST_TYPES) or _has_blocked_descendants(node):
        raise ValueError(f"{node_name} statements are blocked")
    if _has_blocked_function_call(node):
        raise ValueError(f"{node_name} statements call blocked sleep functions")
    if _is_safe_read_statement(node):
        return _PreparedStatement(
            sql=sql,
            params=params,
            kind="read",
            server_cursor_compatible=isinstance(node, ast.SelectStmt),
        )
    raise ValueError(f"{node_name} statements are not allowed; only read-only SQL is supported")


def _normalize_statement_params(
    statements: list[str],
    params: Optional[list[Any]],
) -> list[Optional[list[Any]]]:
    if len(statements) == 1:
        return [params]

    if params is None:
        return [None for _ in statements]

    if len(params) != len(statements):
        raise ValueError(
            "For multi-statement SQL, params must contain one bind list per statement"
        )

    normalized_params: list[Optional[list[Any]]] = []
    for index, statement_params in enumerate(params, start=1):
        if statement_params is None:
            normalized_params.append(None)
            continue
        if not isinstance(statement_params, list):
            raise ValueError(
                "For multi-statement SQL, each params item must be a list. "
                f"Statement {index} has {type(statement_params).__name__}."
            )
        normalized_params.append(statement_params)
    return normalized_params


def _prepare_sql_execution(
    sql: str,
    params: Optional[list[Any]],
) -> list[_PreparedStatement]:
    statements = _split_sql_statements(sql)
    if not statements:
        raise ValueError("SQL must include at least one executable statement")

    statement_params = _normalize_statement_params(statements, params)
    return [
        _validate_statement(statement, params_for_statement)
        for statement, params_for_statement in zip(statements, statement_params)
    ]


def _param_count(prepared_statements: list[_PreparedStatement]) -> int:
    return sum(len(statement.params or []) for statement in prepared_statements)
