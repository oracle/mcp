"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Explicit catalog doubles for behavior tests outside the resolution boundary.

Only identities declared by an individual test are added. Production catalog
validation tests use the installed resource and never install this fixture.
"""

import inspect
from types import MappingProxyType

from oracle.oci_cloud_mcp_server import server
from oracle.oci_cloud_mcp_server.sdk_catalog import ClientEntry, ModelEntry, OperationEntry, SdkCatalog, SdkResolutionError


def install_catalog(monkeypatch, *, clients=None, models=None, schemas=None):
    """Install explicitly named doubles; schemas map model FQNs to field types."""
    clients, models, schemas = clients or {}, models or {}, schemas or {}
    original = server._catalog
    client_entries, model_entries = dict(original.clients), dict(original.models)
    client_aliases, model_aliases = dict(original._client_aliases), dict(original._model_aliases)
    model_by_class = {}
    for identity, client_class in clients.items():
        service, _, name = identity.rpartition(".")
        canonical = f"{client_class.__module__}.{client_class.__name__}"
        aliases = tuple(sorted({identity, canonical}))
        operations = {
            method: OperationEntry(method, (inspect.getdoc(member) or "").partition("\n")[0])
            for method, member in inspect.getmembers(client_class, inspect.isfunction)
            if not method.startswith("_")
        }
        client_entries[identity] = ClientEntry(
            identity, client_class.__module__, name, service, aliases, MappingProxyType(operations),
        )
        client_aliases.update({alias: identity for alias in aliases})
    for identity, model_class in models.items():
        service, separator, name = identity.partition(".models.")
        if not separator or "." in name:
            raise ValueError("Fixture models must use an exported service.models.Class identity")
        schema = schemas.get(identity, getattr(model_class, "swagger_types", None))
        genuine = None
        if schema is None:
            try:
                genuine = original.model_for_class(model_class)
            except SdkResolutionError:
                pass
            else:
                schema = genuine.swagger_types
        if schema is None:
            raise ValueError(f"Declare an explicit schema for fixture model {identity}")
        aliases = tuple(sorted({identity, f"{model_class.__module__}.{model_class.__name__}"}))
        bases = tuple(sorted(
            fqn for fqn, candidate in models.items() if candidate in model_class.__bases__
        ))
        entry = ModelEntry(
            identity, model_class.__module__, name, service, aliases, bases,
            MappingProxyType(dict(schema)),
            MappingProxyType(dict(genuine.attribute_map if genuine else getattr(
                model_class, "attribute_map", {key: key for key in schema},
            ))),
            frozenset(),
        )
        model_entries[identity] = entry
        model_aliases.update({alias: identity for alias in aliases})
        model_by_class[model_class] = entry
    catalog = SdkCatalog(client_entries, model_entries, client_aliases, model_aliases)
    monkeypatch.setattr(catalog, "load_client", lambda entry: (
        clients[entry.identity] if entry.identity in clients else original.load_client(entry)
    ))
    monkeypatch.setattr(catalog, "load_model", lambda entry: (
        models[entry.identity] if entry.identity in models else original.load_model(entry)
    ))
    monkeypatch.setattr(catalog, "model_for_class", lambda cls: (
        model_by_class[cls] if cls in model_by_class else original.model_for_class(cls)
    ))
    monkeypatch.setattr(server, "_catalog", catalog)
    return catalog
