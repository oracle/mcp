import importlib

import pytest

from oracle.oci_iot_mcp_server.data_plane import DataApiTokenError
from oracle.oci_iot_mcp_server.tool_models import DataApiTokenModel


def load_agent_workflows():
    try:
        return importlib.import_module("oracle.oci_iot_mcp_server.agent_workflows")
    except ModuleNotFoundError as exc:
        pytest.fail(f"agent_workflows module should exist: {exc}")


def test_get_twin_platform_context_returns_related_resources(monkeypatch):
    agent_workflows = load_agent_workflows()

    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_for_tool",
        lambda **_: {
            "id": "twin-1",
            "name": "pump-17",
            "iot_domain_id": "domain-1",
            "digital_twin_adapter_id": "adapter-1",
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "get_iot_domain_record",
        lambda _id: {
            "id": "domain-1",
            "name": "factory-a",
            "iot_domain_group_id": "group-1",
            "device_host": "factory-a.iot.us-ashburn-1.oci.oraclecloud.com",
            "db_allowed_identity_domain_host": "idcs.example.com",
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "get_iot_domain_group_record",
        lambda _id: {
            "id": "group-1",
            "name": "factory-group",
            "data_host": "group-a.data.iot.us-ashburn-1.oci.oraclecloud.com",
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "get_digital_twin_adapter_record",
        lambda _id: {
            "id": "adapter-1",
            "name": "pump-adapter",
            "digital_twin_model_id": "model-1",
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "get_digital_twin_model_record",
        lambda _id: {"id": "model-1", "name": "pump-model"},
    )

    payload = agent_workflows.get_twin_platform_context_impl(digital_twin_instance_id="twin-1")

    assert payload["twin"]["id"] == "twin-1"
    assert payload["domain_context"]["domain_short_id"] == "factory-a"


def test_get_twin_platform_context_includes_gateway_for_indirect_twin(monkeypatch):
    agent_workflows = load_agent_workflows()

    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_for_tool",
        lambda **_: {
            "id": "twin-1",
            "name": "pump-17",
            "iot_domain_id": "domain-1",
            "connectivity_type": "INDIRECT",
            "gateways": ["gateway-1"],
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "get_iot_domain_record",
        lambda _id: {
            "id": "domain-1",
            "name": "factory-a",
            "iot_domain_group_id": "group-1",
            "device_host": "factory-a.iot.us-ashburn-1.oci.oraclecloud.com",
            "db_allowed_identity_domain_host": "idcs.example.com",
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "get_iot_domain_group_record",
        lambda _id: {
            "id": "group-1",
            "name": "factory-group",
            "data_host": "group-a.data.iot.us-ashburn-1.oci.oraclecloud.com",
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "get_digital_twin_instance_record",
        lambda _id: {
            "id": "gateway-1",
            "name": "gateway",
            "connectivity_type": "GATEWAY",
            "gateways": None,
        },
        raising=False,
    )

    payload = agent_workflows.get_twin_platform_context_impl(digital_twin_instance_id="twin-1")

    assert payload["twin"]["connectivity_type"] == "INDIRECT"
    assert payload["gateway_topology"]["connectivity_type"] == "INDIRECT"
    assert payload["gateway_topology"]["gateway_twins"] == [
        {
            "id": "gateway-1",
            "name": "gateway",
            "connectivity_type": "GATEWAY",
            "gateways": None,
        }
    ]
    assert payload["gateway_topology"]["gateway_resolution_errors"] == []


def test_get_twin_platform_context_lists_bounded_indirect_children_for_gateway(monkeypatch):
    agent_workflows = load_agent_workflows()

    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_for_tool",
        lambda **_: {
            "id": "gateway-1",
            "name": "gateway",
            "iot_domain_id": "domain-1",
            "connectivity_type": "GATEWAY",
            "gateways": None,
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "get_iot_domain_record",
        lambda _id: {
            "id": "domain-1",
            "name": "factory-a",
            "iot_domain_group_id": "group-1",
            "device_host": "factory-a.iot.us-ashburn-1.oci.oraclecloud.com",
            "db_allowed_identity_domain_host": "idcs.example.com",
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "get_iot_domain_group_record",
        lambda _id: {
            "id": "group-1",
            "name": "factory-group",
            "data_host": "group-a.data.iot.us-ashburn-1.oci.oraclecloud.com",
        },
    )

    captured = {}

    def list_instances(**kwargs):
        captured.update(kwargs)
        return {
            "items": [
                {"id": "child-1", "connectivity_type": "INDIRECT", "gateways": ["gateway-1"]},
                {"id": "child-2", "connectivity_type": "INDIRECT", "gateways": ["gateway-2"]},
            ],
            "opc_next_page": None,
            "opc_request_id": "request-1",
            "page": None,
            "limit": 100,
            "has_more": False,
        }

    monkeypatch.setattr(
        agent_workflows, "list_digital_twin_instances_page_record", list_instances, raising=False
    )

    payload = agent_workflows.get_twin_platform_context_impl(digital_twin_instance_id="gateway-1")

    assert captured == {
        "iot_domain_id": "domain-1",
        "connectivity_type": "INDIRECT",
        "limit": 100,
    }
    assert payload["gateway_topology"]["indirect_children"] == [
        {"id": "child-1", "connectivity_type": "INDIRECT", "gateways": ["gateway-1"]}
    ]
    assert payload["gateway_topology"]["child_discovery_truncated"] is False
    assert payload["gateway_topology"]["warnings"] == []


def test_gateway_topology_warns_when_child_discovery_is_truncated(monkeypatch):
    agent_workflows = load_agent_workflows()

    monkeypatch.setattr(
        agent_workflows,
        "list_digital_twin_instances_page_record",
        lambda **_: {
            "items": [
                {"id": "child-1", "connectivity_type": "INDIRECT", "gateways": ["gateway-1"]}
            ],
            "opc_next_page": "page-2",
            "opc_request_id": "request-1",
            "page": None,
            "limit": 100,
            "has_more": True,
        },
        raising=False,
    )

    topology = agent_workflows.resolve_gateway_topology(
        {
            "twin": {
                "id": "gateway-1",
                "iot_domain_id": "domain-1",
                "connectivity_type": "GATEWAY",
            }
        }
    )

    assert topology["indirect_children"] == [
        {"id": "child-1", "connectivity_type": "INDIRECT", "gateways": ["gateway-1"]}
    ]
    assert topology["child_discovery_truncated"] is True
    assert topology["warnings"] == [
        "Indirect child discovery is bounded to one SDK list call and may not include every child twin."
    ]


def test_gateway_topology_degrades_when_child_discovery_fails(monkeypatch):
    agent_workflows = load_agent_workflows()

    def list_instances(**_kwargs):
        raise RuntimeError("sensitive service detail")

    monkeypatch.setattr(
        agent_workflows, "list_digital_twin_instances_page_record", list_instances, raising=False
    )

    topology = agent_workflows.resolve_gateway_topology(
        {
            "twin": {
                "id": "gateway-1",
                "iot_domain_id": "domain-1",
                "connectivity_type": "GATEWAY",
            }
        }
    )

    assert topology["indirect_children"] == []
    assert topology["child_discovery_truncated"] is False
    assert topology["child_discovery_errors"] == [
        {
            "message": "Unable to discover indirect child twins for gateway.",
            "error_type": "RuntimeError",
        }
    ]
    assert topology["warnings"] == [
        "Indirect child discovery failed; gateway topology may be incomplete."
    ]
    assert "sensitive service detail" not in str(topology)


def test_gateway_topology_normalizes_indirect_gateway_lookup_exception(monkeypatch):
    agent_workflows = load_agent_workflows()

    def get_gateway(_gateway_id):
        raise ValueError("sensitive gateway detail")

    monkeypatch.setattr(agent_workflows, "get_digital_twin_instance_record", get_gateway, raising=False)

    topology = agent_workflows.resolve_gateway_topology(
        {
            "twin": {
                "id": "child-1",
                "connectivity_type": "INDIRECT",
                "gateways": ["gateway-1"],
            }
        }
    )

    assert topology["gateway_resolution_errors"] == [
        {
            "gateway_id": "gateway-1",
            "message": "Gateway twin could not be resolved.",
            "error_type": "ValueError",
        }
    ]
    assert topology["warnings"] == ["One or more gateway twins could not be resolved."]
    assert "sensitive gateway detail" not in str(topology)


def test_gateway_topology_check_warns_on_child_discovery_errors():
    agent_workflows = load_agent_workflows()

    check = agent_workflows._gateway_topology_check(
        {
            "connectivity_type": "GATEWAY",
            "child_discovery_errors": [
                {
                    "message": "Unable to discover indirect child twins for gateway.",
                    "error_type": "ServiceError",
                }
            ],
        }
    )

    assert check == {
        "name": "gateway_topology",
        "status": "warning",
        "details": {
            "connectivity_type": "GATEWAY",
            "child_discovery_errors": [
                {
                    "message": "Unable to discover indirect child twins for gateway.",
                    "error_type": "ServiceError",
                }
            ],
        },
    }


def test_gateway_topology_check_warns_on_truncated_child_discovery():
    agent_workflows = load_agent_workflows()

    check = agent_workflows._gateway_topology_check(
        {
            "connectivity_type": "GATEWAY",
            "child_discovery_truncated": True,
            "indirect_children": [{"id": "child-1"}],
            "warnings": [
                "Indirect child discovery is bounded to one SDK list call and may not include every child twin."
            ],
        }
    )

    assert check == {
        "name": "gateway_topology",
        "status": "warning",
        "details": {
            "connectivity_type": "GATEWAY",
            "child_discovery_truncated": True,
            "indirect_child_count": 1,
            "warnings": [
                "Indirect child discovery is bounded to one SDK list call and may not include every child twin."
            ],
        },
    }


def test_get_latest_twin_state_returns_latest_records(monkeypatch):
    agent_workflows = load_agent_workflows()
    if not hasattr(agent_workflows, "get_latest_twin_state_impl"):
        pytest.fail("agent_workflows should expose get_latest_twin_state_impl")

    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-27T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_bundle_with_token",
        lambda **_: (
            {
                "twin": {"id": "twin-1", "name": "pump-17"},
                "domain_context": {"data_host": "group-a.data.iot.us-ashburn-1.oci.oraclecloud.com", "domain_short_id": "factory-a"},
            },
            token,
        ),
        raising=False,
    )
    monkeypatch.setattr(agent_workflows, "list_snapshot_records", lambda **_: [
        {"id": "snap-old", "time_created": "2026-03-27T09:00:00Z"},
        {"id": "snap-new", "time_created": "2026-03-27T10:00:00Z"},
    ])
    monkeypatch.setattr(agent_workflows, "list_historized_records", lambda **_: [
        {"id": "hist-1", "time_created": "2026-03-27T09:58:00Z"}
    ])
    monkeypatch.setattr(agent_workflows, "list_raw_command_records", lambda **_: [
        {"id": "cmd-1", "time_created": "2026-03-27T09:57:00Z"}
    ])
    monkeypatch.setattr(agent_workflows, "list_rejected_data_records", lambda **_: [
        {"id": "rej-1", "time_received": "2026-03-27T09:40:00Z"}
    ])

    payload = agent_workflows.get_latest_twin_state_impl(digital_twin_instance_id="twin-1")

    assert payload["twin"]["id"] == "twin-1"
    assert payload["latest_snapshot"]["id"] == "snap-new"
    assert payload["latest_historized"]["id"] == "hist-1"
    assert payload["latest_raw_command"]["id"] == "cmd-1"
    assert payload["latest_rejected_data"]["id"] == "rej-1"
    assert payload["observed_timestamps"] == {
        "snapshot": "2026-03-27T10:00:00Z",
        "historized": "2026-03-27T09:58:00Z",
        "raw_command": "2026-03-27T09:57:00Z",
        "rejected_data": "2026-03-27T09:40:00Z",
    }


def test_validate_twin_readiness_reports_warning_when_snapshot_is_missing(monkeypatch):
    agent_workflows = load_agent_workflows()
    if not hasattr(agent_workflows, "validate_twin_readiness_impl"):
        pytest.fail("agent_workflows should expose validate_twin_readiness_impl")

    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-27T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_bundle_with_token",
        lambda **_: (
            {
                "twin": {"id": "twin-1", "name": "pump-17"},
                "domain_context": {
                    "data_host": "group-a.data.iot.us-ashburn-1.oci.oraclecloud.com",
                    "domain_short_id": "factory-a",
                    "region": "us-ashburn-1",
                },
            },
            token,
        ),
        raising=False,
    )
    monkeypatch.setattr(agent_workflows, "list_snapshot_records", lambda **_: [])
    monkeypatch.setattr(agent_workflows, "list_historized_records", lambda **_: [{"id": "hist-1"}])
    monkeypatch.setattr(agent_workflows, "list_raw_command_records", lambda **_: [])
    monkeypatch.setattr(agent_workflows, "list_rejected_data_records", lambda **_: [])
    monkeypatch.setattr(
        agent_workflows,
        "require_token_credentials",
        lambda _env: {
            "ok": True,
            "data": {
                "present": [
                    "OCI_IOT_ORDS_CLIENT_ID",
                    "OCI_IOT_ORDS_CLIENT_SECRET",
                    "OCI_IOT_ORDS_USERNAME",
                    "OCI_IOT_ORDS_PASSWORD",
                ],
                "missing": [],
            },
        },
    )

    payload = agent_workflows.validate_twin_readiness_impl(digital_twin_instance_id="twin-1")

    assert payload["overall_status"] == "warning"
    assert any(
        check["name"] == "ords_credentials" and check["status"] == "ok"
        for check in payload["checks"]
    )
    assert any(
        check["name"] == "snapshot_read" and check["status"] == "warning"
        for check in payload["checks"]
    )
    assert any(
        check["name"] == "snapshot_read"
        and check["details"]["message"] == "No snapshot records found"
        for check in payload["checks"]
    )


def test_validate_twin_readiness_warns_when_indirect_twin_has_no_gateways(monkeypatch):
    agent_workflows = load_agent_workflows()
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-27T13:00:00Z",
        }
    )
    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_bundle_with_token",
        lambda **_: (
            {
                "twin": {
                    "id": "twin-1",
                    "name": "pump-17",
                    "connectivity_type": "INDIRECT",
                    "gateways": [],
                },
                "domain_context": {
                    "data_host": "group-a.data.iot.us-ashburn-1.oci.oraclecloud.com",
                    "domain_short_id": "factory-a",
                    "region": "us-ashburn-1",
                },
            },
            token,
        ),
        raising=False,
    )
    monkeypatch.setattr(
        agent_workflows,
        "require_token_credentials",
        lambda _env: {"ok": True, "data": {"present": [], "missing": []}},
    )
    monkeypatch.setattr(agent_workflows, "list_snapshot_records", lambda **_: [{"id": "snap-1"}])

    payload = agent_workflows.validate_twin_readiness_impl(digital_twin_instance_id="twin-1")

    assert payload["overall_status"] == "warning"
    assert any(
        check["name"] == "gateway_topology"
        and check["status"] == "warning"
        and check["details"]["message"] == "Indirect twin has no gateway references."
        for check in payload["checks"]
    )


def test_resolve_twin_bundle_returns_resolver_error(monkeypatch):
    agent_workflows = load_agent_workflows()

    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_for_tool",
        lambda **_: {
            "ok": False,
            "error": {"code": "not_found", "message": "Twin not found"},
        },
    )

    payload = agent_workflows.resolve_twin_bundle(digital_twin_instance_id="missing")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "not_found"


