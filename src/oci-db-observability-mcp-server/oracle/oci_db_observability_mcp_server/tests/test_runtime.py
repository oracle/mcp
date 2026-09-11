"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import oci

from oracle.oci_db_observability_mcp_server import __project__, __version__
from oracle.oci_db_observability_mcp_server import runtime


EXPECTED_USER_AGENT = f"{__project__.split('oracle.', 1)[1].removesuffix('-server')}/{__version__}"


class FakeClient:
    def __init__(self, config, signer=None):
        self.config = config
        self.signer = signer


@pytest.mark.parametrize("auth_type", ["api_key", "security_token", "instance_principal"])
def test_stdio_client_uses_common_auth_context_and_user_agent(monkeypatch, auth_type) -> None:
    runtime._stdio_client.cache_clear()
    signer = object()
    context = SimpleNamespace(
        auth_type=auth_type,
        config={"region": "us-phoenix-1"},
        signer=signer,
        tenancy_id="tenant",
    )
    build_context = Mock(return_value=context)
    monkeypatch.setattr(runtime, "build_auth_context", build_context)
    monkeypatch.setattr(runtime, "get_access_token", lambda: None)
    monkeypatch.setattr(runtime, "client_class", lambda _service, _client: FakeClient)

    client = runtime._client("opsi", "OperationsInsightsClient")

    build_context.assert_called_once_with()
    assert client.signer is signer
    assert client.config == {"region": "us-phoenix-1", "additional_user_agent": EXPECTED_USER_AGENT}
    assert context.auth_type == auth_type


def test_http_clients_are_caller_specific_and_not_cached(monkeypatch) -> None:
    runtime._stdio_client.cache_clear()
    first_signer, second_signer = object(), object()
    contexts = {
        "first-token": SimpleNamespace(config={"region": "us-chicago-1"}, signer=first_signer),
        "second-token": SimpleNamespace(config={"region": "us-chicago-1"}, signer=second_signer),
    }
    calls: list[str] = []

    def context_for(token: str):
        calls.append(token)
        return contexts[token]

    tokens = iter([SimpleNamespace(token="first-token"), SimpleNamespace(token="second-token")])
    monkeypatch.setattr(runtime, "_http_auth", SimpleNamespace(context_for=context_for))
    monkeypatch.setattr(runtime, "get_access_token", lambda: next(tokens))
    monkeypatch.setattr(runtime, "build_auth_context", lambda: pytest.fail("HTTP must not use stdio credentials"))
    monkeypatch.setattr(runtime, "client_class", lambda _service, _client: FakeClient)

    first = runtime._client("opsi", "OperationsInsightsClient")
    second = runtime._client("opsi", "OperationsInsightsClient")

    assert calls == ["first-token", "second-token"]
    assert first is not second
    assert first.signer is first_signer
    assert second.signer is second_signer
    assert first.config["additional_user_agent"] == EXPECTED_USER_AGENT
    assert second.config["additional_user_agent"] == EXPECTED_USER_AGENT


def test_http_access_token_requires_initialized_policy(monkeypatch) -> None:
    monkeypatch.setattr(runtime, "_http_auth", None)

    with pytest.raises(RuntimeError, match="policy has not been initialized"):
        runtime._get_config_and_signer(SimpleNamespace(token="caller-token"))


def test_identity_bootstrap_uses_http_context(monkeypatch) -> None:
    signer = object()
    monkeypatch.setattr(
        runtime,
        "_http_auth",
        SimpleNamespace(context_for=lambda token: SimpleNamespace(config={"region": "us-ashburn-1"}, signer=signer)),
    )
    monkeypatch.setattr(runtime, "get_access_token", lambda: SimpleNamespace(token="caller-token"))
    monkeypatch.setattr(runtime, "client_class", lambda _service, _client: FakeClient)

    client = runtime.identity_bootstrap_client()

    assert isinstance(client, FakeClient)
    assert client.signer is signer


