"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import ast
import builtins
from typing import Any, Final

MAX_CODE_BYTES: Final[int] = 64_000

SAFE_IMPORT_ROOTS: Final[set[str]] = {
    "base64",
    "collections",
    "dataclasses",
    "datetime",
    "decimal",
    "enum",
    "fractions",
    "functools",
    "itertools",
    "json",
    "math",
    "oci",
    "re",
    "statistics",
    "time",
    "typing",
    "uuid",
}

BANNED_CALLS: Final[set[str]] = {
    "__import__",
    "breakpoint",
    "compile",
    "delattr",
    "eval",
    "exec",
    "getattr",
    "globals",
    "help",
    "input",
    "locals",
    "open",
    "setattr",
    "vars",
}

BANNED_NAME_REFERENCES: Final[set[str]] = {
    "__import__",
    "builtins",
    "compile",
    "ctypes",
    "delattr",
    "eval",
    "exec",
    "getattr",
    "globals",
    "help",
    "importlib",
    "input",
    "locals",
    "open",
    "os",
    "pathlib",
    "resource",
    "setattr",
    "shutil",
    "socket",
    "subprocess",
    "sys",
    "vars",
}

BANNED_ATTR_NAMES: Final[set[str]] = {
    "__bases__",
    "__class__",
    "__code__",
    "__dict__",
    "__globals__",
    "__mro__",
    "__subclasses__",
}


class CodePolicyError(ValueError):
    """Raised when a snippet violates the defense-in-depth policy."""


class CodePolicyVisitor(ast.NodeVisitor):
    """Apply a narrow AST policy before code reaches the sandbox."""

    def __init__(self) -> None:
        self.violations: list[str] = []

    def _add_violation(self, node: ast.AST, message: str) -> None:
        line = getattr(node, "lineno", "?")
        self.violations.append(f"line {line}: {message}")

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            module_root = alias.name.split(".", 1)[0]
            if module_root not in SAFE_IMPORT_ROOTS:
                self._add_violation(node, f"Import '{alias.name}' is not allowed")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        if node.level:
            self._add_violation(node, "Relative imports are not allowed")
        module_root = (node.module or "").split(".", 1)[0]
        if module_root not in SAFE_IMPORT_ROOTS:
            self._add_violation(node, f"Import '{node.module}' is not allowed")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        if isinstance(node.func, ast.Name) and node.func.id in BANNED_CALLS:
            self._add_violation(node, f"Call to '{node.func.id}' is not allowed")
        if isinstance(node.func, ast.Attribute) and node.func.attr in BANNED_ATTR_NAMES:
            self._add_violation(node, f"Reflective access to '{node.func.attr}' is not allowed")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        if node.attr.startswith("__") or node.attr in BANNED_ATTR_NAMES:
            self._add_violation(node, f"Attribute '{node.attr}' is not allowed")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> Any:
        if isinstance(node.ctx, ast.Load) and node.id in BANNED_NAME_REFERENCES:
            self._add_violation(node, f"Name '{node.id}' is not allowed")
        self.generic_visit(node)


def _has_supported_entrypoint(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "main":
            return True
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "result":
                    return True
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "result":
                return True
    return False


def validate_user_code(code: str) -> ast.Module:
    if not isinstance(code, str):
        raise CodePolicyError("code must be a string")
    if not code.strip():
        raise CodePolicyError("code must not be empty")
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        raise CodePolicyError(f"code exceeds the maximum size of {MAX_CODE_BYTES} bytes")

    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        raise CodePolicyError(f"Invalid Python syntax: {exc.msg} (line {exc.lineno})") from exc

    visitor = CodePolicyVisitor()
    visitor.visit(tree)
    if visitor.violations:
        raise CodePolicyError("; ".join(visitor.violations))

    if not _has_supported_entrypoint(tree):
        raise CodePolicyError("code must define main(input_data) or assign a top-level result")

    return tree


def make_restricted_builtins() -> dict[str, Any]:
    removed = (BANNED_CALLS - {"__import__"}) | {"exit", "license", "quit"}
    return {
        name: value
        for name, value in builtins.__dict__.items()
        if name not in removed
    }
