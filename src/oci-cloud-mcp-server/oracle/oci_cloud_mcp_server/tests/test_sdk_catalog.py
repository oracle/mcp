"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Pinned SDK inventory and fail-closed resolution contracts.
"""

import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

import oci
import pytest


PACKAGE = Path(__file__).resolve().parents[3]
GENERATOR = PACKAGE / "scripts" / "generate_sdk_catalog.py"
RESOURCE = PACKAGE / "oracle" / "oci_cloud_mcp_server" / "sdk_catalog.json"


def _manifest_sdk_version():
    manifest = tomllib.loads((PACKAGE / "pyproject.toml").read_text())
    sdk_pins = []
    for dependency in manifest["project"]["dependencies"]:
        name, comparison, pin = dependency.partition("==")
        if name.strip().lower() == "oci" and comparison:
            sdk_pins.append(pin.strip())
    assert len(sdk_pins) == 1, "Cloud requires one exact OCI SDK dependency pin"
    return sdk_pins[0]


SDK_VERSION = _manifest_sdk_version()
MISMATCHED_SDK_VERSION = f"{SDK_VERSION}{'.' if '+' in SDK_VERSION else '+'}mismatch"


def generator():
    assert GENERATOR.is_file(), "Maintainer catalog generator has not been implemented"
    spec = importlib.util.spec_from_file_location("generate_sdk_catalog", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_catalog_sdk_version_matches_manifest_pin():
    assert json.loads(RESOURCE.read_bytes())["sdk_version"] == SDK_VERSION


@pytest.mark.parametrize("dependencies", [
    [], [f"oci>={SDK_VERSION}"], [f"oci=={SDK_VERSION}.*"], [f"oci==={SDK_VERSION}"],
    [f"oci=={SDK_VERSION}; python_version >= '3.13'"],
    [f"oci=={SDK_VERSION}", f"oci=={SDK_VERSION}"], [f"oci-other=={SDK_VERSION}"],
])
def test_generation_requires_one_exact_manifest_sdk_pin(tmp_path, dependencies):
    module = generator()
    assert hasattr(module, "read_sdk_pin"), "Manifest SDK pin validation has not been implemented"
    manifest = tmp_path / "pyproject.toml"
    manifest.write_text("[project]\ndependencies = " + json.dumps(dependencies) + "\n")
    with pytest.raises(ValueError, match="exact OCI SDK pin"):
        module.read_sdk_pin(manifest)


def test_sdk_pin_reader_accepts_other_dependencies_and_whitespace(tmp_path):
    module = generator()
    assert hasattr(module, "read_sdk_pin"), "Manifest SDK pin validation has not been implemented"
    manifest = tmp_path / "pyproject.toml"
    dependencies = ["oci-other==1.0.0", f"OCI == {SDK_VERSION}", "other>=1"]
    manifest.write_text("[project]\ndependencies = " + json.dumps(dependencies) + "\n")
    assert module.read_sdk_pin(manifest) == SDK_VERSION


def test_generation_rejects_manifest_sdk_mismatch_before_inventory(tmp_path, monkeypatch):
    module = generator()
    assert hasattr(module, "read_sdk_pin"), "Manifest SDK pin validation has not been implemented"
    (tmp_path / "pyproject.toml").write_text(f'[project]\ndependencies = ["oci=={MISMATCHED_SDK_VERSION}"]\n')
    monkeypatch.setattr(module, "PACKAGE", tmp_path)
    with pytest.raises(ValueError, match="requires OCI SDK") as error:
        module.generate_catalog()
    assert MISMATCHED_SDK_VERSION in str(error.value)


@pytest.mark.parametrize("mismatch", ["lock", "exceptions"])
def test_generation_checks_pinned_inputs_before_inventory(tmp_path, monkeypatch, mismatch):
    module = generator()
    assert hasattr(module, "read_sdk_pin"), "Manifest SDK pin validation has not been implemented"
    (tmp_path / "pyproject.toml").write_text(f'[project]\ndependencies = ["oci=={SDK_VERSION}"]\n')
    locked = MISMATCHED_SDK_VERSION if mismatch == "lock" else SDK_VERSION
    (tmp_path / "uv.lock").write_text(f'[[package]]\nname = "oci"\nversion = "{locked}"\n')
    if mismatch == "exceptions":
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "sdk_schema_exceptions.json").write_text(json.dumps({
            "sdk_version": MISMATCHED_SDK_VERSION, "references": [],
        }))
    monkeypatch.setattr(module, "PACKAGE", tmp_path)
    message = "lock/version mismatch" if mismatch == "lock" else "exceptions/version mismatch"
    with pytest.raises(ValueError, match=message):
        module.generate_catalog()


def test_generation_is_byte_stable():
    generate = generator().generate_catalog
    first = generate()
    assert first == generate()
    assert first == RESOURCE.read_bytes()
    catalog = json.loads(first)
    assert catalog["sdk_version"] == SDK_VERSION
    assert catalog["clients"]["oci.core.ComputeClient"]["aliases"] == [
        "oci.core.ComputeClient", "oci.core.compute_client.ComputeClient"
    ]
    assert catalog["models"]["oci.core.models.LaunchInstanceDetails"]["aliases"] == [
        "oci.core.models.LaunchInstanceDetails",
        "oci.core.models.launch_instance_details.LaunchInstanceDetails",
    ]


def test_check_detects_missing_or_changed_output(tmp_path):
    generator()
    target = tmp_path / "catalog.json"
    cmd = [sys.executable, str(GENERATOR), "--check", "--output", str(target)]
    missing = subprocess.run(cmd, capture_output=True, text=True)
    assert missing.returncode == 1
    assert not target.exists()
    target.write_text("{}\n")
    changed = subprocess.run(cmd, capture_output=True, text=True)
    assert changed.returncode == 1
    assert target.read_text() == "{}\n"
    target.write_bytes(RESOURCE.read_bytes())
    assert subprocess.run(cmd, capture_output=True, text=True).returncode == 0


def test_exported_sdk_surface_is_complete():
    """Independent export scan catches silent omissions from generation."""
    generator()
    sdk = Path(oci.__file__).parent
    expected_clients, expected_models = set(), set()
    for service in oci.__all__:
        init = sdk / service / "__init__.py"
        models = sdk / service / "models" / "__init__.py"
        if not init.is_file() or not models.is_file():
            continue
        for node in ast.parse(init.read_text()).body:
            if isinstance(node, ast.ImportFrom) and node.level == 1:
                expected_clients.update(
                    f"oci.{service}.{alias.asname or alias.name}"
                    for alias in node.names if alias.name.endswith("Client")
                )
        for node in ast.parse(models.read_text()).body:
            if isinstance(node, ast.ImportFrom) and node.level == 1:
                expected_models.update(
                    f"oci.{service}.models.{alias.asname or alias.name}" for alias in node.names
                )
    catalog = json.loads(RESOURCE.read_bytes())
    assert expected_clients and expected_models
    assert set(catalog["clients"]) == expected_clients
    assert set(catalog["models"]) == expected_models
    assert "oci.BaseClient" not in catalog["clients"]
    assert "oci.object_storage.UploadManager" not in catalog["clients"]
    assert not any("CompositeOperations" in name or "_vendor" in name for name in catalog["clients"])
    assert "__init__" not in catalog["clients"]["oci.core.ComputeClient"]["operations"]


def test_alias_collision_and_unresolved_export_fail_generation():
    module = generator()
    aliases = {}
    module.register_alias(aliases, "oci.core.ComputeClient", "first")
    with pytest.raises(ValueError, match="alias collision"):
        module.register_alias(aliases, "oci.core.ComputeClient", "second")
    with pytest.raises(ValueError, match="unresolved"):
        module.validate_model_references({
            "oci.core.models.Example": {
                "service": "oci.core", "name": "Example", "bases": [],
                "swagger_types": {"field": "MissingModel"},
            }
        })


def test_only_reviewed_sdk_schema_gaps_are_opaque():
    generator()
    catalog = json.loads(RESOURCE.read_bytes())
    exceptions = json.loads((PACKAGE / "scripts" / "sdk_schema_exceptions.json").read_bytes())
    assert exceptions["sdk_version"] == SDK_VERSION
    expected_fields = {}
    for identity, field, type_name in exceptions["references"]:
        expected_fields.setdefault(identity, set()).add(field)
        service = identity.rsplit(".models.", 1)[0]
        assert f"{service}.models.{type_name}" not in catalog["models"]
    for identity, record in catalog["models"].items():
        assert set(record["opaque_fields"]) == expected_fields.get(identity, set())


def catalog_module():
    path = RESOURCE.with_suffix(".py")
    assert path.is_file(), "Fail-closed catalog resolver has not been implemented"
    from oracle.oci_cloud_mcp_server import sdk_catalog
    return sdk_catalog


def test_catalog_aliases_resolve_to_identical_genuine_classes():
    module = catalog_module()
    catalog = module.load_catalog()
    client = catalog.client("oci.core.ComputeClient")
    assert catalog.client("oci.core.compute_client.ComputeClient") is client
    assert catalog.load_client(client) is oci.core.ComputeClient
    model = catalog.model("LaunchInstanceDetails", "oci.core")
    assert catalog.model("oci.core.models.launch_instance_details.LaunchInstanceDetails") is model
    assert catalog.load_model(model) is oci.core.models.LaunchInstanceDetails
    with pytest.raises(TypeError):
        model.swagger_types["extra"] = "str"


@pytest.mark.parametrize("name", [
    "urllib.request.URLopener", "oci.fake.UnknownClient", "oci.BaseClient",
    "oci._vendor.jwt.PyJWKClient", "oci.core.ComputeClientCompositeOperations",
    "oci.object_storage.UploadManager", "", None,
])
def test_rejected_clients_do_not_load_modules(name, monkeypatch):
    module = catalog_module()
    catalog = module.load_catalog()
    monkeypatch.setattr(module, "import_module", lambda name: pytest.fail(f"Unexpected import {name}"))
    with pytest.raises(module.SdkResolutionError):
        catalog.client(name)


@pytest.mark.parametrize("name", ["__init__", "_call_api", "missing", "base_client", None])
def test_rejected_operations_do_not_load_modules(name, monkeypatch):
    module = catalog_module()
    catalog = module.load_catalog()
    monkeypatch.setattr(module, "import_module", lambda name: pytest.fail(f"Unexpected import {name}"))
    with pytest.raises(module.SdkResolutionError):
        catalog.operation(catalog.client("oci.core.ComputeClient"), name)


@pytest.mark.parametrize("mutation", [
    "sdk_version", "schema_version", "alias_collision", "module", "operation", "base", "type", "keys",
])
def test_malformed_catalogs_fail_closed(mutation):
    module = catalog_module()
    raw = json.loads(RESOURCE.read_bytes())
    client = raw["clients"]["oci.core.ComputeClient"]
    model = raw["models"]["oci.core.models.LaunchInstanceDetails"]
    if mutation == "sdk_version":
        raw["sdk_version"] = MISMATCHED_SDK_VERSION
    elif mutation == "schema_version":
        raw["schema_version"] = True
    elif mutation == "alias_collision":
        client["aliases"].append("oci.identity.IdentityClient")
    elif mutation == "module":
        client["module"] = "oci.fake.attacker_client"
    elif mutation == "operation":
        client["operations"]["__init__"] = {"summary": ""}
    elif mutation == "base":
        model["bases"] = ["oci.core.models.NotExported"]
    elif mutation == "type":
        model["swagger_types"]["source_details"] = "NotExported"
    elif mutation == "keys":
        raw["surprise"] = True
    with pytest.raises(module.SdkResolutionError):
        module.SdkCatalog.from_bytes(json.dumps(raw).encode(), SDK_VERSION, SDK_VERSION)


@pytest.mark.parametrize("data", [b"not json", b"{}", b'{"schema_version":1,"schema_version":1}'])
def test_invalid_json_is_a_catalog_error(data):
    module = catalog_module()
    with pytest.raises(module.SdkResolutionError):
        module.SdkCatalog.from_bytes(data, SDK_VERSION, SDK_VERSION)


def test_installed_sdk_and_reported_version_must_both_match():
    module = catalog_module()
    for installed, reported in [(MISMATCHED_SDK_VERSION, SDK_VERSION), (SDK_VERSION, MISMATCHED_SDK_VERSION)]:
        with pytest.raises(module.SdkResolutionError, match="version"):
            module.SdkCatalog.from_bytes(RESOURCE.read_bytes(), installed, reported)


def test_missing_resource_fails_closed(monkeypatch):
    module = catalog_module()
    module.load_catalog.cache_clear()
    monkeypatch.setattr(module, "files", lambda package: Path("/nonexistent-sdk-catalog-test"))
    try:
        with pytest.raises(module.SdkResolutionError, match="catalog"):
            module.load_catalog()
    finally:
        module.load_catalog.cache_clear()


@pytest.mark.parametrize("http", [False, True])
def test_startup_checks_catalog_before_auth_or_serving(http):
    code = '''
from oracle.oci_cloud_mcp_server import sdk_catalog
import oracle_mcp_common
import fastmcp
def unexpected(*args, **kwargs):
    raise AssertionError("auth/server initialized before catalog validation")
oracle_mcp_common.build_auth_context = unexpected
oracle_mcp_common.build_idcs_http_auth = unexpected
fastmcp.FastMCP = unexpected
def reject():
    raise sdk_catalog.SdkResolutionError("missing catalog fixture")
sdk_catalog.load_catalog = reject
try:
    import oracle.oci_cloud_mcp_server.server
except sdk_catalog.SdkResolutionError:
    pass
else:
    raise AssertionError("server imported with invalid catalog")
'''
    env = dict(os.environ)
    if http:
        env.update(ORACLE_MCP_HOST="127.0.0.1", ORACLE_MCP_PORT="8181")
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr


def test_installed_smoke_refuses_editable_source_tree(tmp_path):
    smoke = PACKAGE / "scripts" / "check_installed_catalog.py"
    assert smoke.is_file(), "Installed-distribution smoke has not been implemented"
    result = subprocess.run(
        [sys.executable, str(smoke), "--forbid-root", str(PACKAGE)],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "origin" in result.stderr