def test_invoke_validates_before_creating_sdk_client(monkeypatch) -> None:
    tool = {
        "name": "example_tool",
        "service": "opsi",
        "client": "OperationsInsightsClient",
        "operation": "get_example",
        "inputSchema": {
            "type": "object",
            "properties": {"compartment_id": {"type": "string"}},
            "required": ["compartment_id"],
            "additionalProperties": False,
        },
    }
    monkeypatch.setattr(runtime, "_client", lambda *_args: pytest.fail("client must not be created"))

    with pytest.raises(ValueError, match="example_tool requires compartment_id"):
        runtime.invoke_registered_tool(tool, {})


def test_invoke_rejects_an_inaccessible_compartment_before_creating_service_client(monkeypatch) -> None:
    tool = {
        "name": "example_tool",
        "service": "opsi",
        "client": "OperationsInsightsClient",
        "operation": "get_example",
        "inputSchema": {
            "type": "object",
            "properties": {"compartment_id": {"type": "string"}},
            "required": ["compartment_id"],
            "additionalProperties": False,
        },
    }

    class IdentityClient:
        def get_compartment(self, **_kwargs):
            raise oci.exceptions.ServiceError(404, "NotAuthorizedOrNotFound", {}, "not found")

    monkeypatch.setattr(runtime, "identity_bootstrap_client", IdentityClient)
    monkeypatch.setattr(runtime, "_client", lambda *_args: pytest.fail("service client must not be created"))

    with pytest.raises(ValueError, match="invalid or inaccessible"):
        runtime.invoke_registered_tool(tool, {"compartment_id": "ocid1.compartment.oc1..unknown"})


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [
        ("list_database_insights", {"bogus": 1}),
        ("list_database_insights", {"database_id": ["ocid1.database.oc1..example", 7]}),
    ],
)
def test_registered_tool_rejects_invalid_sdk_schema_arguments_before_client_creation(monkeypatch, tool_name, arguments) -> None:
    from oracle.oci_db_observability_mcp_server.registry import load_registry

    monkeypatch.setattr(runtime, "_client", lambda *_args: pytest.fail("client must not be created"))

    with pytest.raises(ValueError, match="Invalid arguments"):
        runtime.invoke_registered_tool(load_registry().get_tool(tool_name), arguments)


def test_response_serialization_and_model_helpers(monkeypatch) -> None:
    assert runtime.serialize_response(SimpleNamespace(data={"value": "ok"}, headers={"opc-next-page": "page-2"})) == {
        "data": {"value": "ok"},
        "nextPage": "page-2",
    }
    monkeypatch.setattr(runtime.oci.util, "to_dict", lambda _data: (_ for _ in ()).throw(TypeError("bad data")))
    assert runtime.serialize_response(SimpleNamespace(data="fallback", headers={})) == {
        "data": "fallback",
        "nextPage": None,
    }
    assert runtime._type_name("ExampleDetails") == "ExampleDetails"
    assert runtime._type_name(int) == "int"
    assert runtime._type_name(object()) is None

    class Details:
        swagger_types = {"child": "ChildDetails"}

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class ChildDetails:
        swagger_types = {}

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    models = SimpleNamespace(Details=Details, ChildDetails=ChildDetails)
    monkeypatch.setattr(runtime.oci.util, "from_dict", lambda model, payload: (model, payload), raising=False)
    assert runtime._coerce({"child": {"name": "child"}}, "Details", models) == (
        Details,
        {"child": (ChildDetails, {"name": "child"})},
    )
    monkeypatch.setattr(runtime.oci.util, "from_dict", lambda *_args: (_ for _ in ()).throw(ValueError("use constructor")))
    assert runtime._coerce({"name": "details"}, "Details", models).kwargs == {"name": "details"}
    assert runtime._coerce({"name": "unchanged"}, "Missing", models) == {"name": "unchanged"}


def test_coerce_arguments_uses_sdk_doc_types_for_generated_kwargs(monkeypatch) -> None:
    class Details:
        swagger_types = {"name": "str"}

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class Client:
        def create_example(self, **kwargs):
            """:param ExampleDetails details: (required) Request details."""
            return kwargs

    monkeypatch.setattr(runtime, "_models_module", lambda _client: SimpleNamespace(ExampleDetails=Details))
    result = runtime._coerce_arguments(Client(), "create_example", {"details": {"name": "example"}})

    assert isinstance(result["details"], Details)
    assert result["details"].kwargs == {"name": "example"}