def test_resolve_twin_bundle_leaves_adapter_and_model_empty_when_absent(monkeypatch):
    agent_workflows = load_agent_workflows()

    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_for_tool",
        lambda **_: {
            "id": "twin-1",
            "name": "pump-17",
            "iot_domain_id": "domain-1",
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "get_iot_domain_record",
        lambda _id: {
            "id": "domain-1",
            "name": "factory-a",
            "iot_domain_group_id": "group-1",
            "device_host": "factory-a.iot.us-ashburn-1.oci.oraclecloud.com",
            "db_allowed_identity_domain_host": "idcs.example.com",
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "get_iot_domain_group_record",
        lambda _id: {
            "id": "group-1",
            "name": "factory-group",
            "data_host": "group-a.data.iot.us-ashburn-1.oci.oraclecloud.com",
        },
    )

    payload = agent_workflows.resolve_twin_bundle(digital_twin_instance_id="twin-1")

    assert payload["adapter"] is None
    assert payload["model"] is None


def test_resolve_twin_bundle_with_token_returns_credentials_error(monkeypatch):
    agent_workflows = load_agent_workflows()

    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_bundle",
        lambda **_: {"twin": {"id": "twin-1"}, "domain_context": {"domain_short_id": "factory-a"}},
    )
    monkeypatch.setattr(
        agent_workflows,
        "require_token_credentials",
        lambda _env: {
            "ok": False,
            "error": {"code": "missing_token_credentials"},
        },
    )

    payload = agent_workflows.resolve_twin_bundle_with_token(digital_twin_instance_id="twin-1")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "missing_token_credentials"


