"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Generate the reviewed inventory from the locked SDK's explicit source exports.

This maintainer command never imports the server or constructs SDK clients/models.
Generated service/model declarations are read as syntax, never evaluated as code.
"""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import tomllib

import oci


PACKAGE = Path(__file__).resolve().parents[1]
OUTPUT = PACKAGE / "oracle" / "oci_cloud_mcp_server" / "sdk_catalog.json"
PRIMITIVES = {"str", "int", "float", "bool", "object", "datetime", "date", "None", "bytes"}


def read_sdk_pin(manifest: Path) -> str:
    dependencies = tomllib.loads(manifest.read_text(encoding="utf-8"))["project"]["dependencies"]
    sdk_dependencies = [
        dependency.strip() for dependency in dependencies
        if re.match(r"oci(?=\s|[<>=!~\[@;]|$)", dependency.strip(), re.IGNORECASE)
    ]
    match = None
    if len(sdk_dependencies) == 1:
        match = re.fullmatch(r"oci\s*==\s*([0-9][A-Za-z0-9.!+-]*)", sdk_dependencies[0], re.IGNORECASE)
    if match is None:
        raise ValueError("pyproject.toml must declare one exact OCI SDK pin (oci==VERSION)")
    return match.group(1)


def register_alias(aliases: dict, alias: str, identity: str) -> None:
    if alias in aliases and aliases[alias] != identity:
        raise ValueError(f"SDK alias collision: {alias}")
    aliases[alias] = identity


def _exports(path: Path):
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            for alias in node.names:
                yield node.module, alias.name, alias.asname or alias.name


def _class(path: Path, name: str) -> ast.ClassDef:
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise ValueError(f"Unresolved SDK class: {name} in {path.name}")


def _schema(cls: ast.ClassDef, field: str) -> dict:
    for method in cls.body:
        if isinstance(method, ast.FunctionDef) and method.name == "__init__":
            for node in method.body:
                if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
                    and t.value.id == "self" and t.attr == field for t in node.targets
                ):
                    value = ast.literal_eval(node.value)
                    if isinstance(value, dict) and all(
                        isinstance(k, str) and isinstance(v, str) for k, v in value.items()
                    ):
                        return value
    raise ValueError(f"Unresolved {field} for SDK model {cls.name}")


def _type_leaves(type_name: str):
    compact = type_name.replace(" ", "")
    if compact.startswith("list[") and compact.endswith("]"):
        yield from _type_leaves(compact[5:-1])
    elif compact.startswith("dict(") and compact.endswith(")"):
        key, sep, value = compact[5:-1].partition(",")
        if not sep or key != "str":
            raise ValueError(f"Unsupported SDK dictionary type: {type_name}")
        yield from _type_leaves(value)
    else:
        yield compact


def validate_model_references(models: dict, exceptions: frozenset = frozenset()) -> None:
    observed = set()
    for identity, record in models.items():
        opaque = set()
        for field, type_name in record["swagger_types"].items():
            for leaf in _type_leaves(type_name):
                if leaf not in PRIMITIVES and f"{record['service']}.models.{leaf}" not in models:
                    reference = (identity, field, leaf)
                    if reference not in exceptions:
                        raise ValueError(f"unresolved SDK type {leaf} in {identity}")
                    observed.add(reference)
                    opaque.add(field)
        record["opaque_fields"] = sorted(opaque)
        for base in record["bases"]:
            if base not in models:
                raise ValueError(f"unresolved SDK base {base} in {identity}")
    if observed != exceptions:
        raise ValueError("Reviewed SDK schema exceptions no longer match the pinned exports")


def generate_catalog() -> bytes:
    sdk_version = read_sdk_pin(PACKAGE / "pyproject.toml")
    if oci.__version__ != sdk_version:
        raise ValueError(f"Generation requires OCI SDK {sdk_version}; found {oci.__version__}")
    lock = tomllib.loads((PACKAGE / "uv.lock").read_text(encoding="utf-8"))
    locked_sdk = next(p for p in lock["package"] if p["name"] == "oci")
    if locked_sdk["version"] != sdk_version:
        raise ValueError("SDK lock/version mismatch with pyproject.toml")
    gaps = json.loads((PACKAGE / "scripts" / "sdk_schema_exceptions.json").read_text(encoding="utf-8"))
    if gaps["sdk_version"] != sdk_version:
        raise ValueError("Schema exceptions/version mismatch with pyproject.toml")
    sdk = Path(oci.__file__).resolve().parent
    root = ast.parse((sdk / "__init__.py").read_text(encoding="utf-8"))
    services = next(
        ast.literal_eval(node.value) for node in ast.walk(root)
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
        )
    )
    clients, models, aliases = {}, {}, {}
    for service in sorted(services):
        service_path = sdk / service
        init, model_init = service_path / "__init__.py", service_path / "models" / "__init__.py"
        if not init.is_file():
            continue  # Root infrastructure classes and single-file utility modules.
        if not model_init.is_file():
            if service not in {"auth", "pagination", "retry", "circuit_breaker"}:
                raise ValueError(f"Unreviewed SDK package without models: {service}")
            continue
        namespace = f"oci.{service}"
        for module, name, exported in _exports(init):
            if not name.endswith("Client"):
                continue
            if not module.endswith("_client") or module.startswith("_"):
                raise ValueError(f"Unreviewed SDK client export: {namespace}.{exported}")
            cls = _class(service_path / f"{module}.py", name)
            operations = {}
            for method in cls.body:
                if not isinstance(method, ast.FunctionDef) or method.name.startswith("_"):
                    continue
                if not any(isinstance(n, ast.Attribute) and n.attr == "call_api" for n in ast.walk(method)):
                    raise ValueError(f"Unreviewed SDK public method: {namespace}.{name}.{method.name}")
                doc = ast.get_docstring(method) or ""
                operations[method.name] = {"summary": doc.partition("\n")[0]}
            identity = f"{namespace}.{exported}"
            record_aliases = sorted({identity, f"{namespace}.{module}.{name}"})
            for alias in record_aliases:
                register_alias(aliases, alias, identity)
            clients[identity] = {
                "module": f"{namespace}.{module}", "name": name, "service": namespace,
                "aliases": record_aliases, "operations": operations,
            }
        service_models = {}
        for module, name, exported in _exports(model_init):
            cls = _class(service_path / "models" / f"{module}.py", name)
            identity = f"{namespace}.models.{exported}"
            record_aliases = sorted({identity, f"{namespace}.models.{module}.{name}"})
            for alias in record_aliases:
                register_alias(aliases, alias, identity)
            bases = []
            for base in cls.bases:
                if not isinstance(base, ast.Name):
                    raise ValueError(f"Unreviewed SDK model base: {identity}")
                if base.id != "object":
                    bases.append(f"{namespace}.models.{base.id}")
            models[identity] = {
                "module": f"{namespace}.models.{module}", "name": name, "service": namespace,
                "aliases": record_aliases, "bases": sorted(bases),
                "swagger_types": _schema(cls, "swagger_types"),
                "attribute_map": _schema(cls, "attribute_map"),
            }
            service_models[exported] = exported
        mappings = [
            node.value for node in ast.parse(model_init.read_text(encoding="utf-8")).body
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id.endswith("_type_mapping") for t in node.targets
            )
        ]
        if len(mappings) != 1 or not isinstance(mappings[0], ast.Dict):
            raise ValueError(f"Unresolved SDK model type mapping: {namespace}")
        mapping = {
            ast.literal_eval(key): value.id for key, value in zip(mappings[0].keys, mappings[0].values)
            if isinstance(value, ast.Name)
        }
        if mapping != service_models:
            raise ValueError(f"SDK model exports/type mapping disagree: {namespace}")
    validate_model_references(models, frozenset(tuple(r) for r in gaps["references"]))
    catalog = {
        "schema_version": 1, "sdk_version": sdk_version,
        "sdk_artifacts": sorted(a["hash"] for a in [locked_sdk["sdist"], *locked_sdk["wheels"]]),
        "exclusions": {
            "infrastructure": "Root OCI utility classes and packages are not service clients.",
            "helpers": "Only exported generated service clients with API-dispatch methods are supported.",
            "composites": "Composite-operation wrappers are not service clients.",
            "private_vendor": "Private and vendor namespaces are not SDK service/model exports.",
        },
        "clients": clients, "models": models,
    }
    # Canonicalize nested maps while retaining the version metadata first.
    canonical = json.loads(json.dumps(catalog, sort_keys=True))
    ordered = {key: canonical[key] for key in catalog}
    return (json.dumps(ordered, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail on drift without writing")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    try:
        data = generate_catalog()
        if args.check:
            if not args.output.is_file() or args.output.read_bytes() != data:
                print("SDK catalog drift; regenerate in the locked maintainer environment", file=sys.stderr)
                return 1
        else:
            args.output.write_bytes(data)
        print(f"SDK catalog {'checked' if args.check else 'generated'}: sha256:{hashlib.sha256(data).hexdigest()}")
        return 0
    except (ValueError, OSError, StopIteration) as exc:
        print(f"SDK catalog generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