def test_registered_tool_coerces_arguments_serializes_and_wraps_oci_errors(monkeypatch) -> None:
    tool = {
        "name": "example_tool",
        "service": "opsi",
        "client": "OperationsInsightsClient",
        "operation": "get_example",
        "inputSchema": {"type": "object", "properties": {"value": {"type": "string"}}, "additionalProperties": False},
    }

    class Client:
        def get_example(self, value: str):
            return SimpleNamespace(data={"value": value}, headers={})

    monkeypatch.setattr(runtime, "_client", lambda *_args: Client())
    assert runtime.invoke_registered_tool(tool, {"value": "ok"}) == {
        "data": {"value": "ok"},
        "nextPage": None,
    }
    with pytest.raises(ValueError, match="arguments must be a JSON object"):
        runtime.invoke_registered_tool(tool, [])

    class FailingClient:
        def get_example(self, value: str):
            raise RuntimeError("SDK failure")

    monkeypatch.setattr(runtime, "_client", lambda *_args: FailingClient())
    with pytest.raises(RuntimeError, match="OCI operation example_tool failed: SDK failure"):
        runtime.invoke_registered_tool(tool, {"value": "ok"})


def test_metric_catalog_tools_are_local_and_validate_arguments(monkeypatch) -> None:
    from oracle.oci_db_observability_mcp_server.registry import load_registry

    monkeypatch.setattr(runtime, "_client", lambda *_args: pytest.fail("metadata tools must not create an OCI client"))
    registry = load_registry()

    result = runtime.invoke_registered_tool(
        registry.get_tool("search_database_and_infra_observability_metrics"),
        {"keywords": "apply lag", "namespace": "oracle_oci_database"},
    )

    assert result["catalogId"] == "database-and-infra-observability-metrics"
    assert any(item["record"]["name"] == "ApplyLag" for item in result["items"])
    assert json.loads(json.dumps(result)) == result
    with pytest.raises(ValueError, match="Invalid arguments"):
        runtime.invoke_registered_tool(registry.get_tool("get_database_and_infra_observability_metrics"), {"keys": []})


def test_metric_read_builds_one_monitoring_request_from_catalog(monkeypatch) -> None:
    from oracle.oci_db_observability_mcp_server.registry import load_registry

    captured: dict[str, object] = {}

    class Details:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class Client:
        def summarize_metrics_data(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                data=[
                    {"stream": 1, "aggregated_datapoints": [{"value": 1}, {"value": 2}]},
                    {"stream": 2, "aggregated_datapoints": [{"value": 3}]},
                ],
                headers={},
            )

    monkeypatch.setattr(runtime, "_client", lambda *_args: Client())
    monkeypatch.setattr(
        runtime,
        "identity_bootstrap_client",
        lambda: SimpleNamespace(get_compartment=lambda **_kwargs: None),
    )
    monkeypatch.setattr(runtime.oci.monitoring, "models", SimpleNamespace(SummarizeMetricsDataDetails=Details))
    tool = load_registry().get_tool("read_database_and_infra_observability_metrics")

    result = runtime.invoke_registered_tool(
        tool,
        {
            "compartment_id": "ocid1.compartment.oc1..example",
            "namespace": "oracle_oci_database",
            "metric_name": "ApplyLag",
            "dimension_filters": {"dbRole": "PHYSICAL_STANDBY"},
            "group_by": "primaryDbid",
            "aggregation": "mean",
            "interval": "5m",
            "resolution": "1m",
            "start_time": "2026-08-01T00:00:00Z",
            "end_time": "2026-08-01T01:00:00Z",
            "max_results": 1,
        },
    )

    assert captured["compartment_id"] == "ocid1.compartment.oc1..example"
    assert captured["summarize_metrics_data_details"].kwargs["query"] == 'ApplyLag[5m]{dbRole = "PHYSICAL_STANDBY"}.groupBy(primaryDbid).mean()'
    assert result["data"] == [{"stream": 1, "aggregated_datapoints": [{"value": 1}]}]
    assert result["mql"] == 'ApplyLag[5m]{dbRole = "PHYSICAL_STANDBY"}.groupBy(primaryDbid).mean()'


