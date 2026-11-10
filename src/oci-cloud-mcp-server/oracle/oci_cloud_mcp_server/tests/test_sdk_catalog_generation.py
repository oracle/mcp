"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Maintainer generator rejection paths and independent SDK reconciliation.
"""

import importlib.util
from importlib import import_module
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


PACKAGE = Path(__file__).resolve().parents[3]

CLIENT_SOURCE = '''
raise AssertionError("SDK client module must not be imported")
class SampleClient:
    def __init__(self):
        raise AssertionError("SDK client must not be constructed")

    def list_samples(self):
        """List samples."""
        return self.base_client.call_api("samples")

    def update_sample(self):
        """Update a sample."""
        return self.base_client.call_api("sample")

    def _helper(self):
        return None
'''

BASE_SOURCE = '''
raise AssertionError("SDK model module must not be imported")
class Base(object):
    def describe(self):
        return None

    def __init__(self):
        self.ignored = None
        self.swagger_types = {"name": "str", "children": "list[Child]", "lookup": "dict(str, list[Child])"}
        self.attribute_map = {"name": "name", "children": "children", "lookup": "lookup"}
        raise AssertionError("SDK model must not be constructed")
'''

CHILD_SOURCE = '''
from .base import Base
class Child(Base):
    def __init__(self):
        self.swagger_types = {"name": "str"}
        self.attribute_map = {"name": "name"}
        raise AssertionError("SDK model must not be constructed")
'''


@pytest.fixture
def sdk_tree(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("catalog_generator_fixture", PACKAGE / "scripts/generate_sdk_catalog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    version = module.read_sdk_pin(PACKAGE / "pyproject.toml")
    package, sdk = tmp_path / "package", tmp_path / "sdk" / "oci"
    files = {
        package / "pyproject.toml": f'[project]\ndependencies = ["oci=={version}"]\n',
        package / "uv.lock": (
            f'[[package]]\nname = "oci"\nversion = "{version}"\n'
            f'sdist = {{hash = "sha256:{"a" * 64}"}}\nwheels = []\n'
        ),
        package / "scripts/sdk_schema_exceptions.json": json.dumps({"sdk_version": version, "references": []}),
        sdk / "__init__.py": 'raise AssertionError("SDK root must not be imported")\n__all__ = ["sample", "auth", "utility"]\n',
        sdk / "auth/__init__.py": 'raise AssertionError("Utility package must not be imported")\n',
        sdk / "utility.py": 'raise AssertionError("Utility module must not be imported")\n',
        sdk / "sample/__init__.py": 'from .sample_client import SampleClient\nfrom .transfer import TransferHelper\n',
        sdk / "sample/sample_client.py": CLIENT_SOURCE,
        sdk / "sample/models/__init__.py": (
            'from .base import Base\nfrom .child import Child\n'
            'sample_type_mapping = {"Base": Base, "Child": Child}\n'
        ),
        sdk / "sample/models/base.py": BASE_SOURCE,
        sdk / "sample/models/child.py": CHILD_SOURCE,
    }
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    # Only redirect SDK location/version metadata; run the real source parser.
    monkeypatch.setattr(module, "oci", SimpleNamespace(__file__=str(sdk / "__init__.py"), __version__=version))
    monkeypatch.setattr(module, "PACKAGE", package)
    monkeypatch.setattr(module, "OUTPUT", package / "catalog.json")
    return module, package, sdk


def test_generation_records_operations_schemas_and_inheritance_without_execution(sdk_tree):
    module, _, _ = sdk_tree
    catalog = json.loads(module.generate_catalog())
    assert set(catalog["clients"]) == {"oci.sample.SampleClient"}
    client = catalog["clients"]["oci.sample.SampleClient"]
    assert client["operations"] == {
        "list_samples": {"summary": "List samples."},
        "update_sample": {"summary": "Update a sample."},
    }
    assert client["aliases"] == ["oci.sample.SampleClient", "oci.sample.sample_client.SampleClient"]
    assert set(catalog["models"]) == {"oci.sample.models.Base", "oci.sample.models.Child"}
    base = catalog["models"]["oci.sample.models.Base"]
    assert base["swagger_types"] == {
        "name": "str", "children": "list[Child]", "lookup": "dict(str, list[Child])",
    }
    assert base["attribute_map"] == {"name": "name", "children": "children", "lookup": "lookup"}
    assert base["bases"] == []
    assert catalog["models"]["oci.sample.models.Child"]["bases"] == ["oci.sample.models.Base"]
    assert all(record["opaque_fields"] == [] for record in catalog["models"].values())


@pytest.mark.parametrize("path,before,after,message", [
    ("sample/__init__.py", ".sample_client", ".helpers", "Unreviewed SDK client export"),
    ("sample/__init__.py", ".sample_client", "._private_client", "Unreviewed SDK client export"),
    ("sample/sample_client.py", "class SampleClient:", "class Other:", "Unresolved SDK class"),
    ("sample/sample_client.py", 'return self.base_client.call_api("samples")', "return []", "Unreviewed SDK public method"),
    ("sample/models/base.py", "self.swagger_types =", "self.unrelated =", "Unresolved swagger_types"),
    ("sample/models/base.py", "self.swagger_types = {", "self.swagger_types = []\n        ignored = {", "Unresolved swagger_types"),
    ("sample/models/base.py", '"name": "str"', '"name": 7', "Unresolved swagger_types"),
    ("sample/models/base.py", "def __init__(self):", "def setup(self):", "Unresolved swagger_types"),
    ("sample/models/base.py", "self.attribute_map =", "self.unrelated =", "Unresolved attribute_map"),
    ("sample/models/base.py", "dict(str, list[Child])", "dict(int, str)", "Unsupported SDK dictionary type"),
    ("sample/models/base.py", "dict(str, list[Child])", "dict(str)", "Unsupported SDK dictionary type"),
    ("sample/models/base.py", "list[Child]", "list[Missing]", "unresolved SDK type Missing"),
    ("sample/models/child.py", "class Child(Base):", "class Child(Missing):", "unresolved SDK base"),
    ("sample/models/child.py", "class Child(Base):", "class Child(models.Base):", "Unreviewed SDK model base"),
    ("sample/models/__init__.py", "sample_type_mapping", "other_mapping", "Unresolved SDK model type mapping"),
    ("sample/models/__init__.py", 'sample_type_mapping = {"Base": Base, "Child": Child}',
     "sample_type_mapping = []", "Unresolved SDK model type mapping"),
    ("sample/models/__init__.py", '"Child": Child', '"Child": Base', "SDK model exports/type mapping disagree"),
    ("sample/models/__init__.py", '"Child": Child', '"Child": build_child()', "SDK model exports/type mapping disagree"),
])
def test_generation_rejects_unreviewed_sdk_declarations(sdk_tree, path, before, after, message):
    module, _, sdk = sdk_tree
    target = sdk / path
    source = target.read_text()
    assert before in source
    target.write_text(source.replace(before, after))
    with pytest.raises(ValueError, match=message):
        module.generate_catalog()


def test_generation_rejects_new_packages_without_model_exports(sdk_tree):
    module, _, sdk = sdk_tree
    (sdk / "__init__.py").write_text('__all__ = ["unreviewed"]\n')
    (sdk / "unreviewed").mkdir()
    (sdk / "unreviewed/__init__.py").write_text("")
    with pytest.raises(ValueError, match="Unreviewed SDK package without models: unreviewed"):
        module.generate_catalog()


def test_generation_rejects_resolved_schema_exceptions(sdk_tree):
    module, package, _ = sdk_tree
    path = package / "scripts/sdk_schema_exceptions.json"
    metadata = json.loads(path.read_bytes())
    # Child is now exported, so the previously missing reference is stale.
    metadata["references"] = [["oci.sample.models.Base", "children", "Child"]]
    path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="exceptions no longer match"):
        module.generate_catalog()


def test_cli_generates_catalog_file(sdk_tree, monkeypatch, capsys):
    module, _, _ = sdk_tree
    monkeypatch.setattr(sys, "argv", ["generate_sdk_catalog.py"])
    assert module.main() == 0
    catalog = json.loads(module.OUTPUT.read_bytes())
    assert set(catalog["clients"]) == {"oci.sample.SampleClient"}
    assert catalog["models"]["oci.sample.models.Child"]["bases"] == ["oci.sample.models.Base"]
    assert "SDK catalog generated: sha256:" in capsys.readouterr().out


@pytest.mark.parametrize("state", ["missing", "changed", "matching"])
def test_cli_check_returns_status_without_rewriting(sdk_tree, monkeypatch, capsys, state):
    module, _, _ = sdk_tree
    if state == "matching":
        monkeypatch.setattr(sys, "argv", ["generate_sdk_catalog.py"])
        assert module.main() == 0
    elif state == "changed":
        module.OUTPUT.write_bytes(b"preserve this file\n")
    before = module.OUTPUT.read_bytes() if module.OUTPUT.exists() else None
    capsys.readouterr()
    monkeypatch.setattr(sys, "argv", ["generate_sdk_catalog.py", "--check"])
    assert module.main() == (0 if state == "matching" else 1)
    if before is None:
        assert not module.OUTPUT.exists()
    else:
        assert module.OUTPUT.read_bytes() == before
    result = capsys.readouterr()
    if state == "matching":
        assert "checked" in result.out
    else:
        assert "drift" in result.err


@pytest.mark.parametrize("failure", ["invalid_sdk", "missing_output_directory", "missing_exports"])
def test_cli_failures_do_not_publish_a_catalog(sdk_tree, monkeypatch, capsys, failure):
    module, package, sdk = sdk_tree
    target = module.OUTPUT
    if failure == "invalid_sdk":
        (sdk / "sample/sample_client.py").write_text(CLIENT_SOURCE.replace('return self.base_client.call_api("samples")', "return []"))
        target.write_bytes(b"preserve previous catalog\n")
    elif failure == "missing_output_directory":
        target = package / "absent/catalog.json"
    else:
        (sdk / "__init__.py").write_text("NO_EXPORTS = []\n")
    before = target.read_bytes() if target.exists() else None
    monkeypatch.setattr(sys, "argv", ["generate_sdk_catalog.py", "--output", str(target)])
    assert module.main() == 1
    assert "SDK catalog generation failed:" in capsys.readouterr().err
    if before is not None:
        assert target.read_bytes() == before
    else:
        assert not target.exists()


def test_catalog_operations_aliases_and_inheritance_match_installed_sdk():
    """Use real SDK class identity, independently of the generator's AST parser."""
    catalog = json.loads((PACKAGE / "oracle/oci_cloud_mcp_server/sdk_catalog.json").read_bytes())
    for identity, record in catalog["clients"].items():
        service, name = identity.rsplit(".", 1)
        client_class = getattr(import_module(service), name)
        assert client_class.__module__ == record["module"]
        assert client_class.__name__ == record["name"]
        assert set(record["aliases"]) == {identity, f"{client_class.__module__}.{client_class.__name__}"}
        assert getattr(import_module(client_class.__module__), client_class.__name__) is client_class
        expected_operations = {
            name for name, _ in inspect.getmembers(client_class, inspect.isfunction)
            if not name.startswith("_")
        }
        assert set(record["operations"]) == expected_operations, identity

    model_classes = {}
    for identity, record in catalog["models"].items():
        namespace, name = identity.rsplit(".", 1)
        model_class = getattr(import_module(namespace), name)
        assert model_class.__module__ == record["module"]
        assert model_class.__name__ == record["name"]
        assert set(record["aliases"]) == {identity, f"{model_class.__module__}.{model_class.__name__}"}
        assert getattr(import_module(model_class.__module__), model_class.__name__) is model_class
        model_classes[model_class] = identity
    for model_class, identity in model_classes.items():
        expected_bases = {model_classes[base] for base in model_class.__bases__ if base is not object}
        assert set(catalog["models"][identity]["bases"]) == expected_bases, identity
