"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from contextlib import contextmanager
import inspect
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from oracle.oci_cloud_mcp_server import server


def sdk_models(**exports):
    models = ModuleType("oci.fake.models")
    models.fake_type_mapping = {name: cls for name, cls in exports.items() if inspect.isclass(cls)}
    for name, cls in exports.items():
        setattr(models, name, cls)
        if inspect.isclass(cls) and not cls.__module__.startswith("oci."):
            cls.__module__ = models.__name__
    return models


def sdk_service_loader(importer, monkeypatch):
    """Adapt existing fake SDK modules into service exports, without bypassing class lookup."""
    services = {}

    def load(name):
        if name not in services:
            exports = importer(f"oci.{name}")
            try:
                models = importer(f"oci.{name}.models")
            except ImportError:
                models = SimpleNamespace()
            service = ModuleType(f"oci.{name}")
            service.__all__ = [*vars(exports), "models"]
            for alias, cls in vars(exports).items():
                setattr(service, alias, cls)
                if inspect.isclass(cls) and alias.endswith("Client"):
                    monkeypatch.setattr(cls, "__module__", f"oci.{name}.compute_client")
            model_types = getattr(models, f"{name}_type_mapping", {
                alias: cls for alias, cls in vars(models).items()
                if inspect.isclass(cls) and not alias.endswith("Client")
            })
            monkeypatch.setattr(models, "__name__", f"oci.{name}.models", raising=False)
            monkeypatch.setattr(models, f"{name}_type_mapping", model_types, raising=False)
            for cls in model_types.values():
                monkeypatch.setattr(cls, "__module__", f"oci.{name}.models")
            service.models = models
            services[name] = service
        return services[name]

    return load


@contextmanager
def mock_sdk_services(*args, **kwargs):
    importer = MagicMock(*args, **kwargs)
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(server, "_get_service_module", sdk_service_loader(importer, monkeypatch))
        yield importer