@pytest.mark.parametrize(
    "arguments, error",
    [
        ({"dimension_filters": {"notCataloged": "value"}}, "Unsupported dimensions"),
        ({"start_time": "2026-08-01T01:00:00Z", "end_time": "2026-08-01T00:00:00Z"}, "start_time must be earlier"),
        ({"interval": "1m", "resolution": "5m"}, "resolution must not exceed interval"),
    ],
)
def test_metric_read_rejects_invalid_catalog_or_time_before_client_creation(monkeypatch, arguments, error) -> None:
    from oracle.oci_db_observability_mcp_server.registry import load_registry

    base_arguments = {
        "compartment_id": "ocid1.compartment.oc1..example",
        "namespace": "oracle_oci_database",
        "metric_name": "ApplyLag",
        "aggregation": "mean",
        "interval": "5m",
        "resolution": "1m",
        "start_time": "2026-08-01T00:00:00Z",
        "end_time": "2026-08-01T01:00:00Z",
    }
    base_arguments.update(arguments)
    monkeypatch.setattr(runtime, "_client", lambda *_args: pytest.fail("invalid metric read must not create an OCI client"))
    monkeypatch.setattr(
        runtime,
        "identity_bootstrap_client",
        lambda: SimpleNamespace(get_compartment=lambda **_kwargs: None),
    )

    with pytest.raises(ValueError, match=error):
        runtime.invoke_registered_tool(load_registry().get_tool("read_database_and_infra_observability_metrics"), base_arguments)


@pytest.mark.parametrize(("interval", "resolution"), [("60m", "60m"), ("1d", "1d")])
def test_metric_read_schema_accepts_documented_duration_boundaries(interval, resolution) -> None:
    from jsonschema import Draft202012Validator
    from oracle.oci_db_observability_mcp_server.registry import load_registry

    schema = load_registry().get_tool("read_database_and_infra_observability_metrics")["inputSchema"]
    arguments = {
        "compartment_id": "ocid1.compartment.oc1..example",
        "namespace": "oracle_oci_database",
        "metric_name": "ApplyLag",
        "aggregation": "mean",
        "interval": interval,
        "resolution": resolution,
        "start_time": "2026-08-01T00:00:00Z",
        "end_time": "2026-08-01T01:00:00Z",
    }

    assert not list(Draft202012Validator(schema).iter_errors(arguments))
    arguments["interval"] = "2d"
    assert list(Draft202012Validator(schema).iter_errors(arguments))


@pytest.mark.parametrize(
    ("tool_name", "arguments", "operation"),
    [
        ("list_database_and_infra_observability_alarms", {"compartment_id": "ocid1.compartment.oc1..example", "limit": 10}, "list_alarms"),
        ("get_database_and_infra_observability_alarm", {"alarm_id": "ocid1.alarm.oc1..example"}, "get_alarm"),
        ("list_database_and_infra_observability_alarm_states", {"compartment_id": "ocid1.compartment.oc1..example", "status": "FIRING"}, "list_alarms_status"),
    ],
)
def test_alarm_tools_each_make_one_pinned_sdk_operation(monkeypatch, tool_name, arguments, operation) -> None:
    from oracle.oci_db_observability_mcp_server.registry import load_registry

    calls: list[tuple[str, dict[str, object]]] = []

    class Client:
        def __getattr__(self, name):
            def invoke(**kwargs):
                calls.append((name, kwargs))
                return SimpleNamespace(data={"operation": name}, headers={})

            return invoke

    monkeypatch.setattr(runtime, "_client", lambda *_args: Client())
    monkeypatch.setattr(
        runtime,
        "identity_bootstrap_client",
        lambda: SimpleNamespace(get_compartment=lambda **_kwargs: None),
    )

    result = runtime.invoke_registered_tool(load_registry().get_tool(tool_name), arguments)

    assert calls == [(operation, arguments)]
    assert result == {"data": {"operation": operation}, "nextPage": None}
