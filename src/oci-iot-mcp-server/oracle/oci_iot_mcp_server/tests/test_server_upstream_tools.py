import builtins
import io
from types import SimpleNamespace

import httpx
import pytest
from fastmcp import Client
from oci.exceptions import ConfigFileNotFound, InvalidConfig
from oci.iot.models import (
    DigitalTwinAdapterInboundEnvelope,
    DigitalTwinAdapterInboundRoute,
    DigitalTwinAdapterJsonPayload,
)

from oracle.oci_iot_mcp_server import server


def _detail_factory(kind: str):
    def factory(**kwargs):
        return SimpleNamespace(kind=kind, **kwargs)

    return factory


def _response(*, status: int = 202, request_id: str = "req-123", headers: dict | None = None, data=None):
    return SimpleNamespace(status=status, request_id=request_id, headers=headers or {}, data=data)


def _simple_model(identifier: str, **kwargs):
    return SimpleNamespace(id=identifier, **kwargs)


def _fake_upstream_adapter_envelope():
    return DigitalTwinAdapterInboundEnvelope(
        reference_endpoint="/telemetry",
        reference_payload=DigitalTwinAdapterJsonPayload(data_format="JSON"),
        envelope_mapping={"type": "messageType"},
    )


def _fake_upstream_adapter_route():
    return DigitalTwinAdapterInboundRoute(
        condition="true",
        payload_mapping={"temperature": "temp"},
    )


def _fake_upstream_adapter():
    return SimpleNamespace(
        id="ocid1.digitaltwinadapter.oc1..ffff",
        inbound_envelope=_fake_upstream_adapter_envelope(),
        inbound_routes=[_fake_upstream_adapter_route()],
    )


def test_tool_decorator_registers_tool_and_returns_original_function(monkeypatch):
    registered = []

    def fake_tool(*, description):
        def registrar(func):
            registered.append((description, func.__name__))

        return registrar

    monkeypatch.setattr(server.mcp, "tool", fake_tool)

    @server.tool(description="sample description")
    def sample_tool():
        return "ok"

    assert sample_tool() == "ok"
    assert registered == [("sample description", "sample_tool")]


def test_json_and_response_helpers_cover_normalization_and_error_paths(monkeypatch):
    logged = []
    monkeypatch.setattr(server.logger, "error", lambda message: logged.append(message))

    assert server._normalize_items(SimpleNamespace(items=("a", "b"))) == ["a", "b"]
    assert server._normalize_items(("x", "y")) == ["x", "y"]
    assert server._normalize_items(None) == []
    assert server._normalize_items("value") == ["value"]

    assert server._parse_json_input('{"answer": 42}', "payload") == {"answer": 42}
    with pytest.raises(ValueError, match="Invalid JSON for payload"):
        server._parse_json_input("{bad json", "payload")
    assert logged and logged[0].startswith("Invalid JSON for payload:")

    response = SimpleNamespace(status=201, request_id=None, headers={"opc-request-id": "req-1"}, data={"id": "x"})
    assert server._response_to_dict(response) == {
        "status": 201,
        "request_id": "req-1",
        "headers": {"opc-request-id": "req-1"},
        "data": {"id": "x"},
    }
    assert server._result_payload([{"id": "x"}]) == {"result": [{"id": "x"}]}


def test_get_identity_client_for_profile_builds_security_token_client(monkeypatch):
    server._get_identity_client_for_profile.cache_clear()
    config = {
        "key_file": "/tmp/key.pem",
        "security_token_file": "/tmp/security.token",
        "tenancy": "ocid1.tenancy.oc1..aaaa",
    }

    monkeypatch.setattr(server.oci.config, "from_file", lambda profile_name: dict(config))
    monkeypatch.setattr(server.os.path, "exists", lambda path: path == "/tmp/security.token")
    monkeypatch.setattr(
        server.oci.signer,
        "load_private_key_from_file",
        lambda path, pass_phrase=None: f"key:{path}",
    )
    monkeypatch.setattr(
        builtins,
        "open",
        lambda path, mode="r": io.StringIO("token-123"),
    )
    monkeypatch.setattr(
        server.oci.auth.signers,
        "SecurityTokenSigner",
        lambda token, private_key: {"token": token, "private_key": private_key},
    )
    monkeypatch.setattr(
        server.oci.identity,
        "IdentityClient",
        lambda cfg, signer=None: {"config": cfg, "signer": signer},
    )

    client, tenancy_id = server._get_identity_client_for_profile("ALT")

    assert tenancy_id == "ocid1.tenancy.oc1..aaaa"
    assert client["signer"] == {"token": "token-123", "private_key": "key:/tmp/key.pem"}
    assert client["config"]["additional_user_agent"].endswith(f"/{server.__version__}")


def test_get_identity_client_uses_api_key_fallback_when_security_token_missing(monkeypatch):
    server._get_identity_client_for_profile.cache_clear()
    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "auto")
    monkeypatch.setattr(
        server.oci.config,
        "from_file",
        lambda profile_name: {
            "profile": profile_name,
            "key_file": "/tmp/api-key.pem",
            "tenancy": "ocid1.tenancy.oc1..bbbb",
            "user": "ocid1.user.oc1..bbbb",
            "fingerprint": "aa:bb",
            "region": "us-ashburn-1",
        },
    )
    monkeypatch.setattr(
        server.oci.signer,
        "Signer",
        lambda **kwargs: {"kind": "api_key", "kwargs": kwargs},
    )
    monkeypatch.setattr(
        server.oci.identity,
        "IdentityClient",
        lambda cfg, signer=None: {"config": cfg, "signer": signer},
    )

    client, tenancy_id = server.get_identity_client("ALT")

    assert tenancy_id == "ocid1.tenancy.oc1..bbbb"
    assert client["signer"]["kind"] == "api_key"
    assert client["config"]["additional_user_agent"].endswith(f"/{server.__version__}")


def test_get_identity_client_uses_instance_principal_tenancy(monkeypatch):
    server._get_identity_client_for_profile.cache_clear()
    signer = SimpleNamespace(
        kind="instance_principal",
        tenancy_id="ocid1.tenancy.oc1..cccc",
        region="us-phoenix-1",
    )

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "instance_principal")
    monkeypatch.setattr(
        server.oci.auth.signers,
        "InstancePrincipalsSecurityTokenSigner",
        lambda: signer,
    )
    monkeypatch.setattr(
        server.oci.identity,
        "IdentityClient",
        lambda cfg, signer=None: {"config": cfg, "signer": signer},
    )

    client, tenancy_id = server.get_identity_client("ALT")

    assert tenancy_id == "ocid1.tenancy.oc1..cccc"
    assert client["signer"] is signer
    assert client["config"]["region"] == "us-phoenix-1"


def test_get_identity_client_uses_resource_principal_tenancy(monkeypatch):
    server._get_identity_client_for_profile.cache_clear()
    signer = SimpleNamespace(
        kind="resource_principal",
        tenancy_id="ocid1.tenancy.oc1..dddd",
        region="us-chicago-1",
    )

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "resource_principal")
    monkeypatch.setattr(
        server.oci.auth.signers,
        "get_resource_principals_signer",
        lambda: signer,
    )
    monkeypatch.setattr(
        server.oci.identity,
        "IdentityClient",
        lambda cfg, signer=None: {"config": cfg, "signer": signer},
    )

    client, tenancy_id = server.get_identity_client("ALT")

    assert tenancy_id == "ocid1.tenancy.oc1..dddd"
    assert client["signer"] is signer
    assert client["config"]["region"] == "us-chicago-1"


def test_create_digital_twin_adapter_serializes_nested_adapter(monkeypatch):
    def fake_create(**kwargs):
        return SimpleNamespace(data=_fake_upstream_adapter())

    monkeypatch.setattr(
        server,
        "get_iot_client",
        lambda: SimpleNamespace(create_digital_twin_adapter=fake_create),
    )

    result = server.create_digital_twin_adapter(
        iot_domain_id="domain-1",
        display_name="Adapter 1",
        digital_twin_model_id="model-1",
    )

    assert isinstance(result["inbound_envelope"], dict)
    assert isinstance(result["inbound_routes"], list)
    server.JSON_ADAPTER.dump_python(result, mode="json")