def test_resolve_twin_bundle_with_token_returns_bundle_and_token(monkeypatch):
    agent_workflows = load_agent_workflows()
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-27T13:00:00Z",
        }
    )

    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_bundle",
        lambda **_: {
            "twin": {"id": "twin-1"},
            "domain_context": {"domain_short_id": "factory-a"},
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "require_token_credentials",
        lambda _env: {"ok": True, "data": {"present": [], "missing": []}},
    )
    monkeypatch.setattr(agent_workflows, "get_cached_data_api_token", lambda **_: token)

    bundle, resolved_token = agent_workflows.resolve_twin_bundle_with_token(
        digital_twin_instance_id="twin-1"
    )

    assert bundle["twin"]["id"] == "twin-1"
    assert resolved_token.access_token == "token-123"


def test_resolve_twin_bundle_with_token_returns_structured_token_mint_error(monkeypatch):
    agent_workflows = load_agent_workflows()

    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_bundle",
        lambda **_: {
            "twin": {"id": "twin-1"},
            "domain_context": {"domain_short_id": "factory-a"},
        },
    )
    monkeypatch.setattr(
        agent_workflows,
        "require_token_credentials",
        lambda _env: {"ok": True, "data": {"present": [], "missing": []}},
    )
    monkeypatch.setattr(
        agent_workflows,
        "get_cached_data_api_token",
        lambda **_: (_ for _ in ()).throw(
            DataApiTokenError(
                code="missing_ords_configuration",
                message="IoT domain is not configured for ORDS token minting.",
                retry_hint="Configure ORDS data access for the IoT domain and retry.",
                details={"missing": ["db_allowed_identity_domain_host"]},
            )
        ),
    )

    payload = agent_workflows.resolve_twin_bundle_with_token(digital_twin_instance_id="twin-1")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "missing_ords_configuration"


