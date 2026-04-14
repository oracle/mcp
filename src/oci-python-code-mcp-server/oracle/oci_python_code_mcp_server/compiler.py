"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import ast
import inspect
from copy import deepcopy
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Optional

MAX_PROCEDURE_STEPS = 3
DESTRUCTIVE_OPERATION_PREFIXES = (
    "delete_",
    "terminate_",
    "detach_",
    "remove_",
    "purge_",
    "cancel_",
)
SAFE_SETUP_CALL_PREFIXES = (
    "oci.config.",
    "oci.auth.",
    "oci.signer.",
)


class OciSdkCompileError(ValueError):
    """Raised when user-provided OCI SDK code cannot be compiled safely."""


@dataclass(frozen=True)
class ResultReference:
    label: str
    path: tuple[tuple[str, Any], ...] = ()


@dataclass(frozen=True)
class _IgnoredSetupValue:
    source: str


class _CompileEnv:
    def __init__(self) -> None:
        self.module_aliases: dict[str, str] = {"oci": "oci"}
        self.symbol_aliases: dict[str, str] = {}
        self.client_bindings: dict[str, str] = {}
        self.value_bindings: dict[str, Any] = {}
        self.runtime_labels: set[str] = set()
        self.steps: list[dict[str, Any]] = []
        self.program: list[dict[str, Any]] = []
        self.translation_warnings: list[str] = []

    def compile_module(self, source: str, *, allow_reference_final: bool = False) -> list[dict[str, Any]]:
        body = self._parse_body(source)
        for index, stmt in enumerate(body):
            is_final = index == len(body) - 1
            self._compile_statement(stmt, is_final=is_final, allow_reference_final=allow_reference_final)
        return deepcopy(self.steps)

    def compile_program(self, source: str, *, best_effort: bool = False) -> dict[str, Any]:
        body = self._parse_body(source)
        for index, stmt in enumerate(body):
            is_final = index == len(body) - 1
            try:
                self._compile_program_statement(stmt, is_final=is_final)
            except OciSdkCompileError as exc:
                if not best_effort or not self._should_ignore_program_statement(stmt):
                    raise
                self.translation_warnings.append(
                    f"Ignored Python the server could not translate: {ast.unparse(stmt)} ({exc})"
                )

        if not self.steps:
            raise OciSdkCompileError("OCI SDK code must include at least one OCI SDK call")

        return {
            "steps": deepcopy(self.steps),
            "program": deepcopy(self.program),
            "static_bindings": {
                name: deepcopy(value)
                for name, value in self.value_bindings.items()
                if not isinstance(value, _IgnoredSetupValue)
            },
            "setup_bindings": {
                name: value.source
                for name, value in self.value_bindings.items()
                if isinstance(value, _IgnoredSetupValue)
            },
            "translation_warnings": list(self.translation_warnings),
        }

    def _should_ignore_program_statement(self, stmt: ast.stmt) -> bool:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            return False
        if isinstance(stmt, ast.Assign):
            return True
        if isinstance(stmt, ast.Expr):
            return True
        return True

    def resolve_reference(self, source: str) -> dict[str, str]:
        body = self._parse_body(source)
        latest_reference: Optional[dict[str, str]] = None
        for stmt in body:
            latest_reference = self._record_reference_from_statement(stmt, latest_reference)
        if latest_reference is None:
            raise OciSdkCompileError(
                "Could not find an OCI SDK method reference or call in this snippet"
            )
        return latest_reference

    def _parse_body(self, source: str) -> list[ast.stmt]:
        try:
            tree = ast.parse(source, mode="exec")
        except SyntaxError as exc:
            raise OciSdkCompileError(f"Invalid Python syntax: {exc.msg}") from exc

        body = list(tree.body)
        if not body:
            raise OciSdkCompileError("OCI SDK code must not be empty")
        return body

    def _compile_statement(
        self, stmt: ast.stmt, *, is_final: bool, allow_reference_final: bool
    ) -> None:
        if isinstance(stmt, ast.Import):
            self._register_import(stmt)
            return
        if isinstance(stmt, ast.ImportFrom):
            self._register_from_import(stmt)
            return
        if isinstance(stmt, ast.Assign):
            self._compile_assignment(stmt)
            return
        if isinstance(stmt, ast.Expr):
            step = self._try_compile_sdk_step(stmt.value)
            if step is not None:
                self.steps.append(step)
                return
            if is_final and allow_reference_final:
                self._compile_method_reference_expr(stmt.value)
                return
        raise OciSdkCompileError(
            "This OCI Python snippet uses a statement the server cannot translate yet. "
            "Supported patterns are OCI imports, simple assignments, and OCI SDK calls."
        )

    def _compile_program_statement(self, stmt: ast.stmt, *, is_final: bool) -> None:
        if isinstance(stmt, ast.Import):
            self._register_import(stmt)
            return
        if isinstance(stmt, ast.ImportFrom):
            self._register_from_import(stmt)
            return
        if isinstance(stmt, ast.Assign):
            self._compile_program_assignment(stmt, is_final=is_final)
            return
        if isinstance(stmt, ast.Expr):
            step = self._try_compile_sdk_step(stmt.value)
            if step is not None:
                self.steps.append(step)
                self.program.append({"type": "call", **deepcopy(step)})
                return
            if not is_final:
                raise OciSdkCompileError(
                    "Only the final non-call expression may be used as output. "
                    "Put any derived value in an assignment, or keep the final expression last."
                )
            self._validate_runtime_expr(stmt.value)
            self.program.append(
                {
                    "type": "output",
                    "expr": deepcopy(stmt.value),
                    "source": ast.unparse(stmt.value),
                }
            )
            return
        raise OciSdkCompileError(
            "This OCI Python snippet uses Python the server cannot translate yet. "
            "Supported patterns are OCI imports, client setup, SDK calls, simple derived bindings, "
            "and a final output expression."
        )

    def _compile_setup_statement(self, stmt: ast.stmt) -> None:
        if isinstance(stmt, ast.Import):
            self._register_import(stmt)
            return
        if isinstance(stmt, ast.ImportFrom):
            self._register_from_import(stmt)
            return
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                raise OciSdkCompileError("Only single-name assignments are supported")
            target_name = stmt.targets[0].id
            if self._bind_client_assignment(target_name, stmt.value):
                return
            bindable = self._try_compile_bindable_value(stmt.value)
            if bindable is not None:
                self.value_bindings[target_name] = bindable
                return
            if self._is_safe_setup_call(stmt.value):
                self.value_bindings[target_name] = _IgnoredSetupValue(ast.unparse(stmt.value))
                return
        raise OciSdkCompileError(
            "Only OCI imports, simple assignments, and OCI SDK calls are supported before the final reference"
        )

    def _record_reference_from_statement(
        self, stmt: ast.stmt, latest_reference: Optional[dict[str, str]]
    ) -> Optional[dict[str, str]]:
        if isinstance(stmt, ast.Import):
            self._register_import(stmt)
            return latest_reference
        if isinstance(stmt, ast.ImportFrom):
            self._register_from_import(stmt)
            return latest_reference
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                target_name = stmt.targets[0].id
                if self._bind_client_assignment(target_name, stmt.value):
                    return latest_reference
                bindable = self._try_compile_bindable_value(stmt.value)
                if bindable is not None:
                    self.value_bindings[target_name] = bindable
                    return latest_reference
                if self._is_safe_setup_call(stmt.value):
                    self.value_bindings[target_name] = _IgnoredSetupValue(ast.unparse(stmt.value))
                    return latest_reference
            reference = self._try_compile_method_reference_expr(stmt.value)
            return reference or latest_reference
        if isinstance(stmt, ast.Expr):
            reference = self._try_compile_method_reference_expr(stmt.value)
            return reference or latest_reference
        return latest_reference

    def _compile_assignment(self, stmt: ast.Assign) -> None:
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            raise OciSdkCompileError("Only single-name assignments are supported")
        target_name = stmt.targets[0].id

        if self._bind_client_assignment(target_name, stmt.value):
            return

        step = self._try_compile_sdk_step(stmt.value)
        if step is not None:
            step["label"] = target_name
            self.steps.append(step)
            self.runtime_labels.add(target_name)
            return

        bindable = self._try_compile_bindable_value(stmt.value)
        if bindable is not None:
            self.value_bindings[target_name] = bindable
            if is_final and self.steps:
                self.program.append(
                    {
                        "type": "output",
                        "expr": ast.Name(id=target_name, ctx=ast.Load()),
                        "source": target_name,
                    }
                )
            return

        if self._is_safe_setup_call(stmt.value):
            self.value_bindings[target_name] = _IgnoredSetupValue(ast.unparse(stmt.value))
            return

        raise OciSdkCompileError(
            f"Unsupported assignment to '{target_name}'. "
            "Only OCI client constructors, SDK calls, and simple data/model values are supported."
        )

    def _compile_program_assignment(self, stmt: ast.Assign, *, is_final: bool) -> None:
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            raise OciSdkCompileError("Only single-name assignments are supported")
        target_name = stmt.targets[0].id

        if self._bind_client_assignment(target_name, stmt.value):
            return

        step = self._try_compile_sdk_step(stmt.value)
        if step is not None:
            step["label"] = target_name
            self.steps.append(step)
            self.program.append({"type": "call", **deepcopy(step)})
            self.runtime_labels.add(target_name)
            return

        bindable = self._try_compile_bindable_value(stmt.value)
        if bindable is not None:
            self.value_bindings[target_name] = bindable
            return

        if self._is_safe_setup_call(stmt.value):
            self.value_bindings[target_name] = _IgnoredSetupValue(ast.unparse(stmt.value))
            return

        self._validate_runtime_expr(stmt.value)
        self.program.append(
            {
                "type": "bind",
                "label": target_name,
                "expr": deepcopy(stmt.value),
                "source": ast.unparse(stmt.value),
                "final": is_final,
            }
        )
        self.runtime_labels.add(target_name)

    def _register_import(self, stmt: ast.Import) -> None:
        for alias in stmt.names:
            if not alias.name.startswith("oci"):
                raise OciSdkCompileError("Only imports from the OCI SDK are supported")
            if alias.asname:
                self.module_aliases[alias.asname] = alias.name
                continue
            top_level = alias.name.split(".", 1)[0]
            if top_level == "oci":
                self.module_aliases.setdefault("oci", "oci")
            else:
                self.module_aliases[top_level] = top_level

    def _register_from_import(self, stmt: ast.ImportFrom) -> None:
        if stmt.level != 0 or not stmt.module or not stmt.module.startswith("oci"):
            raise OciSdkCompileError("Only imports from the OCI SDK are supported")

        for alias in stmt.names:
            if alias.name == "*":
                raise OciSdkCompileError("Wildcard imports are not supported")
            binding_name = alias.asname or alias.name
            candidate_module = f"{stmt.module}.{alias.name}"
            if self._is_importable_module(candidate_module):
                self.module_aliases[binding_name] = candidate_module
            else:
                self.symbol_aliases[binding_name] = candidate_module

    def _bind_client_assignment(self, target_name: str, value: ast.AST) -> bool:
        client_fqn = self._try_resolve_client_constructor(value)
        if not client_fqn:
            return False
        self.client_bindings[target_name] = client_fqn
        return True

    def _try_compile_sdk_step(self, node: ast.AST) -> Optional[dict[str, Any]]:
        if not isinstance(node, ast.Call):
            return None

        resolved = self._parse_call_target(node.func)
        if resolved is None:
            return None
        client_fqn, operation = resolved

        params = self._compile_call_arguments(node, client_fqn, operation)
        return {
            "client_fqn": client_fqn,
            "operation": operation,
            "params": params,
        }

    def _compile_method_reference_expr(self, node: ast.AST) -> dict[str, str]:
        resolved = self._try_compile_method_reference_expr(node)
        if resolved is not None:
            return resolved
        raise OciSdkCompileError(
            "Expected one OCI SDK method reference or call like "
            "'oci.identity.IdentityClient.list_regions()'"
        )

    def _try_compile_method_reference_expr(self, node: ast.AST) -> Optional[dict[str, str]]:
        if isinstance(node, ast.Call):
            resolved = self._parse_call_target(node.func)
        else:
            resolved = self._parse_call_target(node)
        if resolved is None:
            return None
        client_fqn, operation = resolved
        return {"client_fqn": client_fqn, "operation": operation}

    def _parse_call_target(self, node: ast.AST) -> Optional[tuple[str, str]]:
        if not isinstance(node, ast.Attribute):
            return None

        client_fqn = self._resolve_client_expression(node.value)
        if not client_fqn:
            return None
        operation = node.attr
        if not self._client_has_operation(client_fqn, operation):
            raise OciSdkCompileError(f"{client_fqn} has no callable operation '{operation}'")
        return client_fqn, operation

    def _resolve_client_expression(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name) and node.id in self.client_bindings:
            return self.client_bindings[node.id]

        if isinstance(node, ast.Call):
            return self._try_resolve_client_constructor(node)

        fqn = self._resolve_dotted_path(node)
        if fqn and self._is_client_class_fqn(fqn):
            return fqn
        return None

    def _try_resolve_client_constructor(self, node: ast.AST) -> Optional[str]:
        if not isinstance(node, ast.Call):
            return None
        if any(keyword.arg is None for keyword in node.keywords):
            raise OciSdkCompileError("**kwargs are not supported")

        fqn = self._resolve_dotted_path(node.func)
        if not fqn or not self._is_client_class_fqn(fqn):
            return None
        return fqn

    def _compile_call_arguments(
        self, node: ast.Call, client_fqn: str, operation: str
    ) -> dict[str, Any]:
        if any(keyword.arg is None for keyword in node.keywords):
            raise OciSdkCompileError("**kwargs are not supported")

        params: dict[str, Any] = {}
        if node.args:
            method = self._load_client_method(client_fqn, operation)
            param_names = [
                param.name
                for param in inspect.signature(method).parameters.values()
                if param.name != "self" and param.kind != inspect.Parameter.VAR_KEYWORD
            ]
            if len(node.args) > len(param_names):
                raise OciSdkCompileError(
                    f"{client_fqn}.{operation} accepts at most {len(param_names)} positional arguments here"
                )
            for index, arg in enumerate(node.args):
                params[param_names[index]] = self._compile_value(arg)

        for keyword in node.keywords:
            if keyword.arg in params:
                raise OciSdkCompileError(f"Argument '{keyword.arg}' was provided more than once")
            params[keyword.arg] = self._compile_value(keyword.value)
        return params

    def _try_compile_bindable_value(self, node: ast.AST) -> Optional[Any]:
        try:
            return self._compile_value(node)
        except OciSdkCompileError:
            return None

    def _compile_value(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.List):
            return [self._compile_value(item) for item in node.elts]
        if isinstance(node, ast.Tuple):
            return [self._compile_value(item) for item in node.elts]
        if isinstance(node, ast.Dict):
            compiled: dict[str, Any] = {}
            for key_node, value_node in zip(node.keys, node.values, strict=True):
                if key_node is None:
                    raise OciSdkCompileError("Dict unpacking is not supported")
                key = self._compile_value(key_node)
                if not isinstance(key, str):
                    raise OciSdkCompileError("Only string keys are supported in dict literals")
                if key.startswith("__"):
                    raise OciSdkCompileError(
                        f"Dict key '{key}' is reserved for internal metadata and is not allowed"
                    )
                compiled[key] = self._compile_value(value_node)
            return compiled
        if isinstance(node, ast.Name):
            return self._resolve_name_value(node.id)
        if isinstance(node, ast.Attribute):
            return self._compile_reference_or_attr_value(node)
        if isinstance(node, ast.Subscript):
            return self._compile_subscript_value(node)
        if isinstance(node, ast.Call):
            return self._compile_nested_call(node)
        raise OciSdkCompileError(
            f"Unsupported expression type: {node.__class__.__name__}. "
            "Only literals, dicts/lists, SDK model constructors, and simple references are supported."
        )

    def _resolve_name_value(self, name: str) -> Any:
        if name in self.value_bindings:
            value = self.value_bindings[name]
            if isinstance(value, _IgnoredSetupValue):
                return ResultReference(name)
            return deepcopy(value)
        if name in self.runtime_labels:
            return ResultReference(name)
        raise OciSdkCompileError(f"Unknown value '{name}'")

    def _compile_reference_or_attr_value(self, node: ast.Attribute) -> Any:
        if isinstance(node.value, ast.Name) and node.value.id in self.runtime_labels:
            return ResultReference(node.value.id, (("attr", node.attr),))
        if isinstance(node.value, ast.Name) and node.value.id in self.value_bindings:
            base_value = self._resolve_name_value(node.value.id)
            if isinstance(base_value, ResultReference):
                return ResultReference(base_value.label, base_value.path + (("attr", node.attr),))

        base_fqn = self._resolve_dotted_path(node)
        if base_fqn and base_fqn.startswith("oci."):
            raise OciSdkCompileError(
                f"Unexpected OCI symbol '{base_fqn}' in value position. "
                "Did you mean to call an OCI model constructor?"
            )

        if isinstance(node.value, ast.Attribute):
            parent = self._compile_reference_or_attr_value(node.value)
            if isinstance(parent, ResultReference):
                return ResultReference(parent.label, parent.path + (("attr", node.attr),))

        if isinstance(node.value, ast.Subscript):
            parent = self._compile_subscript_value(node.value)
            if isinstance(parent, ResultReference):
                return ResultReference(parent.label, parent.path + (("attr", node.attr),))

        raise OciSdkCompileError("Only result references support attribute access")

    def _compile_subscript_value(self, node: ast.Subscript) -> Any:
        segment = self._compile_subscript_segment(node.slice)
        base_value: Any
        if isinstance(node.value, ast.Name) and node.value.id in self.runtime_labels:
            return ResultReference(node.value.id, (segment,))
        if isinstance(node.value, ast.Attribute):
            base_value = self._compile_reference_or_attr_value(node.value)
            if isinstance(base_value, ResultReference):
                return ResultReference(base_value.label, base_value.path + (segment,))
            return self._resolve_static_path(base_value, (segment,))
        if isinstance(node.value, ast.Subscript):
            base_value = self._compile_subscript_value(node.value)
            if isinstance(base_value, ResultReference):
                return ResultReference(base_value.label, base_value.path + (segment,))
            return self._resolve_static_path(base_value, (segment,))
        if isinstance(node.value, ast.Name) and node.value.id in self.value_bindings:
            base_value = self._resolve_name_value(node.value.id)
            if isinstance(base_value, ResultReference):
                return ResultReference(base_value.label, base_value.path + (segment,))
            return self._resolve_static_path(base_value, (segment,))
        raise OciSdkCompileError("Only result references and bound literals support indexing")

    def _compile_subscript_segment(self, node: ast.AST) -> tuple[str, Any]:
        key = self._compile_value(node)
        if isinstance(key, str):
            return ("key", key)
        if isinstance(key, int):
            return ("index", key)
        raise OciSdkCompileError("Only string and integer subscripts are supported")

    def _resolve_static_path(self, value: Any, path: tuple[tuple[str, Any], ...]) -> Any:
        current = deepcopy(value)
        for kind, piece in path:
            if kind == "index":
                current = current[piece]
                continue
            if isinstance(current, dict):
                current = current[piece]
                continue
            raise OciSdkCompileError("Only dict and list literals support compile-time indexing")
        return current

    def _compile_nested_call(self, node: ast.Call) -> Any:
        if any(keyword.arg is None for keyword in node.keywords):
            raise OciSdkCompileError("**kwargs are not supported")

        call_fqn = self._resolve_dotted_path(node.func)
        if call_fqn == "dict":
            if node.args:
                raise OciSdkCompileError("dict(...) only supports keyword arguments in OCI SDK code")
            compiled: dict[str, Any] = {}
            for keyword in node.keywords:
                if keyword.arg.startswith("__"):
                    raise OciSdkCompileError(
                        f"Dict key '{keyword.arg}' is reserved for internal metadata and is not allowed"
                    )
                compiled[keyword.arg] = self._compile_value(keyword.value)
            return compiled

        if call_fqn and self._is_model_class_fqn(call_fqn):
            if node.args:
                raise OciSdkCompileError("OCI model constructors must use keyword arguments only")
            compiled: dict[str, Any] = {"__model_fqn": call_fqn}
            for keyword in node.keywords:
                compiled[keyword.arg] = self._compile_value(keyword.value)
            return compiled

        raise OciSdkCompileError(
            "Only OCI SDK model constructors and dict(...) are supported in nested expressions"
        )

    def _validate_runtime_expr(self, node: ast.AST, local_names: Optional[set[str]] = None) -> None:
        locals_now = local_names or set()
        if isinstance(node, ast.Constant):
            return
        if isinstance(node, ast.Name):
            if node.id in locals_now:
                return
            if node.id in self.value_bindings:
                return
            if node.id in self.runtime_labels:
                return
            raise OciSdkCompileError(f"Unknown value '{node.id}'")
        if isinstance(node, ast.Attribute):
            self._validate_runtime_expr(node.value, locals_now)
            return
        if isinstance(node, ast.Subscript):
            self._validate_runtime_expr(node.value, locals_now)
            self._validate_runtime_expr(node.slice, locals_now)
            return
        if isinstance(node, ast.List):
            for item in node.elts:
                self._validate_runtime_expr(item, locals_now)
            return
        if isinstance(node, ast.Tuple):
            for item in node.elts:
                self._validate_runtime_expr(item, locals_now)
            return
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=True):
                if key is None:
                    raise OciSdkCompileError("Dict unpacking is not supported")
                self._validate_runtime_expr(key, locals_now)
                self._validate_runtime_expr(value, locals_now)
            return
        if isinstance(node, ast.ListComp):
            if len(node.generators) != 1:
                raise OciSdkCompileError("Only single-generator list comprehensions are supported")
            generator = node.generators[0]
            if generator.is_async:
                raise OciSdkCompileError("Async comprehensions are not supported")
            if not isinstance(generator.target, ast.Name):
                raise OciSdkCompileError("Only simple loop variables are supported in comprehensions")
            self._validate_runtime_expr(generator.iter, locals_now)
            nested_locals = set(locals_now)
            nested_locals.add(generator.target.id)
            for condition in generator.ifs:
                self._validate_runtime_expr(condition, nested_locals)
            self._validate_runtime_expr(node.elt, nested_locals)
            return
        if isinstance(node, ast.Compare):
            self._validate_runtime_expr(node.left, locals_now)
            for comparator in node.comparators:
                self._validate_runtime_expr(comparator, locals_now)
            return
        if isinstance(node, ast.BoolOp):
            for value in node.values:
                self._validate_runtime_expr(value, locals_now)
            return
        if isinstance(node, ast.UnaryOp):
            self._validate_runtime_expr(node.operand, locals_now)
            return
        if isinstance(node, ast.Call):
            if any(keyword.arg is None for keyword in node.keywords):
                raise OciSdkCompileError("Only simple keyword-free builtins are supported in derived output")
            if not isinstance(node.func, ast.Name) or node.func.id not in {"str", "int", "float", "bool", "len"}:
                raise OciSdkCompileError(
                    "Only simple builtins like str(...), int(...), float(...), bool(...), and len(...) "
                    "are supported in derived output"
                )
            for arg in node.args:
                self._validate_runtime_expr(arg, locals_now)
            for keyword in node.keywords:
                self._validate_runtime_expr(keyword.value, locals_now)
            return
        raise OciSdkCompileError(
            "This OCI Python snippet includes derived Python the server cannot translate yet. "
            "Supported derived output is limited to names, attributes, indexing, literals, "
            "simple comparisons, boolean tests, a few pure builtins, and single-generator list comprehensions."
        )

    def _resolve_dotted_path(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            if node.id in self.module_aliases:
                return self.module_aliases[node.id]
            if node.id in self.symbol_aliases:
                return self.symbol_aliases[node.id]
            if node.id in self.client_bindings:
                return self.client_bindings[node.id]
            return None
        if isinstance(node, ast.Attribute):
            base = self._resolve_dotted_path(node.value)
            if not base:
                return None
            return f"{base}.{node.attr}"
        return None

    def _is_importable_module(self, module_name: str) -> bool:
        try:
            import_module(module_name)
            return True
        except Exception:
            return False

    def _is_client_class_fqn(self, client_fqn: str) -> bool:
        try:
            module_name, class_name = client_fqn.rsplit(".", 1)
            module = import_module(module_name)
            cls = getattr(module, class_name)
            return inspect.isclass(cls) and class_name.endswith("Client")
        except Exception:
            return False

    def _is_model_class_fqn(self, model_fqn: str) -> bool:
        if not model_fqn.startswith("oci.") or ".models." not in model_fqn:
            return False
        try:
            module_name, class_name = model_fqn.rsplit(".", 1)
            module = import_module(module_name)
            cls = getattr(module, class_name)
            return inspect.isclass(cls)
        except Exception:
            return False

    def _client_has_operation(self, client_fqn: str, operation: str) -> bool:
        try:
            method = self._load_client_method(client_fqn, operation)
            return callable(method)
        except Exception:
            return False

    def _load_client_method(self, client_fqn: str, operation: str):
        module_name, class_name = client_fqn.rsplit(".", 1)
        module = import_module(module_name)
        cls = getattr(module, class_name)
        if not inspect.isclass(cls):
            raise OciSdkCompileError(f"{client_fqn} is not a concrete OCI SDK client class")
        if not hasattr(cls, operation):
            raise OciSdkCompileError(f"{client_fqn} has no callable operation '{operation}'")
        return getattr(cls, operation)

    def _is_safe_setup_call(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.Call):
            return False
        call_fqn = self._resolve_dotted_path(node.func)
        return bool(call_fqn and call_fqn.startswith(SAFE_SETUP_CALL_PREFIXES))


def _validate_procedure_steps(steps: list[dict[str, Any]]) -> None:
    if not steps:
        raise OciSdkCompileError("OCI SDK code must include at least one SDK call")
    if len(steps) > MAX_PROCEDURE_STEPS:
        raise OciSdkCompileError(f"OCI SDK procedures may contain at most {MAX_PROCEDURE_STEPS} steps")

    destructive_indexes = [
        index
        for index, step in enumerate(steps)
        if step["operation"].startswith(DESTRUCTIVE_OPERATION_PREFIXES)
    ]
    if len(destructive_indexes) > 1:
        raise OciSdkCompileError("OCI SDK procedures may contain at most one destructive step")
    if destructive_indexes and destructive_indexes[-1] != len(steps) - 1:
        raise OciSdkCompileError("A destructive OCI SDK operation is only allowed as the final step")


def compile_oci_sdk_call(source: str) -> dict[str, Any]:
    env = _CompileEnv()
    steps = env.compile_module(source)
    if len(steps) != 1:
        raise OciSdkCompileError("Expected exactly one OCI SDK call")
    step = steps[0]
    step.pop("label", None)
    return step


def compile_oci_sdk_procedure(source: str) -> dict[str, list[dict[str, Any]]]:
    env = _CompileEnv()
    steps = env.compile_module(source)
    _validate_procedure_steps(steps)
    return {"steps": steps}


def compile_oci_sdk_program(source: str, *, best_effort: bool = False) -> dict[str, Any]:
    env = _CompileEnv()
    plan = env.compile_program(source, best_effort=best_effort)
    _validate_procedure_steps(plan["steps"])
    return plan


def resolve_oci_sdk_reference(source: str) -> dict[str, str]:
    env = _CompileEnv()
    return env.resolve_reference(source)