def test_get_identity_client_uses_instance_principal_delegation_tenancy(monkeypatch):
    server._get_identity_client_for_profile.cache_clear()
    signer = SimpleNamespace(
        kind="instance_principal_delegation",
        tenancy_id="ocid1.tenancy.oc1..delegated1",
        region="us-ashburn-1",
    )

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "instance_principal_delegation")
    monkeypatch.setenv("OCI_IOT_DELEGATION_TOKEN", "delegation-token-123")
    monkeypatch.setattr(
        server.oci.auth.signers,
        "InstancePrincipalsDelegationTokenSigner",
        lambda **kwargs: signer,
    )
    monkeypatch.setattr(
        server.oci.identity,
        "IdentityClient",
        lambda cfg, signer=None: {"config": cfg, "signer": signer},
    )

    client, tenancy_id = server.get_identity_client("ALT")

    assert tenancy_id == "ocid1.tenancy.oc1..delegated1"
    assert client["signer"] is signer
    assert client["config"]["region"] == "us-ashburn-1"


def test_get_identity_client_uses_resource_principal_delegation_tenancy(monkeypatch):
    server._get_identity_client_for_profile.cache_clear()
    signer = SimpleNamespace(
        kind="resource_principal_delegation",
        tenancy_id="ocid1.tenancy.oc1..delegated2",
        region="us-sanjose-1",
    )

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "resource_principal_delegation")
    monkeypatch.setenv("OCI_IOT_DELEGATION_TOKEN", "delegation-token-456")
    monkeypatch.setattr(
        server.oci.auth.signers,
        "get_resource_principal_delegation_token_signer",
        lambda delegation_token, resource_principal_token_path_provider=None: signer,
    )
    monkeypatch.setattr(
        server.oci.identity,
        "IdentityClient",
        lambda cfg, signer=None: {"config": cfg, "signer": signer},
    )

    client, tenancy_id = server.get_identity_client("ALT")

    assert tenancy_id == "ocid1.tenancy.oc1..delegated2"
    assert client["signer"] is signer
    assert client["config"]["region"] == "us-sanjose-1"


def test_get_identity_client_uses_oke_workload_identity_tenancy_override(monkeypatch):
    server._get_identity_client_for_profile.cache_clear()
    signer = SimpleNamespace(
        kind="oke_workload_identity",
        region="us-phoenix-1",
    )

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "oke_workload_identity")
    monkeypatch.setenv("OCI_IOT_TENANCY_ID_OVERRIDE", "ocid1.tenancy.oc1..override")
    monkeypatch.setattr(
        server.oci.auth.signers,
        "get_oke_workload_identity_resource_principal_signer",
        lambda service_account_token_path=None, service_account_token=None, **kwargs: signer,
    )
    monkeypatch.setattr(
        server.oci.identity,
        "IdentityClient",
        lambda cfg, signer=None: {"config": cfg, "signer": signer},
    )

    client, tenancy_id = server.get_identity_client("ALT")

    assert tenancy_id == "ocid1.tenancy.oc1..override"
    assert client["signer"] is signer
    assert client["config"]["region"] == "us-phoenix-1"


def test_get_identity_client_rejects_oke_workload_identity_without_tenancy_override(monkeypatch):
    server._get_identity_client_for_profile.cache_clear()
    signer = SimpleNamespace(
        kind="oke_workload_identity",
        region="us-phoenix-1",
    )

    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "oke_workload_identity")
    monkeypatch.delenv("OCI_IOT_TENANCY_ID_OVERRIDE", raising=False)
    monkeypatch.setattr(
        server.oci.auth.signers,
        "get_oke_workload_identity_resource_principal_signer",
        lambda service_account_token_path=None, service_account_token=None, **kwargs: signer,
    )
    monkeypatch.setattr(
        server.oci.identity,
        "IdentityClient",
        lambda cfg, signer=None: {"config": cfg, "signer": signer},
    )

    with pytest.raises(ValueError, match="tenancy"):
        server.get_identity_client("ALT")


def test_get_identity_client_uses_default_profile_from_env(monkeypatch):
    monkeypatch.setenv("OCI_CONFIG_PROFILE", "ALT")
    monkeypatch.setattr(
        server,
        "_get_identity_client_for_profile",
        lambda profile_name, auth_type=None: ("client", profile_name),
    )

    assert server.get_identity_client() == ("client", "ALT")


@pytest.mark.parametrize(
    ("exception", "prefix"),
    [
        (ConfigFileNotFound("missing config"), "OCI config file not found:"),
        (InvalidConfig("bad config"), "Invalid OCI configuration:"),
        (RuntimeError("boom"), "Error creating Identity client:"),
    ],
)
def test_get_identity_client_logs_and_reraises_known_errors(monkeypatch, exception, prefix):
    logged = []
    monkeypatch.setattr(server.logger, "error", lambda message: logged.append(message))
    monkeypatch.setattr(
        server,
        "_get_identity_client_for_profile",
        lambda profile_name, auth_type=None: (_ for _ in ()).throw(exception),
    )

    with pytest.raises(type(exception)):
        server.get_identity_client("ALT")

    assert logged == [f"{prefix} {exception}"]


def test_oci_config_token_query_and_url_helpers_cover_success_and_failure_paths(monkeypatch):
    monkeypatch.setenv("OCI_CONFIG_PROFILE", "DEFAULT")
    monkeypatch.setattr(
        server.oci.config,
        "from_file",
        lambda profile_name: {"profile": profile_name, "region": "us-ashburn-1"},
    )

    assert server._get_oci_config() == {"profile": "DEFAULT", "region": "us-ashburn-1"}
    assert server._get_oci_config("ALT") == {"profile": "ALT", "region": "us-ashburn-1"}

    monkeypatch.setenv("OCI_IOT_DATA_API_ACCESS_TOKEN", "env-token")
    assert server._get_iot_data_api_access_token() == "env-token"
    assert server._get_iot_data_api_access_token("explicit-token") == "explicit-token"
    monkeypatch.delenv("OCI_IOT_DATA_API_ACCESS_TOKEN")
    with pytest.raises(ValueError, match="IoT Data API access token is required"):
        server._get_iot_data_api_access_token()

    normalized = server._normalize_query_params(
        '{"limit": 5, "enabled": true, "payload": {"x": 1}, "ids": ["a"], "skip": null}'
    )
    assert normalized == {
        "limit": 5,
        "enabled": "true",
        "payload": '{"x": 1}',
        "ids": '["a"]',
    }
    assert server._normalize_query_params(None) == {}
    with pytest.raises(ValueError, match="query_params must be a dictionary"):
        server._normalize_query_params("[]")

    monkeypatch.setattr(server, "_get_oci_config", lambda profile_name=None: {"region": "us-phoenix-1"})
    assert server._build_iot_data_api_url("group-short", "domain-short", "/rawData") == (
        "https://group-short.data.iot.us-phoenix-1.oci.oraclecloud.com/ords/domain-short/rawData"
    )
    assert server._build_iot_data_api_url("group-short", "domain-short", "/rawData", region="eu-frankfurt-1") == (
        "https://group-short.data.iot.eu-frankfurt-1.oci.oraclecloud.com/ords/domain-short/rawData"
    )


def test_build_iot_data_api_url_uses_principal_region_default(monkeypatch):
    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "instance_principal")
    monkeypatch.setattr(server, "get_default_region", lambda profile_name=None, auth_type=None: "us-phoenix-1")

    assert server._build_iot_data_api_url("group-short", "domain-short", "/rawData") == (
        "https://group-short.data.iot.us-phoenix-1.oci.oraclecloud.com/ords/domain-short/rawData"
    )


def test_build_iot_data_api_url_uses_oke_region_default(monkeypatch):
    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "oke_workload_identity")
    monkeypatch.setattr(server, "get_default_region", lambda profile_name=None, auth_type=None: "us-sanjose-1")

    assert server._build_iot_data_api_url("group-short", "domain-short", "/rawData") == (
        "https://group-short.data.iot.us-sanjose-1.oci.oraclecloud.com/ords/domain-short/rawData"
    )