def test_validate_twin_readiness_returns_resolution_error(monkeypatch):
    agent_workflows = load_agent_workflows()

    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_bundle_with_token",
        lambda **_: {
            "ok": False,
            "error": {"code": "ambiguous_identifier"},
        },
        raising=False,
    )

    payload = agent_workflows.validate_twin_readiness_impl(digital_twin_instance_id="twin-1")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "ambiguous_identifier"


def test_validate_twin_readiness_returns_credential_error(monkeypatch):
    agent_workflows = load_agent_workflows()
    token = DataApiTokenModel.model_validate(
        {
            "access_token": "token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": "2026-03-27T13:00:00Z",
        }
    )

    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_bundle_with_token",
        lambda **_: (
            {
                "twin": {"id": "twin-1", "name": "pump-17"},
                "domain_context": {
                    "data_host": "group-a.data.iot.us-ashburn-1.oci.oraclecloud.com",
                    "domain_short_id": "factory-a",
                    "region": "us-ashburn-1",
                },
            },
            token,
        ),
        raising=False,
    )
    monkeypatch.setattr(
        agent_workflows,
        "require_token_credentials",
        lambda _env: {
            "ok": False,
            "error": {"code": "missing_token_credentials"},
        },
    )

    payload = agent_workflows.validate_twin_readiness_impl(digital_twin_instance_id="twin-1")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "missing_token_credentials"


def test_get_latest_twin_state_returns_resolution_error(monkeypatch):
    agent_workflows = load_agent_workflows()

    monkeypatch.setattr(
        agent_workflows,
        "resolve_twin_bundle_with_token",
        lambda **_: {
            "ok": False,
            "error": {"code": "not_found"},
        },
        raising=False,
    )

    payload = agent_workflows.get_latest_twin_state_impl(digital_twin_instance_id="missing")

    assert payload["ok"] is False
    assert payload["error"]["code"] == "not_found"


def test_summarize_checks_reports_error_warning_and_ok():
    agent_workflows = load_agent_workflows()

    assert agent_workflows._summarize_checks([{"status": "error"}]) == "error"
    assert agent_workflows._summarize_checks([{"status": "warning"}]) == "warning"
    assert agent_workflows._summarize_checks([{"status": "ok"}]) == "ok"
    assert agent_workflows._build_check("snapshot_read", "ok") == {
        "name": "snapshot_read",
        "status": "ok",
        "details": {},
    }