def test_call_iot_data_api_handles_json_text_and_structured_errors(monkeypatch):
    captured = {}
    monkeypatch.setattr(server, "_get_iot_data_api_access_token", lambda access_token=None: "token-123")
    monkeypatch.setattr(
        server,
        "_build_iot_data_api_url",
        lambda **kwargs: "https://example.com/ords/domain-short/rawData",
    )

    def fake_get(url, *, headers, timeout):
        captured["url"] = url
        captured["headers"] = {key.lower(): value for key, value in headers.items()}
        captured["timeout"] = timeout
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={"items": [1]},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(server.httpx, "get", fake_get)

    result = server._call_iot_data_api(
        resource_path="/rawData",
        iot_domain_group_short_id="group-short",
        iot_domain_short_id="domain-short",
        query_params={"limit": 5, "enabled": True},
        opc_request_id="opc-1",
    )

    assert result == {"items": [1]}
    assert captured["url"].endswith("rawData?limit=5&enabled=true")
    assert captured["headers"]["authorization"] == "Bearer token-123"
    assert captured["headers"]["accept"] == "application/json"
    assert captured["headers"]["opc-request-id"] == "opc-1"
    assert captured["timeout"] == 30.0

    monkeypatch.setattr(
        server.httpx,
        "get",
        lambda url, *, headers, timeout: httpx.Response(
            200,
            headers={"Content-Type": "text/plain"},
            text="plain text",
            request=httpx.Request("GET", url),
        ),
    )
    assert server._call_iot_data_api(
        resource_path="/rawData",
        iot_domain_group_short_id="group-short",
        iot_domain_short_id="domain-short",
    ) == "plain text"

    logged = []
    monkeypatch.setattr(server.logger, "error", lambda message: logged.append(message))
    request = httpx.Request("GET", "https://example.com/ords/domain-short/rawData")
    response = httpx.Response(
        500,
        headers={"Content-Type": "application/json"},
        json={"message": "bad"},
        request=request,
    )
    monkeypatch.setattr(
        server.httpx,
        "get",
        lambda url, *, headers, timeout: (_ for _ in ()).throw(
            httpx.HTTPStatusError("boom", request=request, response=response)
        ),
    )

    result = server._call_iot_data_api(
        resource_path="/rawData",
        iot_domain_group_short_id="group-short",
        iot_domain_short_id="domain-short",
    )
    assert result["ok"] is False
    assert result["error"]["code"] == "data_plane_http_error"
    assert result["error"]["details"]["status_code"] == 500
    assert logged and "IoT Data API request failed" in logged[0]

    monkeypatch.setattr(
        server.httpx,
        "get",
        lambda url, *, headers, timeout: (_ for _ in ()).throw(httpx.TimeoutException("slow")),
    )
    result = server._call_iot_data_api(
        resource_path="/rawData",
        iot_domain_group_short_id="group-short",
        iot_domain_short_id="domain-short",
    )
    assert result["ok"] is False
    assert result["error"]["code"] == "data_plane_timeout"

    monkeypatch.setattr(
        server.httpx,
        "get",
        lambda url, *, headers, timeout: (_ for _ in ()).throw(
            httpx.RequestError("network down", request=httpx.Request("GET", url))
        ),
    )
    result = server._call_iot_data_api(
        resource_path="/rawData",
        iot_domain_group_short_id="group-short",
        iot_domain_short_id="domain-short",
    )
    assert result["ok"] is False
    assert result["error"]["code"] == "data_plane_request_error"


@pytest.mark.parametrize(
    ("request_data_format", "request_data", "constructor_name", "expected_request_data"),
    [
        ("JSON", '{"enabled": true}', "InvokeRawJsonCommandDetails", {"enabled": True}),
        ("TEXT", "PING", "InvokeRawTextCommandDetails", "PING"),
        ("BINARY", "QUJD", "InvokeRawBinaryCommandDetails", "QUJD"),
    ],
)
def test_build_direct_invoke_raw_command_details_supports_all_formats(
    monkeypatch,
    request_data_format,
    request_data,
    constructor_name,
    expected_request_data,
):
    monkeypatch.setattr(server.oci.iot.models, constructor_name, _detail_factory(constructor_name))

    details = server._build_direct_invoke_raw_command_details(
        request_data_format=request_data_format,
        request_endpoint="/v1/cmd",
        response_endpoint="/v1/reply",
        request_duration="PT1S",
        response_duration="PT2S",
        request_data_content_type="application/json",
        request_data=request_data,
    )

    assert details.kind == constructor_name
    assert details.request_endpoint == "/v1/cmd"
    assert details.response_endpoint == "/v1/reply"
    assert details.request_duration == "PT1S"
    assert details.response_duration == "PT2S"
    assert details.request_data_content_type == "application/json"
    assert details.request_data == expected_request_data


def test_build_direct_invoke_raw_command_details_rejects_unknown_format():
    with pytest.raises(ValueError, match="request_data_format must be one of"):
        server._build_direct_invoke_raw_command_details(
            request_data_format="XML",
            request_endpoint="/v1/cmd",
        )


def test_get_digital_twin_instance_content_metadata_path_calls_client(monkeypatch):
    captured = {}

    def get_content(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            data={
                "content": {"temperature": 73},
                "metadata": {"x": 1, "status": "ok"},
            }
        )

    monkeypatch.setattr(server, "get_iot_client", lambda: SimpleNamespace(get_digital_twin_instance_content=get_content))

    result = server.get_digital_twin_instance_content(
        "twin-1",
        should_include_metadata=True,
        opc_request_id="opc-1",
    )

    assert result == {
        "content": {"temperature": 73},
        "metadata": {"x": 1, "status": "ok"},
    }
    assert captured == {
        "digital_twin_instance_id": "twin-1",
        "should_include_metadata": True,
        "opc_request_id": "opc-1",
    }
    assert server.JSON_ADAPTER.dump_python(result, mode="json") == {
        "content": {"temperature": 73},
        "metadata": {"x": 1, "status": "ok"},
    }


def test_health_check_reports_healthy_service():
    assert server.health_check() == {
        "status": "healthy",
        "service": "oci-iot-mcp-server",
        "version": server.__version__,
    }


MODEL_TOOL_CASES = [
    {
        "tool_name": "create_digital_twin_model",
        "constructor_name": "CreateDigitalTwinModelDetails",
        "client_method": "create_digital_twin_model",
        "details_arg": "create_digital_twin_model_details",
        "call_kwargs": {
            "iot_domain_id": "domain-1",
            "display_name": "Model 1",
            "spec": '{"contents": []}',
            "description": "desc",
            "freeform_tags": '{"env": "dev"}',
            "defined_tags": '{"ops": {"cost": "1"}}',
            "opc_retry_token": "retry-1",
            "opc_request_id": "req-1",
        },
        "expected_details": {
            "iot_domain_id": "domain-1",
            "display_name": "Model 1",
            "description": "desc",
            "spec": {"contents": []},
            "freeform_tags": {"env": "dev"},
            "defined_tags": {"ops": {"cost": "1"}},
        },
        "expected_client_kwargs": {"opc_retry_token": "retry-1", "opc_request_id": "req-1"},
        "response_model": _simple_model("model-1", display_name="Model 1"),
    },
    {
        "tool_name": "create_digital_twin_adapter",
        "constructor_name": "CreateDigitalTwinAdapterDetails",
        "client_method": "create_digital_twin_adapter",
        "details_arg": "create_digital_twin_adapter_details",
        "call_kwargs": {
            "iot_domain_id": "domain-1",
            "display_name": "Adapter 1",
            "description": "desc",
            "digital_twin_model_id": "model-1",
            "inbound_envelope": '{"type": "telemetry"}',
            "inbound_routes": '[{"endpoint": "/temp"}]',
            "freeform_tags": '{"env": "dev"}',
            "defined_tags": '{"ops": {"cost": "1"}}',
            "opc_retry_token": "retry-1",
            "opc_request_id": "req-1",
        },
        "expected_details": {
            "iot_domain_id": "domain-1",
            "display_name": "Adapter 1",
            "digital_twin_model_id": "model-1",
            "inbound_envelope": {"type": "telemetry"},
            "inbound_routes": [{"endpoint": "/temp"}],
            "freeform_tags": {"env": "dev"},
            "defined_tags": {"ops": {"cost": "1"}},
        },
        "expected_client_kwargs": {"opc_retry_token": "retry-1", "opc_request_id": "req-1"},
        "response_model": _simple_model("adapter-1", display_name="Adapter 1"),
    },
    {
        "tool_name": "create_digital_twin_instance",
        "constructor_name": "CreateDigitalTwinInstanceDetails",
        "client_method": "create_digital_twin_instance",
        "details_arg": "create_digital_twin_instance_details",
        "call_kwargs": {
            "iot_domain_id": "domain-1",
            "auth_id": "auth-1",
            "external_key": "pump-01",
            "display_name": "Pump 01",
            "digital_twin_adapter_id": "adapter-1",
            "digital_twin_model_id": "model-1",
            "digital_twin_model_spec_uri": "https://example.com/models/pump.json",
            "connectivity_type": "INDIRECT",
            "gateways": ["gateway-1"],
            "freeform_tags": '{"env": "dev"}',
            "defined_tags": '{"ops": {"cost": "1"}}',
            "opc_retry_token": "retry-1",
            "opc_request_id": "req-1",
        },
        "expected_details": {
            "iot_domain_id": "domain-1",
            "auth_id": "auth-1",
            "external_key": "pump-01",
            "display_name": "Pump 01",
            "digital_twin_adapter_id": "adapter-1",
            "digital_twin_model_id": "model-1",
            "digital_twin_model_spec_uri": "https://example.com/models/pump.json",
            "connectivity_type": "INDIRECT",
            "gateways": ["gateway-1"],
            "freeform_tags": {"env": "dev"},
            "defined_tags": {"ops": {"cost": "1"}},
        },
        "expected_client_kwargs": {"opc_retry_token": "retry-1", "opc_request_id": "req-1"},
        "response_model": _simple_model(
            "twin-1",
            display_name="Pump 01",
            connectivity_type="INDIRECT",
            gateways=["gateway-1"],
        ),
    },
    {
        "tool_name": "create_digital_twin_relationship",
        "constructor_name": "CreateDigitalTwinRelationshipDetails",
        "client_method": "create_digital_twin_relationship",
        "details_arg": "create_digital_twin_relationship_details",
        "call_kwargs": {
            "iot_domain_id": "domain-1",
            "content_path": "contains",
            "source_digital_twin_instance_id": "twin-1",
            "target_digital_twin_instance_id": "twin-2",
            "display_name": "Contains",
            "content": '{"state": "active"}',
            "freeform_tags": '{"env": "dev"}',
            "defined_tags": '{"ops": {"cost": "1"}}',
            "opc_retry_token": "retry-1",
            "opc_request_id": "req-1",
        },
        "expected_details": {
            "iot_domain_id": "domain-1",
            "content_path": "contains",
            "source_digital_twin_instance_id": "twin-1",
            "target_digital_twin_instance_id": "twin-2",
            "content": {"state": "active"},
            "freeform_tags": {"env": "dev"},
            "defined_tags": {"ops": {"cost": "1"}},
        },
        "expected_client_kwargs": {"opc_retry_token": "retry-1", "opc_request_id": "req-1"},
        "response_model": _simple_model("rel-1", display_name="Contains"),
    },
    {
        "tool_name": "update_digital_twin_adapter",
        "constructor_name": "UpdateDigitalTwinAdapterDetails",
        "client_method": "update_digital_twin_adapter",
        "details_arg": "update_digital_twin_adapter_details",
        "call_kwargs": {
            "digital_twin_adapter_id": "adapter-1",
            "display_name": "Adapter 1",
            "inbound_envelope": '{"type": "telemetry"}',
            "inbound_routes": '[{"endpoint": "/temp"}]',
            "freeform_tags": '{"env": "dev"}',
            "defined_tags": '{"ops": {"cost": "1"}}',
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "expected_details": {
            "display_name": "Adapter 1",
            "inbound_envelope": {"type": "telemetry"},
            "inbound_routes": [{"endpoint": "/temp"}],
            "freeform_tags": {"env": "dev"},
            "defined_tags": {"ops": {"cost": "1"}},
        },
        "expected_client_kwargs": {
            "digital_twin_adapter_id": "adapter-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "response_model": _simple_model("adapter-1", display_name="Adapter 1"),
    },
    {
        "tool_name": "update_digital_twin_instance",
        "constructor_name": "UpdateDigitalTwinInstanceDetails",
        "client_method": "update_digital_twin_instance",
        "details_arg": "update_digital_twin_instance_details",
        "call_kwargs": {
            "digital_twin_instance_id": "twin-1",
            "auth_id": "auth-1",
            "external_key": "pump-01",
            "display_name": "Pump 01",
            "digital_twin_adapter_id": "adapter-1",
            "digital_twin_model_id": "model-1",
            "digital_twin_model_spec_uri": "https://example.com/models/pump.json",
            "gateways": ["gateway-1", "gateway-2"],
            "freeform_tags": '{"env": "dev"}',
            "defined_tags": '{"ops": {"cost": "1"}}',
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "expected_details": {
            "auth_id": "auth-1",
            "external_key": "pump-01",
            "display_name": "Pump 01",
            "digital_twin_adapter_id": "adapter-1",
            "digital_twin_model_id": "model-1",
            "digital_twin_model_spec_uri": "https://example.com/models/pump.json",
            "gateways": ["gateway-1", "gateway-2"],
            "freeform_tags": {"env": "dev"},
            "defined_tags": {"ops": {"cost": "1"}},
        },
        "expected_client_kwargs": {
            "digital_twin_instance_id": "twin-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "response_model": _simple_model(
            "twin-1",
            display_name="Pump 01",
            connectivity_type="INDIRECT",
            gateways=["gateway-1", "gateway-2"],
        ),
    },
    {
        "tool_name": "update_digital_twin_model",
        "constructor_name": "UpdateDigitalTwinModelDetails",
        "client_method": "update_digital_twin_model",
        "details_arg": "update_digital_twin_model_details",
        "call_kwargs": {
            "digital_twin_model_id": "model-1",
            "display_name": "Model 1",
            "description": "desc",
            "freeform_tags": '{"env": "dev"}',
            "defined_tags": '{"ops": {"cost": "1"}}',
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "expected_details": {
            "display_name": "Model 1",
            "description": "desc",
            "freeform_tags": {"env": "dev"},
            "defined_tags": {"ops": {"cost": "1"}},
        },
        "expected_client_kwargs": {
            "digital_twin_model_id": "model-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "response_model": _simple_model("model-1", display_name="Model 1"),
    },
    {
        "tool_name": "update_digital_twin_relationship",
        "constructor_name": "UpdateDigitalTwinRelationshipDetails",
        "client_method": "update_digital_twin_relationship",
        "details_arg": "update_digital_twin_relationship_details",
        "call_kwargs": {
            "digital_twin_relationship_id": "rel-1",
            "display_name": "Contains",
            "description": "desc",
            "content": '{"state": "active"}',
            "freeform_tags": '{"env": "dev"}',
            "defined_tags": '{"ops": {"cost": "1"}}',
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "expected_details": {
            "display_name": "Contains",
            "description": "desc",
            "content": {"state": "active"},
            "freeform_tags": {"env": "dev"},
            "defined_tags": {"ops": {"cost": "1"}},
        },
        "expected_client_kwargs": {
            "digital_twin_relationship_id": "rel-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "response_model": _simple_model("rel-1", display_name="Contains"),
    },
    {
        "tool_name": "create_iot_domain",
        "constructor_name": "CreateIotDomainDetails",
        "client_method": "create_iot_domain",
        "details_arg": "create_iot_domain_details",
        "call_kwargs": {
            "iot_domain_group_id": "group-1",
            "compartment_id": "compartment-1",
            "display_name": "Domain 1",
            "description": "desc",
            "freeform_tags": '{"env": "dev"}',
            "defined_tags": '{"ops": {"cost": "1"}}',
            "opc_retry_token": "retry-1",
            "opc_request_id": "req-1",
        },
        "expected_details": {
            "iot_domain_group_id": "group-1",
            "compartment_id": "compartment-1",
            "display_name": "Domain 1",
            "description": "desc",
            "freeform_tags": {"env": "dev"},
            "defined_tags": {"ops": {"cost": "1"}},
        },
        "expected_client_kwargs": {"opc_retry_token": "retry-1", "opc_request_id": "req-1"},
        "response_model": _simple_model("domain-1", display_name="Domain 1"),
    },
    {
        "tool_name": "create_iot_domain_group",
        "constructor_name": "CreateIotDomainGroupDetails",
        "client_method": "create_iot_domain_group",
        "details_arg": "create_iot_domain_group_details",
        "call_kwargs": {
            "compartment_id": "compartment-1",
            "type": "STANDARD",
            "display_name": "Group 1",
            "description": "desc",
            "freeform_tags": '{"env": "dev"}',
            "defined_tags": '{"ops": {"cost": "1"}}',
            "opc_retry_token": "retry-1",
            "opc_request_id": "req-1",
        },
        "expected_details": {
            "compartment_id": "compartment-1",
            "type": "STANDARD",
            "display_name": "Group 1",
            "description": "desc",
            "freeform_tags": {"env": "dev"},
            "defined_tags": {"ops": {"cost": "1"}},
        },
        "expected_client_kwargs": {"opc_retry_token": "retry-1", "opc_request_id": "req-1"},
        "response_model": _simple_model("group-1", display_name="Group 1"),
    },
]


@pytest.mark.parametrize("case", MODEL_TOOL_CASES, ids=lambda case: case["tool_name"])
def test_model_mutation_tools_build_details_and_return_model_dict(monkeypatch, case):
    captured = {}
    monkeypatch.setattr(server.oci.iot.models, case["constructor_name"], _detail_factory(case["constructor_name"]))

    def method(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(data=case["response_model"])

    monkeypatch.setattr(server, "get_iot_client", lambda: SimpleNamespace(**{case["client_method"]: method}))

    result = getattr(server, case["tool_name"])(**case["call_kwargs"])

    assert result["id"] == case["response_model"].id
    details = captured[case["details_arg"]]
    assert details.kind == case["constructor_name"]
    for key, value in case["expected_details"].items():
        assert getattr(details, key) == value
    for key, value in case["expected_client_kwargs"].items():
        assert captured[key] == value


@pytest.mark.parametrize(
    ("connectivity_type", "gateways"),
    [
        ("GATEWAY", None),
        ("INDIRECT", ["gateway-1"]),
        ("NONE", None),
    ],
)
def test_create_digital_twin_instance_accepts_gateway_connectivity_modes(
    monkeypatch,
    connectivity_type,
    gateways,
):
    captured = {}
    monkeypatch.setattr(
        server.oci.iot.models,
        "CreateDigitalTwinInstanceDetails",
        _detail_factory("CreateDigitalTwinInstanceDetails"),
    )

    def method(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            data=_simple_model(
                "twin-1",
                display_name="Twin 1",
                connectivity_type=connectivity_type,
                gateways=gateways,
            )
        )

    monkeypatch.setattr(server, "get_iot_client", lambda: SimpleNamespace(create_digital_twin_instance=method))

    result = server.create_digital_twin_instance(
        iot_domain_id="domain-1",
        display_name="Twin 1",
        connectivity_type=connectivity_type,
        gateways=gateways,
    )

    details = captured["create_digital_twin_instance_details"]
    assert details.connectivity_type == connectivity_type
    assert details.gateways == gateways
    assert result["connectivity_type"] == connectivity_type
    assert result["gateways"] == gateways


def test_create_and_update_digital_twin_instance_accept_json_gateway_arrays(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        server.oci.iot.models,
        "CreateDigitalTwinInstanceDetails",
        _detail_factory("CreateDigitalTwinInstanceDetails"),
    )
    monkeypatch.setattr(
        server.oci.iot.models,
        "UpdateDigitalTwinInstanceDetails",
        _detail_factory("UpdateDigitalTwinInstanceDetails"),
    )

    def create(**kwargs):
        captured["create"] = kwargs
        return SimpleNamespace(data=_simple_model("twin-1", gateways=["gateway-1"]))

    def update(**kwargs):
        captured["update"] = kwargs
        return SimpleNamespace(data=_simple_model("twin-1", gateways=["gateway-1"]))

    monkeypatch.setattr(
        server,
        "get_iot_client",
        lambda: SimpleNamespace(
            create_digital_twin_instance=create,
            update_digital_twin_instance=update,
        ),
    )

    server.create_digital_twin_instance(
        iot_domain_id="domain-1",
        gateways='["gateway-1"]',
    )
    server.update_digital_twin_instance(
        digital_twin_instance_id="twin-1",
        gateways='["gateway-1"]',
    )

    assert captured["create"]["create_digital_twin_instance_details"].gateways == ["gateway-1"]
    assert captured["update"]["update_digital_twin_instance_details"].gateways == ["gateway-1"]


@pytest.mark.parametrize(
    "gateways",
    [
        {"gateway": "gateway-1"},
        123,
        ["gateway-1", 2],
        [""],
        '{"gateway": "gateway-1"}',
        '"gateway-1"',
        "null",
        '["gateway-1", 2]',
        '[""]',
    ],
)
@pytest.mark.parametrize("operation", ["create", "update"])
def test_create_and_update_digital_twin_instance_reject_invalid_gateways(
    monkeypatch,
    gateways,
    operation,
):
    monkeypatch.setattr(
        server,
        "get_iot_client",
        lambda: pytest.fail("invalid gateways must be rejected before invoking OCI"),
    )

    kwargs = {"gateways": gateways}
    if operation == "create":
        call = server.create_digital_twin_instance
        kwargs["iot_domain_id"] = "domain-1"
    else:
        call = server.update_digital_twin_instance
        kwargs["digital_twin_instance_id"] = "twin-1"

    with pytest.raises(
        ValueError,
        match="gateways must be an array of non-empty strings or a JSON array string",
    ):
        call(**kwargs)


def test_list_digital_twin_instances_forwards_sdk_filters(monkeypatch):
    captured = {}

    def list_records(**kwargs):
        captured["kwargs"] = kwargs
        return [{"id": "twin-1"}]

    monkeypatch.setattr(
        server,
        "list_digital_twin_instances_records",
        list_records,
    )

    result = server.list_digital_twin_instances(
        iot_domain_id="domain-1",
        display_name="Pump 01",
        page="page-token",
        lifecycle_state="ACTIVE",
        sort_order="ASC",
        sort_by="displayName",
        opc_request_id="req-1",
        digital_twin_model_id="model-1",
        digital_twin_model_spec_uri="https://example.com/models/pump.json",
        connectivity_type="INDIRECT",
        id="twin-1",
        limit=50,
    )

    assert result == {"result": [{"id": "twin-1"}]}
    assert captured["kwargs"] == {
        "iot_domain_id": "domain-1",
        "display_name": "Pump 01",
        "page": "page-token",
        "lifecycle_state": "ACTIVE",
        "sort_order": "ASC",
        "sort_by": "displayName",
        "opc_request_id": "req-1",
        "digital_twin_model_id": "model-1",
        "digital_twin_model_spec_uri": "https://example.com/models/pump.json",
        "connectivity_type": "INDIRECT",
        "id": "twin-1",
        "limit": 50,
    }


def test_list_digital_twin_adapters_forwards_sdk_filters(monkeypatch):
    captured = {}

    def list_records(**kwargs):
        captured["kwargs"] = kwargs
        return [{"id": "adapter-1"}]

    monkeypatch.setattr(server, "list_digital_twin_adapters_records", list_records)

    result = server.list_digital_twin_adapters(
        iot_domain_id="domain-1",
        id="adapter-1",
        digital_twin_model_spec_uri="dtmi:example:Pump;1",
        digital_twin_model_id="model-1",
        display_name="Pump Adapter",
        lifecycle_state="ACTIVE",
        page="page-token",
        limit=25,
        sort_order="ASC",
        sort_by="displayName",
        opc_request_id="req-1",
    )

    assert result == {"result": [{"id": "adapter-1"}]}
    assert captured["kwargs"] == {
        "iot_domain_id": "domain-1",
        "id": "adapter-1",
        "digital_twin_model_spec_uri": "dtmi:example:Pump;1",
        "digital_twin_model_id": "model-1",
        "display_name": "Pump Adapter",
        "lifecycle_state": "ACTIVE",
        "page": "page-token",
        "limit": 25,
        "sort_order": "ASC",
        "sort_by": "displayName",
        "opc_request_id": "req-1",
    }


def test_list_digital_twin_models_forwards_sdk_filters(monkeypatch):
    captured = {}

    def list_records(**kwargs):
        captured["kwargs"] = kwargs
        return [{"id": "model-1"}]

    monkeypatch.setattr(server, "list_digital_twin_models_records", list_records)

    result = server.list_digital_twin_models(
        iot_domain_id="domain-1",
        id="model-1",
        display_name="Pump Model",
        spec_uri_starts_with="dtmi:example:Pump",
        lifecycle_state="ACTIVE",
        page="page-token",
        limit=25,
        sort_order="DESC",
        sort_by="timeCreated",
        opc_request_id="req-1",
    )

    assert result == {"result": [{"id": "model-1"}]}
    assert captured["kwargs"] == {
        "iot_domain_id": "domain-1",
        "id": "model-1",
        "display_name": "Pump Model",
        "spec_uri_starts_with": "dtmi:example:Pump",
        "lifecycle_state": "ACTIVE",
        "page": "page-token",
        "limit": 25,
        "sort_order": "DESC",
        "sort_by": "timeCreated",
        "opc_request_id": "req-1",
    }


def test_list_digital_twin_adapter_and_model_pages_return_metadata(monkeypatch):
    captured = {}
    adapter_payload = {
        "items": [{"id": "adapter-1"}],
        "opc_next_page": "adapter-next",
        "opc_request_id": "adapter-req",
        "page": "adapter-page",
        "limit": 10,
        "has_more": True,
    }
    model_payload = {
        "items": [{"id": "model-1"}],
        "opc_next_page": "model-next",
        "opc_request_id": "model-req",
        "page": "model-page",
        "limit": 20,
        "has_more": True,
    }

    def adapter_page(**kwargs):
        captured["adapter"] = kwargs
        return adapter_payload

    def model_page(**kwargs):
        captured["model"] = kwargs
        return model_payload

    monkeypatch.setattr(server, "list_digital_twin_adapters_page_record", adapter_page, raising=False)
    monkeypatch.setattr(server, "list_digital_twin_models_page_record", model_page, raising=False)

    adapter_result = server.list_digital_twin_adapters_page(
        iot_domain_id="domain-1",
        page="adapter-page",
        limit=10,
    )
    model_result = server.list_digital_twin_models_page(
        iot_domain_id="domain-1",
        page="model-page",
        limit=20,
    )

    assert adapter_result == {"result": adapter_payload}
    assert model_result == {"result": model_payload}
    assert captured["adapter"] == {
        "iot_domain_id": "domain-1",
        "id": None,
        "digital_twin_model_spec_uri": None,
        "digital_twin_model_id": None,
        "display_name": None,
        "lifecycle_state": None,
        "page": "adapter-page",
        "limit": 10,
        "sort_order": None,
        "sort_by": None,
        "opc_request_id": None,
    }
    assert captured["model"] == {
        "iot_domain_id": "domain-1",
        "id": None,
        "display_name": None,
        "spec_uri_starts_with": None,
        "lifecycle_state": None,
        "page": "model-page",
        "limit": 20,
        "sort_order": None,
        "sort_by": None,
        "opc_request_id": None,
    }


def test_domain_group_domain_and_work_request_list_tools_forward_sdk_filters(monkeypatch):
    captured = {}

    def list_groups(**kwargs):
        captured["groups"] = kwargs
        return [{"id": "group-1"}]

    def list_domains(**kwargs):
        captured["domains"] = kwargs
        return [{"id": "domain-1"}]

    def list_work_requests(**kwargs):
        captured["work_requests"] = kwargs
        return [{"id": "wr-1"}]

    monkeypatch.setattr(server, "list_iot_domain_groups_records", list_groups)
    monkeypatch.setattr(server, "list_iot_domains_records", list_domains)
    monkeypatch.setattr(server, "list_work_requests_records", list_work_requests)

    groups = server.list_iot_domain_groups(
        compartment_id="compartment-1",
        id="group-1",
        display_name="Group 1",
        lifecycle_state="ACTIVE",
        type="STANDARD",
        page="group-page",
        limit=25,
        sort_order="ASC",
        sort_by="displayName",
        opc_request_id="group-req",
    )
    domains = server.list_iot_domains(
        compartment_id="compartment-1",
        id="domain-1",
        iot_domain_group_id="group-1",
        display_name="Domain 1",
        lifecycle_state="ACTIVE",
        page="domain-page",
        limit=50,
        sort_order="DESC",
        sort_by="timeCreated",
        opc_request_id="domain-req",
    )
    work_requests = server.list_work_requests(
        compartment_id="compartment-1",
        id="wr-1",
        status="SUCCEEDED",
        resource_id="domain-1",
        page="wr-page",
        limit=10,
        sort_order="DESC",
        sort_by="timeAccepted",
        opc_request_id="wr-req",
    )

    assert groups == {"result": [{"id": "group-1"}]}
    assert domains == {"result": [{"id": "domain-1"}]}
    assert work_requests == {"result": [{"id": "wr-1"}]}
    assert captured == {
        "groups": {
            "compartment_id": "compartment-1",
            "id": "group-1",
            "display_name": "Group 1",
            "lifecycle_state": "ACTIVE",
            "type": "STANDARD",
            "page": "group-page",
            "limit": 25,
            "sort_order": "ASC",
            "sort_by": "displayName",
            "opc_request_id": "group-req",
        },
        "domains": {
            "compartment_id": "compartment-1",
            "id": "domain-1",
            "iot_domain_group_id": "group-1",
            "display_name": "Domain 1",
            "lifecycle_state": "ACTIVE",
            "page": "domain-page",
            "limit": 50,
            "sort_order": "DESC",
            "sort_by": "timeCreated",
            "opc_request_id": "domain-req",
        },
        "work_requests": {
            "compartment_id": "compartment-1",
            "id": "wr-1",
            "status": "SUCCEEDED",
            "resource_id": "domain-1",
            "page": "wr-page",
            "limit": 10,
            "sort_order": "DESC",
            "sort_by": "timeAccepted",
            "opc_request_id": "wr-req",
        },
    }


def test_list_digital_twin_relationships_forwards_sdk_filters(monkeypatch):
    captured = {}

    def list_records(**kwargs):
        captured["kwargs"] = kwargs
        return [{"id": "rel-1"}]

    monkeypatch.setattr(
        server,
        "list_digital_twin_relationships_records",
        list_records,
    )

    result = server.list_digital_twin_relationships(
        iot_domain_id="domain-1",
        display_name="Floor contains Room",
        content_path="contains",
        source_digital_twin_instance_id="floor-1",
        target_digital_twin_instance_id="room-1",
        lifecycle_state="ACTIVE",
        page="page-token",
        sort_order="ASC",
        sort_by="displayName",
        opc_request_id="req-1",
        id="rel-1",
        limit=50,
    )

    assert result == {"result": [{"id": "rel-1"}]}
    assert captured["kwargs"] == {
        "iot_domain_id": "domain-1",
        "display_name": "Floor contains Room",
        "content_path": "contains",
        "source_digital_twin_instance_id": "floor-1",
        "target_digital_twin_instance_id": "room-1",
        "lifecycle_state": "ACTIVE",
        "page": "page-token",
        "sort_order": "ASC",
        "sort_by": "displayName",
        "opc_request_id": "req-1",
        "id": "rel-1",
        "limit": 50,
    }


def test_list_digital_twin_relationships_page_returns_metadata(monkeypatch):
    captured = {}
    payload = {
        "items": [{"id": "rel-1"}],
        "opc_next_page": "next-token",
        "opc_request_id": "req-1",
        "page": "page-token",
        "limit": 10,
        "has_more": True,
    }

    def list_page_record(**kwargs):
        captured["kwargs"] = kwargs
        return payload

    monkeypatch.setattr(
        server,
        "list_digital_twin_relationships_page_record",
        list_page_record,
        raising=False,
    )

    result = server.list_digital_twin_relationships_page(
        iot_domain_id="domain-1",
        page="page-token",
        limit=10,
    )

    assert result == {"result": payload}
    assert captured["kwargs"] == {
        "iot_domain_id": "domain-1",
        "display_name": None,
        "content_path": None,
        "source_digital_twin_instance_id": None,
        "target_digital_twin_instance_id": None,
        "lifecycle_state": None,
        "page": "page-token",
        "sort_order": None,
        "sort_by": None,
        "opc_request_id": None,
        "id": None,
        "limit": 10,
    }


def test_list_all_digital_twin_relationships_returns_bounded_payload(monkeypatch):
    captured = {}
    payload = {
        "items": [{"id": "rel-1"}, {"id": "rel-2"}],
        "count": 2,
        "max_items": 50,
        "page_size": 25,
        "pages_fetched": 1,
        "opc_next_page": None,
        "opc_request_id": "req-1",
        "has_more": False,
        "truncated": False,
    }

    def list_all_records(**kwargs):
        captured["kwargs"] = kwargs
        return payload

    monkeypatch.setattr(
        server,
        "list_all_digital_twin_relationships_records",
        list_all_records,
        raising=False,
    )

    result = server.list_all_digital_twin_relationships(
        iot_domain_id="domain-1",
        lifecycle_state="ACTIVE",
        max_items=50,
        page_size=25,
    )

    assert result == {"result": payload}
    assert captured["kwargs"] == {
        "iot_domain_id": "domain-1",
        "display_name": None,
        "content_path": None,
        "source_digital_twin_instance_id": None,
        "target_digital_twin_instance_id": None,
        "lifecycle_state": "ACTIVE",
        "sort_order": None,
        "sort_by": None,
        "opc_request_id": None,
        "id": None,
        "max_items": 50,
        "page_size": 25,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("max_items", 0, "greater than or equal to 1"),
        ("max_items", 1001, "less than or equal to 1000"),
        ("page_size", 0, "greater than or equal to 1"),
        ("page_size", 1001, "less than or equal to 1000"),
    ],
)
async def test_list_all_digital_twin_relationships_rejects_out_of_bounds_fastmcp_calls(
    field,
    value,
    message,
):
    async with Client(server.mcp) as client:
        with pytest.raises(Exception, match=message):
            await client.call_tool(
                "list_all_digital_twin_relationships",
                {
                    "iot_domain_id": "domain-1",
                    field: value,
                },
            )


def test_get_digital_twin_instance_full_returns_raw_sdk_payload(monkeypatch):
    captured = {}

    def get_digital_twin_instance(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            data={
                "id": "twin-1",
                "connectivity_type": "INDIRECT",
                "gateways": ["gateway-1"],
                "new_sdk_field": {"kept": True},
            }
        )

    monkeypatch.setattr(
        server,
        "get_iot_client",
        lambda: SimpleNamespace(get_digital_twin_instance=get_digital_twin_instance),
    )

    result = server.get_digital_twin_instance_full(
        digital_twin_instance_id="twin-1",
        opc_request_id="req-1",
    )

    assert result["ok"] is True
    assert result["data"]["connectivity_type"] == "INDIRECT"
    assert result["data"]["gateways"] == ["gateway-1"]
    assert result["data"]["new_sdk_field"] == {"kept": True}
    assert captured == {
        "digital_twin_instance_id": "twin-1",
        "opc_request_id": "req-1",
    }


RESPONSE_TOOL_CASES = [
    {
        "tool_name": "delete_digital_twin_adapter",
        "client_method": "delete_digital_twin_adapter",
        "call_kwargs": {
            "digital_twin_adapter_id": "adapter-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "expected_client_kwargs": {
            "digital_twin_adapter_id": "adapter-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
    },
    {
        "tool_name": "delete_digital_twin_instance",
        "client_method": "delete_digital_twin_instance",
        "call_kwargs": {
            "digital_twin_instance_id": "twin-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "expected_client_kwargs": {
            "digital_twin_instance_id": "twin-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
    },
    {
        "tool_name": "delete_digital_twin_model",
        "client_method": "delete_digital_twin_model",
        "call_kwargs": {
            "digital_twin_model_id": "model-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "expected_client_kwargs": {
            "digital_twin_model_id": "model-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
    },
    {
        "tool_name": "delete_digital_twin_relationship",
        "client_method": "delete_digital_twin_relationship",
        "call_kwargs": {
            "digital_twin_relationship_id": "rel-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "expected_client_kwargs": {
            "digital_twin_relationship_id": "rel-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
    },
    {
        "tool_name": "change_iot_domain_compartment",
        "client_method": "change_iot_domain_compartment",
        "constructor_name": "ChangeIotDomainCompartmentDetails",
        "details_arg": "change_iot_domain_compartment_details",
        "call_kwargs": {
            "iot_domain_id": "domain-1",
            "compartment_id": "compartment-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
            "opc_retry_token": "retry-1",
        },
        "expected_details": {"compartment_id": "compartment-1"},
        "expected_client_kwargs": {
            "iot_domain_id": "domain-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
            "opc_retry_token": "retry-1",
        },
    },
    {
        "tool_name": "change_iot_domain_data_retention_period",
        "client_method": "change_iot_domain_data_retention_period",
        "constructor_name": "ChangeIotDomainDataRetentionPeriodDetails",
        "details_arg": "change_iot_domain_data_retention_period_details",
        "call_kwargs": {
            "iot_domain_id": "domain-1",
            "type": "RAW_DATA",
            "data_retention_period_in_days": 14,
            "if_match": "etag-1",
            "opc_request_id": "req-1",
            "opc_retry_token": "retry-1",
        },
        "expected_details": {"type": "RAW_DATA", "data_retention_period_in_days": 14},
        "expected_client_kwargs": {
            "iot_domain_id": "domain-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
            "opc_retry_token": "retry-1",
        },
    },
    {
        "tool_name": "change_iot_domain_group_compartment",
        "client_method": "change_iot_domain_group_compartment",
        "constructor_name": "ChangeIotDomainGroupCompartmentDetails",
        "details_arg": "change_iot_domain_group_compartment_details",
        "call_kwargs": {
            "iot_domain_group_id": "group-1",
            "compartment_id": "compartment-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
            "opc_retry_token": "retry-1",
        },
        "expected_details": {"compartment_id": "compartment-1"},
        "expected_client_kwargs": {
            "iot_domain_group_id": "group-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
            "opc_retry_token": "retry-1",
        },
    },
    {
        "tool_name": "configure_iot_domain_group_data_access",
        "client_method": "configure_iot_domain_group_data_access",
        "constructor_name": "ConfigureIotDomainGroupDataAccessDetails",
        "details_arg": "configure_iot_domain_group_data_access_details",
        "call_kwargs": {
            "iot_domain_group_id": "group-1",
            "db_allow_listed_vcn_ids": '["vcn-1", "vcn-2"]',
            "if_match": "etag-1",
            "opc_request_id": "req-1",
            "opc_retry_token": "retry-1",
        },
        "expected_details": {"db_allow_listed_vcn_ids": ["vcn-1", "vcn-2"]},
        "expected_client_kwargs": {
            "iot_domain_group_id": "group-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
            "opc_retry_token": "retry-1",
        },
    },
    {
        "tool_name": "update_iot_domain",
        "client_method": "update_iot_domain",
        "constructor_name": "UpdateIotDomainDetails",
        "details_arg": "update_iot_domain_details",
        "call_kwargs": {
            "iot_domain_id": "domain-1",
            "display_name": "Domain 1",
            "description": "desc",
            "freeform_tags": '{"env": "dev"}',
            "defined_tags": '{"ops": {"cost": "1"}}',
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "expected_details": {
            "display_name": "Domain 1",
            "description": "desc",
            "freeform_tags": {"env": "dev"},
            "defined_tags": {"ops": {"cost": "1"}},
        },
        "expected_client_kwargs": {
            "iot_domain_id": "domain-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
    },
    {
        "tool_name": "update_iot_domain_group",
        "client_method": "update_iot_domain_group",
        "constructor_name": "UpdateIotDomainGroupDetails",
        "details_arg": "update_iot_domain_group_details",
        "call_kwargs": {
            "iot_domain_group_id": "group-1",
            "display_name": "Group 1",
            "description": "desc",
            "freeform_tags": '{"env": "dev"}',
            "defined_tags": '{"ops": {"cost": "1"}}',
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "expected_details": {
            "display_name": "Group 1",
            "description": "desc",
            "freeform_tags": {"env": "dev"},
            "defined_tags": {"ops": {"cost": "1"}},
        },
        "expected_client_kwargs": {
            "iot_domain_group_id": "group-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
    },
    {
        "tool_name": "delete_iot_domain",
        "client_method": "delete_iot_domain",
        "call_kwargs": {
            "iot_domain_id": "domain-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "expected_client_kwargs": {
            "iot_domain_id": "domain-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
    },
    {
        "tool_name": "delete_iot_domain_group",
        "client_method": "delete_iot_domain_group",
        "call_kwargs": {
            "iot_domain_group_id": "group-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
        "expected_client_kwargs": {
            "iot_domain_group_id": "group-1",
            "if_match": "etag-1",
            "opc_request_id": "req-1",
        },
    },
]


@pytest.mark.parametrize("case", RESPONSE_TOOL_CASES, ids=lambda case: case["tool_name"])
def test_response_mutation_tools_return_response_metadata(monkeypatch, case):
    captured = {}
    if "constructor_name" in case:
        monkeypatch.setattr(server.oci.iot.models, case["constructor_name"], _detail_factory(case["constructor_name"]))

    def method(**kwargs):
        captured.update(kwargs)
        return _response(status=202, request_id="req-123", headers={"etag": "etag-1"}, data={"ok": True})

    monkeypatch.setattr(server, "get_iot_client", lambda: SimpleNamespace(**{case["client_method"]: method}))

    result = getattr(server, case["tool_name"])(**case["call_kwargs"])

    assert result == {
        "status": 202,
        "request_id": "req-123",
        "headers": {"etag": "etag-1"},
        "data": {"ok": True},
    }
    if "details_arg" in case:
        details = captured[case["details_arg"]]
        assert details.kind == case["constructor_name"]
        for key, value in case["expected_details"].items():
            assert getattr(details, key) == value
    for key, value in case["expected_client_kwargs"].items():
        assert captured[key] == value


@pytest.mark.parametrize(
    ("access_type", "constructor_name", "call_kwargs", "expected_detail_fields"),
    [
        (
            "DIRECT",
            "DirectDataAccessDetails",
            {
                "iot_domain_id": "domain-1",
                "type": "DIRECT",
                "db_allow_listed_identity_group_names": '["operators"]',
                "if_match": "etag-1",
                "opc_request_id": "req-1",
                "opc_retry_token": "retry-1",
            },
            {"db_allow_listed_identity_group_names": ["operators"]},
        ),
        (
            "ORDS",
            "OrdsDataAccessDetails",
            {
                "iot_domain_id": "domain-1",
                "type": "ORDS",
                "db_allowed_identity_domain_host": "identity.example.com",
                "if_match": "etag-1",
                "opc_request_id": "req-1",
                "opc_retry_token": "retry-1",
            },
            {"db_allowed_identity_domain_host": "identity.example.com"},
        ),
        (
            "APEX",
            "ApexDataAccessDetails",
            {
                "iot_domain_id": "domain-1",
                "type": "APEX",
                "db_workspace_admin_initial_password": "Secret123!",
                "if_match": "etag-1",
                "opc_request_id": "req-1",
                "opc_retry_token": "retry-1",
            },
            {"db_workspace_admin_initial_password": "Secret123!"},
        ),
    ],
)
def test_configure_iot_domain_data_access_supports_each_access_type(
    monkeypatch,
    access_type,
    constructor_name,
    call_kwargs,
    expected_detail_fields,
):
    captured = {}
    monkeypatch.setattr(server.oci.iot.models, constructor_name, _detail_factory(constructor_name))

    def method(**kwargs):
        captured.update(kwargs)
        return _response(status=202, request_id="req-123", headers={"etag": "etag-1"}, data={"ok": True})

    monkeypatch.setattr(server, "get_iot_client", lambda: SimpleNamespace(configure_iot_domain_data_access=method))

    result = server.configure_iot_domain_data_access(**call_kwargs)

    assert result["request_id"] == "req-123"
    details = captured["configure_iot_domain_data_access_details"]
    assert details.kind == constructor_name
    for key, value in expected_detail_fields.items():
        assert getattr(details, key) == value
    assert captured["iot_domain_id"] == "domain-1"
    assert captured["if_match"] == "etag-1"
    assert captured["opc_request_id"] == "req-1"
    assert captured["opc_retry_token"] == "retry-1"


def test_configure_iot_domain_data_access_rejects_unknown_type(monkeypatch):
    monkeypatch.setattr(server, "get_iot_client", lambda: SimpleNamespace())

    with pytest.raises(ValueError, match="type must be one of: DIRECT, ORDS, APEX"):
        server.configure_iot_domain_data_access(iot_domain_id="domain-1", type="UNKNOWN")


def test_invoke_raw_command_builds_details_through_helper_and_returns_response_metadata(monkeypatch):
    captured = {}
    helper_calls = {}

    def fake_build_details(**kwargs):
        helper_calls["kwargs"] = kwargs
        return SimpleNamespace(kind="InvokeRawDetails")

    monkeypatch.setattr(server, "_build_direct_invoke_raw_command_details", fake_build_details)

    def method(**kwargs):
        captured.update(kwargs)
        return _response(status=202, request_id="req-123", headers={"etag": "etag-1"}, data={"ok": True})

    monkeypatch.setattr(server, "get_iot_client", lambda: SimpleNamespace(invoke_raw_command=method))

    result = server.invoke_raw_command(
        digital_twin_instance_id="twin-1",
        request_endpoint="/v1/cmd",
        request_data_format="JSON",
        request_data='{"enabled": true}',
        response_endpoint="/v1/reply",
        request_duration="PT1S",
        response_duration="PT2S",
        request_data_content_type="application/json",
        opc_retry_token="retry-1",
        opc_request_id="req-1",
    )

    assert result["request_id"] == "req-123"
    assert helper_calls["kwargs"] == {
        "request_data_format": "JSON",
        "request_endpoint": "/v1/cmd",
        "response_endpoint": "/v1/reply",
        "request_duration": "PT1S",
        "response_duration": "PT2S",
        "request_data_content_type": "application/json",
        "request_data": '{"enabled": true}',
    }
    assert captured["digital_twin_instance_id"] == "twin-1"
    assert captured["opc_retry_token"] == "retry-1"
    assert captured["opc_request_id"] == "req-1"


def test_invoke_raw_command_returns_invalid_input_error_for_unknown_format(monkeypatch):
    result = server.invoke_raw_command(
        digital_twin_instance_id="twin-1",
        request_endpoint="/v1/cmd",
        request_data_format="XML",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_input"


def test_list_compartments_includes_root_and_deduplicates_results(monkeypatch):
    root = _simple_model(
        "tenancy-1",
        name="Root",
        description="Tenancy",
        parent_id=None,
        lifecycle_state="ACTIVE",
    )
    child = _simple_model(
        "child-1",
        name="Child",
        description="Child compartment",
        parent_id="tenancy-1",
        lifecycle_state="ACTIVE",
    )

    def get_compartment(*, compartment_id):
        assert compartment_id == "tenancy-1"
        return SimpleNamespace(data=root)

    identity_client = SimpleNamespace(
        get_compartment=get_compartment,
        list_compartments=lambda **kwargs: None,
    )
    monkeypatch.setattr(server, "get_identity_client", lambda profile_name=None: (identity_client, "tenancy-1"))

    def list_all_results(func, **kwargs):
        assert func is identity_client.list_compartments
        assert kwargs == {
            "compartment_id": "tenancy-1",
            "compartment_id_in_subtree": True,
            "access_level": "ACCESSIBLE",
        }
        return SimpleNamespace(data=[root, child])

    monkeypatch.setattr(server.oci.pagination, "list_call_get_all_results", list_all_results)

    result = server.list_compartments()

    assert result["result"][0]["id"] == "tenancy-1"
    assert result["result"][1]["id"] == "child-1"
    assert len(result["result"]) == 2


DATA_API_TOOL_CASES = [
    (
        "list_raw_data",
        {
            "iot_domain_group_short_id": "group-short",
            "iot_domain_short_id": "domain-short",
            "query_params": {"limit": 5},
            "region": "us-ashburn-1",
            "access_token": "token-123",
            "opc_request_id": "req-1",
        },
        "/rawData",
    ),
    (
        "get_raw_data",
        {
            "iot_domain_group_short_id": "group-short",
            "iot_domain_short_id": "domain-short",
            "record_id": "raw-1",
            "region": "us-ashburn-1",
            "access_token": "token-123",
            "opc_request_id": "req-1",
        },
        "/rawData/raw-1",
    ),
    (
        "list_rejected_data",
        {
            "iot_domain_group_short_id": "group-short",
            "iot_domain_short_id": "domain-short",
            "query_params": {"limit": 5},
            "region": "us-ashburn-1",
            "access_token": "token-123",
            "opc_request_id": "req-1",
        },
        "/rejectedData",
    ),
    (
        "get_rejected_data",
        {
            "iot_domain_group_short_id": "group-short",
            "iot_domain_short_id": "domain-short",
            "record_id": "rej-1",
            "region": "us-ashburn-1",
            "access_token": "token-123",
            "opc_request_id": "req-1",
        },
        "/rejectedData/rej-1",
    ),
    (
        "list_snapshot_data",
        {
            "iot_domain_group_short_id": "group-short",
            "iot_domain_short_id": "domain-short",
            "query_params": {"limit": 5},
            "region": "us-ashburn-1",
            "access_token": "token-123",
            "opc_request_id": "req-1",
        },
        "/snapshotData",
    ),
    (
        "list_historized_data",
        {
            "iot_domain_group_short_id": "group-short",
            "iot_domain_short_id": "domain-short",
            "query_params": {"limit": 5},
            "region": "us-ashburn-1",
            "access_token": "token-123",
            "opc_request_id": "req-1",
        },
        "/historizedData",
    ),
    (
        "get_historized_data",
        {
            "iot_domain_group_short_id": "group-short",
            "iot_domain_short_id": "domain-short",
            "record_id": "hist-1",
            "region": "us-ashburn-1",
            "access_token": "token-123",
            "opc_request_id": "req-1",
        },
        "/historizedData/hist-1",
    ),
    (
        "list_raw_command_data",
        {
            "iot_domain_group_short_id": "group-short",
            "iot_domain_short_id": "domain-short",
            "query_params": {"limit": 5},
            "region": "us-ashburn-1",
            "access_token": "token-123",
            "opc_request_id": "req-1",
        },
        "/rawCommandData",
    ),
    (
        "get_raw_command_data",
        {
            "iot_domain_group_short_id": "group-short",
            "iot_domain_short_id": "domain-short",
            "record_id": "cmd-1",
            "region": "us-ashburn-1",
            "access_token": "token-123",
            "opc_request_id": "req-1",
        },
        "/rawCommandData/cmd-1",
    ),
]


@pytest.mark.parametrize(("tool_name", "call_kwargs", "resource_path"), DATA_API_TOOL_CASES)
def test_direct_data_api_tools_delegate_to_call_helper(monkeypatch, tool_name, call_kwargs, resource_path):
    captured = {}

    def fake_call(**kwargs):
        captured.update(kwargs)
        return {"items": ["ok"]}

    monkeypatch.setattr(server, "_call_iot_data_api", fake_call)

    result = getattr(server, tool_name)(**call_kwargs)

    assert result == {"items": ["ok"]}
    assert captured["resource_path"] == resource_path
    assert captured["iot_domain_group_short_id"] == "group-short"
    assert captured["iot_domain_short_id"] == "domain-short"
    assert captured["region"] == "us-ashburn-1"
    assert captured["access_token"] == "token-123"
    assert captured["opc_request_id"] == "req-1"
    if "query_params" in call_kwargs:
        assert captured["query_params"] == {"limit": 5}


def test_direct_data_api_tool_returns_missing_access_token_error(monkeypatch):
    monkeypatch.delenv("OCI_IOT_DATA_API_ACCESS_TOKEN", raising=False)

    result = server.list_raw_data(
        iot_domain_group_short_id="group-short",
        iot_domain_short_id="domain-short",
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "missing_access_token"
