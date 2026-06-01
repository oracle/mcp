"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import inspect
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
import oracle.oci_recovery_mcp_server.models as models
import oracle.oci_recovery_mcp_server.server as server
from oracle.oci_recovery_mcp_server.server import mcp


def _response(data, *, has_next_page=False, next_page=None):
    return SimpleNamespace(
        data=data,
        has_next_page=has_next_page,
        next_page=next_page,
        status=200,
        headers={},
        request_id="request-id",
        opc_request_id="opc-request-id",
    )


def _raise(error):
    raise error


class TestGetClientFactories:
    @patch(
        "oracle.oci_recovery_mcp_server.server._wrap_oci_client",
        side_effect=lambda client, **_: client,
    )
    @patch("oracle.oci_recovery_mcp_server.server.oci.recovery.DatabaseRecoveryClient")
    @patch(
        "oracle.oci_recovery_mcp_server.server._effective_auth_method",
        return_value="apikey",
    )
    @patch("oracle.oci_recovery_mcp_server.server._load_oci_config_for_server")
    def test_get_recovery_client_apikey_passes_circuit_breaker(
        self,
        mock_load_config,
        _mock_auth_method,
        mock_client,
        _mock_wrap,
    ):
        mock_load_config.return_value = {"region": "us-ashburn-1"}

        result = server.get_recovery_client(region="us-phoenix-1", request_id="rid")

        args, kwargs = mock_client.call_args
        assert args[0]["region"] == "us-phoenix-1"
        assert "signer" not in kwargs
        assert isinstance(
            kwargs["circuit_breaker_strategy"],
            oci.circuit_breaker.CircuitBreakerStrategy,
        )
        assert callable(kwargs["circuit_breaker_callback"])
        assert result is mock_client.return_value

    @patch(
        "oracle.oci_recovery_mcp_server.server._wrap_oci_client",
        side_effect=lambda client, **_: client,
    )
    @patch("oracle.oci_recovery_mcp_server.server._build_signer_for_session")
    @patch("oracle.oci_recovery_mcp_server.server.oci.monitoring.MonitoringClient")
    @patch(
        "oracle.oci_recovery_mcp_server.server._effective_auth_method",
        return_value="session",
    )
    @patch("oracle.oci_recovery_mcp_server.server._load_oci_config_for_server")
    def test_get_monitoring_client_session_passes_circuit_breaker(
        self,
        mock_load_config,
        _mock_auth_method,
        mock_client,
        mock_build_signer,
        _mock_wrap,
    ):
        mock_load_config.return_value = {"region": "us-ashburn-1"}
        signer = object()
        mock_build_signer.return_value = signer

        result = server.get_monitoring_client(region="us-phoenix-1", request_id="rid")

        args, kwargs = mock_client.call_args
        assert args[0]["region"] == "us-phoenix-1"
        assert kwargs["signer"] is signer
        assert isinstance(
            kwargs["circuit_breaker_strategy"],
            oci.circuit_breaker.CircuitBreakerStrategy,
        )
        assert callable(kwargs["circuit_breaker_callback"])
        assert result is mock_client.return_value


def test_model_conversion_helpers_cover_fallback_paths(monkeypatch):
    assert models._oci_to_dict(None) is None
    assert models._first_not_none(None, False, "fallback") is False
    assert models._map_list([1, 2], lambda value: value * 2) == [2, 4]

    class BadIterable:
        def __iter__(self):
            raise RuntimeError("cannot iterate")

    assert models._map_list(BadIterable(), lambda value: value) is None

    def raising_to_dict(_sdk_obj):
        raise RuntimeError("conversion failed")

    monkeypatch.setattr(models.oci.util, "to_dict", raising_to_dict)

    class MinimalObject:
        def __init__(self):
            self.id = "obj1"
            self._private = "hidden"

    assert models._oci_to_dict({"id": "dict1"}) == {"id": "dict1"}
    assert models._oci_to_dict(MinimalObject()) == {"id": "obj1"}
    assert models._oci_to_dict(object()) is None


def test_generated_model_mappers_handle_none_and_sdk_conversion_fallback(monkeypatch):
    def raising_to_dict(_sdk_obj):
        raise RuntimeError("conversion failed")

    monkeypatch.setattr(models.oci.util, "to_dict", raising_to_dict)

    for mapper_name, mapper in inspect.getmembers(models, inspect.isfunction):
        if not mapper_name.startswith("map_"):
            continue

        assert mapper(None) is None, mapper_name
        mapped = mapper(SimpleNamespace())
        assert mapped is None or isinstance(mapped, models.OCIBaseModel), mapper_name


def test_model_mappers_capture_nested_and_variant_fields():
    rss = models.map_recovery_service_subnet(
        {
            "id": "rss1",
            "nsgIds": ("nsg1", "nsg2"),
            "subnets": [{"subnetId": "subnet1"}, {"id": "subnet2"}],
        }
    )
    assert rss.id == "rss1"
    assert rss.nsg_ids == ["nsg1", "nsg2"]
    assert rss.subnets == ["subnet1", "subnet2"]

    backup_config = models.map_db_backup_config(
        {
            "isAutoBackupEnabled": True,
            "backupDestinationDetails": [
                {
                    "destinationType": "OBJECT_STORE",
                    "bucketName": "bucket",
                    "customField": "preserved",
                }
            ],
        }
    )
    assert backup_config.is_auto_backup_enabled is True
    assert backup_config.backup_destination_details[0].type == "OBJECT_STORE"
    assert backup_config.backup_destination_details[0].extras == {
        "customField": "preserved"
    }

    metrics = models.map_metrics(
        {
            "backupSpaceUsedInGbs": 5.5,
            "isRedoLogsEnabled": False,
            "retentionPeriodInDays": 14,
        }
    )
    assert metrics.backup_space_used_in_gbs == 5.5
    assert metrics.is_redo_logs_enabled is False
    assert metrics.retention_period_in_days == 14

    work_request = models.map_work_request(
        {
            "id": "wr1",
            "compartmentId": "compartment",
            "operationType": "RESTORE_DATABASE",
            "percentComplete": 75.5,
            "resourceId": "db1",
        }
    )
    assert work_request.id == "wr1"
    assert work_request.operation_type == "RESTORE_DATABASE"
    assert work_request.percent_complete == 75.5
    assert work_request.resource_id == "db1"


def test_model_mappers_cover_unusual_iterables_and_attribute_sources(monkeypatch):
    class BadIterable:
        def __iter__(self):
            raise RuntimeError("cannot iterate")

    rss = models.map_recovery_service_subnet(
        {"id": "rss1", "nsgIds": BadIterable(), "subnets": BadIterable()}
    )
    assert rss.id == "rss1"
    assert rss.nsg_ids is None
    assert rss.subnets is None

    assert models.map_recovery_service_subnet_details("rss-id").id == "rss-id"
    assert (
        models.map_recovery_service_subnet_details(
            {"id": "rss-detail", "nsgIds": BadIterable()}
        ).nsg_ids
        is None
    )
    assert (
        models.map_recovery_service_subnet_input(
            {"displayName": "input", "nsgIds": BadIterable()}
        ).nsg_ids
        is None
    )
    assert (
        models.map_recovery_service_subnet_summary(
            {"id": "rss-summary", "nsgIds": BadIterable()}
        ).nsg_ids
        is None
    )

    class GetWithoutItems:
        def get(self, _key, default=None):
            return default

    monkeypatch.setattr(models, "_oci_to_dict", lambda _obj: GetWithoutItems())
    backup_destination = models.map_backup_destination_details(
        SimpleNamespace(type="NFS")
    )
    assert backup_destination.type == "NFS"
    assert backup_destination.extras is None
    backup_config = models.map_db_backup_config(
        SimpleNamespace(is_auto_backup_enabled=True)
    )
    assert backup_config.is_auto_backup_enabled is True
    assert backup_config.extras is None


def test_server_helpers_cover_serialization_config_and_wrapping(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "_LOG_MAX_VALUE_CHARS", 5)
    monkeypatch.setattr(
        server.oci.util,
        "to_dict",
        lambda _obj: _raise(RuntimeError("no SDK conversion")),
    )

    class DumpOnly:
        __slots__ = ()

        def model_dump(self, **_kwargs):
            return {"token": "secret", "value": "abcdef"}

    class DictOnly:
        __slots__ = ()

        def dict(self, **_kwargs):
            return {"private_key": "secret", "value": "ok"}

    class BadRepr:
        __slots__ = ()

        def __repr__(self):
            raise RuntimeError("bad repr")

    safe = server._safe_jsonable(
        {
            "access_token": "secret",
            "nested": ["abcdef"],
            "dump": DumpOnly(),
            "dict": DictOnly(),
            "object": SimpleNamespace(answer=42),
            "repr": object(),
        }
    )
    assert safe["access_token"] == "***REDACTED***"
    assert safe["nested"] == ["abcde...(truncated,len=6)"]
    assert safe["dump"]["token"] == "***REDACTED***"
    assert safe["dict"]["private_key"] == "***REDACTED***"
    assert safe["object"] == {"answer": 42}
    assert isinstance(safe["repr"], str)
    assert server._safe_jsonable(BadRepr()) == "<unserializable>"

    log_calls = []
    monkeypatch.setattr(
        server.logger,
        "log",
        lambda level, message: log_calls.append((level, message)),
    )
    server._log_event(
        "unit_event",
        request_id="rid",
        tool="tool",
        phase="phase",
        payload={"value": 1},
    )
    assert "unit_event" in log_calls[-1][1]

    monkeypatch.setattr(
        server.json,
        "dumps",
        lambda *_args, **_kwargs: _raise(TypeError("cannot encode")),
    )
    server._log_event("fallback_event", request_id="rid")
    assert "fallback_event" in log_calls[-1][1]

    wrapped_events = []
    monkeypatch.setattr(
        server,
        "_log_event",
        lambda event, **kwargs: wrapped_events.append((event, kwargs)),
    )
    inner = SimpleNamespace(
        value=3,
        successful=MagicMock(return_value=_response(SimpleNamespace(id="ok"))),
        failing=MagicMock(side_effect=RuntimeError("boom")),
    )
    wrapped = server._wrap_oci_client(inner, request_id="rid", client_name="database")
    assert wrapped.value == 3
    assert wrapped.successful("arg", key="value").data.id == "ok"
    with pytest.raises(RuntimeError, match="boom"):
        wrapped.failing()
    assert [kwargs["phase"] for _, kwargs in wrapped_events] == [
        "start",
        "end",
        "start",
        "error",
    ]

    monkeypatch.setenv("ORACLE_MCP_AUTH_METHOD", "api-key")
    assert server._effective_auth_method() == "apikey"
    monkeypatch.setenv("ORACLE_MCP_AUTH_METHOD", "session")
    assert server._effective_auth_method() == "session"
    monkeypatch.setenv("ORACLE_MCP_AUTH_PROFILE", "PROFILE1")
    assert server._effective_profile_name() == "PROFILE1"
    monkeypatch.delenv("ORACLE_MCP_AUTH_PROFILE", raising=False)
    monkeypatch.setenv("OCI_CONFIG_PROFILE", "PROFILE2")
    assert server._effective_profile_name() == "PROFILE2"

    monkeypatch.setattr(
        server.oci.config, "from_file", lambda profile_name: {"region": profile_name}
    )
    loaded = server._load_oci_config_for_server()
    assert loaded["region"] == "PROFILE2"
    assert loaded["additional_user_agent"].startswith("oci-recovery-mcp/")

    config_file = tmp_path / "oci_config"
    config_file.write_text(
        "[DEFAULT]\ntenancy=tenancy-default\n[PROFILE1]\nuser=user1\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OCI_CONFIG_FILE", str(config_file))
    monkeypatch.setenv("ORACLE_MCP_AUTH_PROFILE", "PROFILE1")
    assert server._get_profile_value("user") == "user1"
    assert server._get_profile_value("tenancy") == "tenancy-default"

    token_file = tmp_path / "security_token"
    token_file.write_text("SECURITY_TOKEN", encoding="utf-8")
    private_key = object()
    signer = object()
    monkeypatch.setattr(
        server.oci.signer,
        "load_private_key_from_file",
        lambda key_file: private_key if key_file == "key.pem" else None,
    )
    security_token_signer = MagicMock(return_value=signer)
    monkeypatch.setattr(
        server.oci.auth.signers,
        "SecurityTokenSigner",
        security_token_signer,
    )
    assert (
        server._build_signer_for_session(
            {"key_file": "key.pem", "security_token_file": str(token_file)}
        )
        is signer
    )
    security_token_signer.assert_called_once_with("SECURITY_TOKEN", private_key)

    kwargs_without_signer = server._get_oci_client_kwargs()
    kwargs_with_signer = server._get_oci_client_kwargs(signer=signer)
    assert "signer" not in kwargs_without_signer
    assert kwargs_with_signer["signer"] is signer
    assert callable(kwargs_with_signer["circuit_breaker_callback"])


def test_http_config_and_client_factories_cover_auth_paths(monkeypatch):
    for key in (
        "ORACLE_MCP_HOST",
        "ORACLE_MCP_PORT",
        "IDCS_DOMAIN",
        "IDCS_CLIENT_ID",
        "IDCS_CLIENT_SECRET",
        "OCI_REGION",
    ):
        monkeypatch.delenv(key, raising=False)

    assert server._get_http_config_and_signer() == (None, None)

    monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("ORACLE_MCP_PORT", "8080")
    monkeypatch.setattr(server, "get_access_token", lambda: None)
    with pytest.raises(RuntimeError, match="access token"):
        server._get_http_config_and_signer()

    monkeypatch.setattr(
        server, "get_access_token", lambda: SimpleNamespace(token="idcs-token")
    )
    with pytest.raises(RuntimeError, match="IDCS authentication"):
        server._get_http_config_and_signer()

    monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
    monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
    monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")
    with pytest.raises(RuntimeError, match="OCI_REGION"):
        server._get_http_config_and_signer()

    token_exchange_signer = MagicMock(return_value="http-signer")
    monkeypatch.setattr(
        server.oci.auth.signers, "TokenExchangeSigner", token_exchange_signer
    )
    config, signer = server._get_http_config_and_signer(region="us-phoenix-1")
    assert config["region"] == "us-phoenix-1"
    assert signer == "http-signer"
    token_exchange_signer.assert_called_once_with(
        "idcs-token",
        "https://idcs.example.com",
        "client-id",
        "client-secret",
        region="us-phoenix-1",
    )

    wrapped = object()
    monkeypatch.setattr(
        server,
        "_wrap_oci_client",
        lambda client, **kwargs: (wrapped, client, kwargs["client_name"]),
    )
    monkeypatch.setattr(
        server,
        "_get_http_config_and_signer",
        lambda region=None: ({"region": region or "home"}, signer),
    )

    recovery_client = MagicMock(return_value="recovery-client")
    database_client = MagicMock(return_value="database-client")
    identity_client = MagicMock(return_value="identity-client")
    monitoring_client = MagicMock(return_value="monitoring-client")
    monkeypatch.setattr(server.oci.recovery, "DatabaseRecoveryClient", recovery_client)
    monkeypatch.setattr(server.oci.database, "DatabaseClient", database_client)
    monkeypatch.setattr(server.oci.identity, "IdentityClient", identity_client)
    monkeypatch.setattr(server.oci.monitoring, "MonitoringClient", monitoring_client)

    assert server.get_recovery_client(region="us-ashburn-1")[2] == "recovery"
    assert server.get_database_client(region="us-ashburn-1")[2] == "database"
    assert server.get_identity_client()[2] == "identity"
    assert server.get_monitoring_client(region="us-ashburn-1")[2] == "monitoring"
    assert recovery_client.call_args.kwargs["signer"] == signer
    assert database_client.call_args.kwargs["signer"] == signer
    assert identity_client.call_args.kwargs["signer"] == signer
    assert monitoring_client.call_args.kwargs["signer"] == signer

    monkeypatch.setattr(
        server, "_get_http_config_and_signer", lambda region=None: (None, None)
    )
    monkeypatch.setattr(
        server, "_load_oci_config_for_server", lambda: {"region": "home"}
    )
    monkeypatch.setattr(server, "_effective_auth_method", lambda: "session")
    monkeypatch.setattr(
        server, "_build_signer_for_session", lambda config: "session-signer"
    )
    assert server.get_identity_client()[2] == "identity"
    assert server.get_database_client(region="us-chicago-1")[2] == "database"
    assert identity_client.call_args.kwargs["signer"] == "session-signer"
    assert database_client.call_args.kwargs["signer"] == "session-signer"


def test_new_client_factories_cover_limits_work_requests_and_subscription(monkeypatch):
    monkeypatch.setattr(
        server,
        "_get_http_config_and_signer",
        lambda region=None: (None, None),
    )
    monkeypatch.setattr(
        server,
        "_load_oci_config_for_server",
        lambda: {"region": "home-region"},
    )
    monkeypatch.setattr(server, "_effective_auth_method", lambda: "apikey")
    monkeypatch.setattr(
        server,
        "_wrap_oci_client",
        lambda client, **kwargs: (client, kwargs["client_name"]),
    )

    limits_client = MagicMock(return_value="limits-client")
    work_request_client = MagicMock(return_value="work-request-client")
    subscribed_service_client = MagicMock(return_value="subscription-client")
    monkeypatch.setattr(server.oci.limits, "LimitsClient", limits_client)
    monkeypatch.setattr(
        server.oci.work_requests, "WorkRequestClient", work_request_client
    )
    monkeypatch.setattr(
        server.oci.onesubscription,
        "SubscribedServiceClient",
        subscribed_service_client,
    )

    assert server.get_limits_client(region="us-phoenix-1")[1] == "limits"
    assert (
        server.get_work_request_client(region="us-chicago-1")[1] == "work_requests"
    )
    assert (
        server.get_onesubscription_client(region="us-ashburn-1")[1]
        == "onesubscription"
    )
    assert limits_client.call_args.args[0]["region"] == "us-phoenix-1"
    assert work_request_client.call_args.args[0]["region"] == "us-chicago-1"
    assert subscribed_service_client.call_args.args[0]["region"] == "us-ashburn-1"
    assert "signer" not in limits_client.call_args.kwargs

    monkeypatch.setattr(server, "_effective_auth_method", lambda: "session")
    monkeypatch.setattr(
        server, "_build_signer_for_session", lambda _config: "session-signer"
    )
    assert server.get_limits_client()[1] == "limits"
    assert limits_client.call_args.kwargs["signer"] == "session-signer"

    http_signer = object()
    monkeypatch.setattr(
        server,
        "_get_http_config_and_signer",
        lambda region=None: ({"region": region or "home-region"}, http_signer),
    )
    assert server.get_work_request_client(region="us-sanjose-1")[1] == "work_requests"
    assert server.get_limits_client(region="us-sanjose-1")[1] == "limits"
    assert (
        server.get_onesubscription_client(region="us-sanjose-1")[1]
        == "onesubscription"
    )
    assert work_request_client.call_args.kwargs["signer"] is http_signer
    assert limits_client.call_args.kwargs["signer"] is http_signer
    assert subscribed_service_client.call_args.kwargs["signer"] is http_signer


def test_compartment_and_database_home_helpers_cover_resolution(monkeypatch):
    compartments = [
        SimpleNamespace(id="compartment-a", name="Dev"),
        SimpleNamespace(id="compartment-b", name="Prod"),
    ]
    root = SimpleNamespace(id="tenancy", name="Root")
    identity_client = MagicMock()
    identity_client.list_compartments.side_effect = [
        _response([compartments[0]], has_next_page=True, next_page="next"),
        _response([compartments[1]]),
    ]
    identity_client.get_compartment.return_value = _response(root)
    monkeypatch.setattr(server, "get_identity_client", lambda: identity_client)
    monkeypatch.setattr(server, "get_tenancy", lambda: "tenancy")

    assert server.list_all_compartments_internal(True, limit=25) == [
        compartments[0],
        root,
    ]
    identity_client.list_compartments.reset_mock()
    identity_client.list_compartments.side_effect = [
        _response([compartments[0]], has_next_page=True, next_page="next"),
        _response([compartments[1]]),
    ]
    all_compartments = server.list_all_compartments_internal(False, limit=25)
    assert [compartment.id for compartment in all_compartments] == [
        "compartment-a",
        "tenancy",
        "compartment-b",
    ]

    monkeypatch.setattr(
        server,
        "list_all_compartments_internal",
        lambda _only_one_page: compartments + [root],
    )
    assert server.get_compartment_by_name("prod").id == "compartment-b"
    assert server.get_compartment_by_name("missing") is None
    assert server._looks_like_ocid(" ocid1.compartment.oc1..abc ")
    assert not server._looks_like_ocid("Dev")
    assert server._resolve_compartment_id("ocid1.compartment.oc1..abc") == (
        "ocid1.compartment.oc1..abc"
    )
    assert server._resolve_compartment_id("Dev") == "compartment-a"
    assert server._resolve_compartment_id(None, default_to_tenancy=True) == "tenancy"
    with pytest.raises(ValueError, match="required"):
        server._resolve_compartment_id(None)
    with pytest.raises(ValueError, match="cannot be empty"):
        server._resolve_compartment_id(" ")
    with pytest.raises(ValueError, match="not found"):
        server._resolve_compartment_id("Missing")
    monkeypatch.setattr(
        server, "get_compartment_by_name", lambda _name: SimpleNamespace(name="NoId")
    )
    with pytest.raises(ValueError, match="Unable to resolve"):
        server._resolve_compartment_id("NoId")

    db_client = MagicMock()
    db_client.list_db_homes.return_value = _response(
        SimpleNamespace(
            items=[
                SimpleNamespace(id="home1"),
                {"id": "home2"},
                SimpleNamespace(display_name="missing-id"),
            ]
        )
    )
    monkeypatch.setattr(server, "get_database_client", lambda region=None: db_client)
    assert server._fetch_db_home_ids_for_compartment("compartment-a") == [
        "home1",
        "home2",
    ]
    db_client.list_db_homes.side_effect = RuntimeError("service unavailable")
    assert server._fetch_db_home_ids_for_compartment("compartment-a") == []


def test_region_subscription_and_limit_tools_cover_current_contracts(monkeypatch):
    region_cache = {"fetched_at": 0.0, "ttl_seconds": 3600, "items": {}}
    monkeypatch.setattr(server, "_REGION_CACHE", region_cache)
    monkeypatch.setattr(server, "get_tenancy", lambda: "tenancy")

    identity_client = MagicMock()
    identity_client.list_region_subscriptions.return_value = _response(
        [
            SimpleNamespace(region_name="us-phoenix-1", status="READY"),
            SimpleNamespace(regionName="us-ashburn-1", status="READY"),
            SimpleNamespace(status="IGNORED"),
        ]
    )
    monkeypatch.setattr(
        server, "get_identity_client", lambda request_id=None: identity_client
    )

    regions = server._iam_subscribed_regions_with_status(request_id="rid")
    assert regions == [
        {"region": "us-ashburn-1", "status": "READY"},
        {"region": "us-phoenix-1", "status": "READY"},
    ]
    assert server._iam_subscribed_regions_with_status(request_id="rid2") == regions
    identity_client.list_region_subscriptions.assert_called_once_with(
        tenancy_id="tenancy"
    )
    assert server.fetch_regions_subscribed()["total"] == 2

    limits_client = MagicMock()
    monkeypatch.setattr(
        server.oci.util,
        "to_dict",
        lambda _obj: _raise(RuntimeError("no SDK conversion")),
    )
    limits_client.get_resource_availability.side_effect = [
        _response(
            SimpleNamespace(
                scope_type="REGION",
                available=90,
                used=10,
                fractional_availability=0.9,
                fractional_usage=0.1,
                effective_quota_value=100,
                policy_name="storage-policy",
            )
        ),
        _response(
            {
                "scope_type": "AD",
                "available": 4,
                "used": 1,
                "fractional_availability": 0.8,
                "fractional_usage": 0.2,
                "effective_quota_value": 5,
                "policy_name": "count-policy",
            }
        ),
    ]
    monkeypatch.setattr(
        server,
        "_load_oci_config_for_server",
        lambda: {"region": "us-phoenix-1"},
    )
    monkeypatch.setattr(
        server,
        "get_limits_client",
        lambda region, request_id=None: limits_client,
    )

    limits = server.check_recovery_service_limits(
        compartment_id="ignored",
        region="ignored",
        opc_request_id="opc",
    )
    assert limits["compartmentId"] == "tenancy"
    assert limits["region"] == "us-phoenix-1"
    assert limits["limits"]["protectedDatabaseBackupStorageGb"]["available"] == 90
    assert limits["limits"]["protectedDatabaseCount"]["policyName"] == "count-policy"
    assert [
        call.kwargs["limit_name"]
        for call in limits_client.get_resource_availability.call_args_list
    ] == [
        "protected-database-backup-storage-gb",
        "protected-database-count",
    ]
    assert all(
        call.kwargs["opc_request_id"] == "opc"
        for call in limits_client.get_resource_availability.call_args_list
    )


def test_child_compartment_helpers_cover_cache_fast_path_and_fallback(monkeypatch):
    monkeypatch.setattr(
        server,
        "_COMPARTMENT_CACHE",
        {"fetched_at": 0.0, "ttl_seconds": 300, "items": None},
    )
    monkeypatch.setattr(server.time, "time", lambda: 100.0)
    monkeypatch.setattr(server, "get_tenancy", lambda: "tenancy")
    monkeypatch.setattr(
        server,
        "list_all_compartments_internal",
        lambda _only_one_page: [
            SimpleNamespace(id="child", compartment_id="tenancy"),
            SimpleNamespace(id="child", compartment_id="tenancy"),
            SimpleNamespace(name="missing id"),
        ],
    )
    identity_client = MagicMock()
    identity_client.get_compartment.return_value = _response(
        SimpleNamespace(id="tenancy", name="Root")
    )
    monkeypatch.setattr(
        server, "get_identity_client", lambda request_id=None: identity_client
    )

    cached = server._list_all_compartments_cached(request_id="rid")
    assert [compartment.id for compartment in cached] == ["child", "tenancy"]
    assert server._list_all_compartments_cached(request_id="rid2") is cached

    compartments = [
        SimpleNamespace(id="root", compartment_id="tenancy"),
        SimpleNamespace(id="child", compartment_id="root"),
        SimpleNamespace(id="grandchild", compartmentId="child"),
        SimpleNamespace(id="orphan"),
    ]
    assert server._build_children_index(compartments) == {
        "tenancy": ["root"],
        "root": ["child"],
        "child": ["grandchild"],
    }
    monkeypatch.setattr(
        server,
        "_list_all_compartments_cached",
        lambda request_id=None: compartments,
    )
    assert server._expand_compartment_scope(
        "root", include_child_compartments=True
    ) == ["root", "child", "grandchild"]
    assert server._expand_compartment_scope(
        "root", include_child_compartments=False
    ) == ["root"]

    fallback_identity = MagicMock()
    fallback_identity.list_compartments.side_effect = [
        _response([SimpleNamespace(id="child")], has_next_page=True, next_page="p2"),
        _response([SimpleNamespace(id="sibling")]),
        _response([]),
        _response([]),
    ]
    monkeypatch.setattr(server, "_list_all_compartments_cached", lambda **_: [])
    monkeypatch.setattr(
        server, "get_identity_client", lambda request_id=None: fallback_identity
    )
    assert server._expand_compartment_scope(
        "root", include_child_compartments=True
    ) == ["root", "child", "sibling"]

    monkeypatch.setattr(
        server, "_resolve_compartment_id", lambda value, **_kwargs: f"resolved-{value}"
    )
    monkeypatch.setattr(
        server,
        "_expand_compartment_scope",
        MagicMock(side_effect=RuntimeError("identity unavailable")),
    )
    assert server._compartment_ids_for_tool(
        "Dev", fetch_for_child_compartment=True
    ) == ["resolved-Dev"]


def test_fetch_child_compartments_crawls_and_applies_output_options(monkeypatch):
    identity_client = MagicMock()
    identity_client.list_compartments.side_effect = [
        _response([SimpleNamespace(id="child")]),
        _response([]),
    ]
    monkeypatch.setattr(
        server,
        "_resolve_compartment_id",
        lambda compartment_id: f"resolved-{compartment_id}",
    )
    monkeypatch.setattr(
        server,
        "_expand_compartment_scope",
        lambda *_args, **_kwargs: ["resolved-Root"],
    )
    monkeypatch.setattr(
        server, "get_identity_client", lambda request_id=None: identity_client
    )

    result = server.fetch_child_compartments("Root", include_self=False)
    assert result == {
        "rootCompartmentId": "resolved-Root",
        "total": 1,
        "compartmentIds": ["child"],
    }

    monkeypatch.setattr(
        server,
        "_expand_compartment_scope",
        lambda *_args, **_kwargs: ["resolved-Root", "child", "grandchild"],
    )
    result = server.fetch_child_compartments("Root", include_self=True, limit=2)
    assert result["compartmentIds"] == ["resolved-Root", "child"]


class TestRecoveryTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_list_protected_databases(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock list response with a single ProtectedDatabaseSummary
        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.recovery.models.ProtectedDatabaseSummary(
                id="pd1",
                display_name="Protected DB 1",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_protected_databases.return_value = mock_list_response
        # attach metrics at summary level to ensure fallback path covers
        mock_list_response.data[0].metrics = {"backup_space_used_in_gbs": 10.5}

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_protected_databases",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "pd1"
            assert result[0]["display_name"] == "Protected DB 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_get_protected_database(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock get response with a ProtectedDatabase
        mock_get_response = create_autospec(oci.response.Response)
        pd = oci.recovery.models.ProtectedDatabase(
            id="pd1",
            display_name="Protected DB 1",
            lifecycle_state="ACTIVE",
            health="PROTECTED",
        )
        # attach minimal metrics for mapping tolerance
        pd.metrics = {"backup_space_used_in_gbs": 12.5}
        mock_get_response.data = pd
        mock_client.get_protected_database.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_protected_database", {"protected_database_id": "pd1"}
            )
            result = call_tool_result.structured_content

            assert result["id"] == "pd1"
            assert result["health"] == "PROTECTED"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_list_protection_policies(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.recovery.models.ProtectionPolicySummary(
                id="pp1",
                display_name="Policy 1",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_protection_policies.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_protection_policies",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "pp1"
            assert result[0]["display_name"] == "Policy 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_get_protection_policy(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.recovery.models.ProtectionPolicy(
            id="pp1",
            display_name="Policy 1",
            lifecycle_state="ACTIVE",
        )
        mock_client.get_protection_policy.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_protection_policy", {"protection_policy_id": "pp1"}
            )
            result = call_tool_result.structured_content

            assert result["id"] == "pp1"
            assert result["display_name"] == "Policy 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_list_recovery_service_subnets(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.recovery.models.RecoveryServiceSubnetSummary(
                id="rss1",
                display_name="RSS 1",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_recovery_service_subnets.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_recovery_service_subnets",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "rss1"
            assert result[0]["display_name"] == "RSS 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_get_recovery_service_subnet(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.recovery.models.RecoveryServiceSubnet(
            id="rss1",
            display_name="RSS 1",
            lifecycle_state="ACTIVE",
        )
        mock_client.get_recovery_service_subnet.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_recovery_service_subnet", {"recovery_service_subnet_id": "rss1"}
            )
            result = call_tool_result.structured_content

            assert result["id"] == "rss1"
            assert result["display_name"] == "RSS 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_summarize_protected_database_health(
        self, mock_get_client, mock_get_tenancy
    ):
        mock_get_tenancy.return_value = "ocid1.compartment.oc1..test"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # list two PDs
        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.recovery.models.ProtectedDatabaseSummary(id="pd1"),
            oci.recovery.models.ProtectedDatabaseSummary(id="pd2"),
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_protected_databases.return_value = mock_list_response

        # get each with different health
        mock_get_pd_resp1 = create_autospec(oci.response.Response)
        mock_get_pd_resp1.data = oci.recovery.models.ProtectedDatabase(
            id="pd1", health="PROTECTED"
        )
        mock_get_pd_resp2 = create_autospec(oci.response.Response)
        mock_get_pd_resp2.data = oci.recovery.models.ProtectedDatabase(
            id="pd2", health="WARNING"
        )
        mock_client.get_protected_database.side_effect = [
            mock_get_pd_resp1,
            mock_get_pd_resp2,
        ]

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "summarize_protected_database_health",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content

            aggregated = result["aggregated"]
            assert aggregated["protected"] == 1
            assert aggregated["warning"] == 1
            assert aggregated["alert"] == 0
            assert aggregated["total"] == 2
            assert result["compartmentIdsScanned"] == ["ocid1.compartment.oc1..test"]
            assert result["per_compartment"][0]["warning"] == 1

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_summarize_protected_database_redo_status(
        self, mock_get_client, mock_get_tenancy
    ):
        mock_get_tenancy.return_value = "ocid1.compartment.oc1..test"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.recovery.models.ProtectedDatabaseSummary(id="pd1"),
            oci.recovery.models.ProtectedDatabaseSummary(id="pd2"),
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_protected_databases.return_value = mock_list_response

        # get PDs with redo shipped enabled/disabled
        pd1 = oci.recovery.models.ProtectedDatabase(id="pd1")
        pd1.is_redo_logs_shipped = True
        pd2 = oci.recovery.models.ProtectedDatabase(id="pd2")
        pd2.is_redo_logs_shipped = False
        mock_get_pd_resp1 = create_autospec(oci.response.Response)
        mock_get_pd_resp1.data = pd1
        mock_get_pd_resp2 = create_autospec(oci.response.Response)
        mock_get_pd_resp2.data = pd2
        mock_client.get_protected_database.side_effect = [
            mock_get_pd_resp1,
            mock_get_pd_resp2,
        ]

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "summarize_protected_database_redo_status",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content

            aggregated = result["aggregated"]
            assert aggregated["enabled"] == 1
            assert aggregated["disabled"] == 1
            assert aggregated["total"] == 2
            assert result["compartmentIdsScanned"] == ["ocid1.compartment.oc1..test"]
            assert result["per_compartment"][0]["enabled"] == 1

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.server.get_recovery_client")
    async def test_summarize_backup_space_used(self, mock_get_client, mock_get_tenancy):
        mock_get_tenancy.return_value = "ocid1.compartment.oc1..test"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        pd1_summary = oci.recovery.models.ProtectedDatabaseSummary(
            id="pd1", lifecycle_state="ACTIVE"
        )
        pd2_summary = oci.recovery.models.ProtectedDatabaseSummary(
            id="pd2", lifecycle_state="ACTIVE"
        )
        mock_list_response.data = [pd1_summary, pd2_summary]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_protected_databases.return_value = mock_list_response
        # Fallback path for metrics at summary level
        pd1_summary.metrics = {"backup_space_used_in_gbs": 10.5}
        pd2_summary.metrics = {"backup_space_used_in_gbs": 4.5}

        # PD1 metrics 10.5 GB, PD2 metrics 4.5 GB
        pd1 = oci.recovery.models.ProtectedDatabase(id="pd1")
        pd1.metrics = {"backup_space_used_in_gbs": 10.5}
        pd2 = oci.recovery.models.ProtectedDatabase(id="pd2")
        pd2.metrics = {"backup_space_used_in_gbs": 4.5}

        mock_get_pd_resp1 = create_autospec(oci.response.Response)
        mock_get_pd_resp1.data = pd1
        mock_get_pd_resp2 = create_autospec(oci.response.Response)
        mock_get_pd_resp2.data = pd2
        mock_client.get_protected_database.side_effect = [
            mock_get_pd_resp1,
            mock_get_pd_resp2,
        ]

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "summarize_backup_space_used",
                {
                    "compartment_id": "ocid1.compartment.oc1..test",
                    "region": "us-ashburn-1",
                },
            )
            result = call_tool_result.structured_content

        aggregated = result["aggregated"]
        total_scanned = aggregated.get("total_databases_scanned") or aggregated.get(
            "totalDatabasesScanned"
        )
        sum_gb = aggregated.get("sum_backup_space_used_in_gbs") or aggregated.get(
            "sumBackupSpaceUsedInGBs"
        )
        assert abs(sum_gb - 15.0) < 1e-9
        assert total_scanned == 2
        assert result["missingMetricsCount"] == 0

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.server.get_monitoring_client")
    async def test_get_recovery_service_metrics(self, mock_get_monitoring_client):
        mock_client = MagicMock()
        mock_get_monitoring_client.return_value = mock_client

        # Prepare a fake series with aggregated datapoints
        dp1 = SimpleNamespace(timestamp="2024-01-01T00:00:00Z", value=1.0)
        dp2 = SimpleNamespace(timestamp="2024-01-01T00:01:00Z", value=2.0)
        series = SimpleNamespace(
            dimensions={"resourceId": "pd1"}, aggregated_datapoints=[dp1, dp2]
        )

        mock_metrics_response = create_autospec(oci.response.Response)
        mock_metrics_response.data = [series]
        mock_client.summarize_metrics_data.return_value = mock_metrics_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_recovery_service_metrics",
                {
                    "compartment_id": "ocid1.compartment.oc1..test",
                    "start_time": "2024-01-01T00:00:00Z",
                    "end_time": "2024-01-01T00:05:00Z",
                    "metricName": "SpaceUsedForRecoveryWindow",
                    "resolution": "1m",
                    "aggregation": "mean",
                    "protected_database_id": "pd1",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["dimensions"]["resourceId"] == "pd1"
            assert len(result[0]["datapoints"]) == 2
            assert result[0]["datapoints"][0]["value"] == 1.0


def test_child_scope_tools_cover_dedup_and_filter_kwargs(monkeypatch):
    recovery_client = MagicMock()
    monitoring_client = MagicMock()
    work_request_client = MagicMock()
    monkeypatch.setattr(
        models.oci.util,
        "to_dict",
        lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
    )
    monkeypatch.setattr(
        server,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        server,
        "get_monitoring_client",
        lambda request_id=None: monitoring_client,
    )
    monkeypatch.setattr(
        server,
        "get_work_request_client",
        lambda region=None, request_id=None: work_request_client,
    )
    monkeypatch.setattr(
        server,
        "_compartment_ids_for_tool",
        lambda compartment_id, fetch_for_child_compartment, request_id=None: [
            "compartment-a",
            "compartment-b",
        ],
    )

    recovery_client.list_protected_databases.side_effect = [
        _response([SimpleNamespace(id="pd1", display_name="PD 1")]),
        _response([SimpleNamespace(id="pd1", display_name="PD 1 duplicate")]),
    ]
    recovery_client.get_protected_database.return_value = _response(
        SimpleNamespace(
            metrics=SimpleNamespace(backup_space_used_in_gbs=1.5),
            is_redo_logs_shipped=True,
        )
    )
    protected_databases = server.list_protected_databases(
        "root", fetch_for_child_compartment=True
    )
    assert [pd["id"] for pd in protected_databases] == ["pd1"]

    recovery_client.list_protection_policies.side_effect = [
        _response([SimpleNamespace(id="policy1")]),
        _response([SimpleNamespace(id="policy1"), SimpleNamespace(id="policy2")]),
    ]
    policies = server.list_protection_policies(
        "root", fetch_for_child_compartment=True
    )
    assert [policy.id for policy in policies] == ["policy1", "policy2"]

    recovery_client.list_recovery_service_subnets.side_effect = [
        _response([SimpleNamespace(id="rss1", subnet_id="subnet1")]),
        _response([SimpleNamespace(id="rss1"), SimpleNamespace(id="rss2")]),
    ]
    recovery_client.get_recovery_service_subnet.side_effect = RuntimeError(
        "optional full lookup failed"
    )
    subnets = server.list_recovery_service_subnets(
        "root", fetch_for_child_compartment=True
    )
    assert [subnet.id for subnet in subnets] == ["rss1", "rss2"]
    assert subnets[0].subnets == ["subnet1"]

    series_a = SimpleNamespace(
        dimensions={"resourceId": "pd1"},
        aggregated_datapoints=[SimpleNamespace(timestamp="t1", value=1)],
    )
    series_b = SimpleNamespace(
        dimensions={"resourceId": "pd2"},
        aggregated_datapoints=[SimpleNamespace(timestamp="t2", value=2)],
    )
    monitoring_client.summarize_metrics_data.side_effect = [
        _response([series_a]),
        _response([series_b]),
    ]
    metrics = server.get_recovery_service_metrics(
        compartment_id="root",
        start_time="2024-01-01T00:00:00Z",
        end_time="2024-01-01T01:00:00Z",
        fetch_for_child_compartment=True,
        metricName="DataLossExposure",
        resolution="5m",
        aggregation="sum",
        protected_database_id="pd1",
    )
    assert [item["compartmentId"] for item in metrics] == [
        "compartment-a",
        "compartment-b",
    ]
    details = monitoring_client.summarize_metrics_data.call_args_list[0].kwargs[
        "summarize_metrics_data_details"
    ]
    assert details.query == 'DataLossExposure[5m]{resourceId="pd1"}.sum()'

    work_request_client.list_work_requests.side_effect = [
        _response(
            SimpleNamespace(
                items=[
                    {
                        "id": "wr1",
                        "operationType": "RESTORE_DATABASE",
                        "status": "IN_PROGRESS",
                    },
                    {"id": "skip", "operationType": "Create Backup"},
                ]
            ),
            has_next_page=True,
            next_page="wr-page-2",
        ),
        _response([{"id": "wr1", "operation_type": "Restore Database"}]),
        _response([{"id": "wr2", "operation_type": "restore-database"}]),
    ]
    restore_requests = server.list_restore(
        "root",
        fetch_for_child_compartment=True,
        resource_id="db1",
        status="IN_PROGRESS",
        limit=2,
        page="wr-page-1",
        sort_order="DESC",
        sort_by="timeAccepted",
        opc_request_id="opc",
        region="us-ashburn-1",
    )
    assert [request.id for request in restore_requests] == ["wr1", "wr2"]
    first_restore_call = work_request_client.list_work_requests.call_args_list[0].kwargs
    assert first_restore_call == {
        "compartment_id": "compartment-a",
        "resource_id": "db1",
        "status": "IN_PROGRESS",
        "sort_order": "DESC",
        "sort_by": "timeAccepted",
        "opc_request_id": "opc",
        "limit": 2,
        "page": "wr-page-1",
    }
    assert (
        work_request_client.list_work_requests.call_args_list[1].kwargs["page"]
        == "wr-page-2"
    )


def test_recovery_resource_tools_cover_filters_pagination_and_enrichment(monkeypatch):
    recovery_client = MagicMock()
    monkeypatch.setattr(
        models.oci.util,
        "to_dict",
        lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
    )
    monkeypatch.setattr(
        server,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        server,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: f"resolved-{compartment_id}",
    )

    recovery_client.list_protected_databases.side_effect = [
        _response(
            [
                SimpleNamespace(
                    id="pd1",
                    display_name="Protected 1",
                    lifecycle_state="ACTIVE",
                    recovery_service_subnets=[SimpleNamespace(id="rss1")],
                )
            ],
            has_next_page=True,
            next_page="page-2",
        ),
        _response(
            SimpleNamespace(
                items=[
                    SimpleNamespace(
                        id="pd2",
                        display_name="Protected 2",
                        lifecycle_state="ACTIVE",
                    )
                ]
            )
        ),
    ]
    recovery_client.get_recovery_service_subnet.return_value = _response(
        SimpleNamespace(
            id="rss1",
            display_name="Subnet 1",
            compartment_id="compartment",
            vcn_id="vcn",
            subnet_id="subnet",
            lifecycle_details="drop-me",
        )
    )
    recovery_client.get_protected_database.side_effect = [
        _response(
            SimpleNamespace(
                metrics=SimpleNamespace(
                    backup_space_used_in_gbs=9.5,
                    database_size_in_gbs=42,
                    is_redo_logs_enabled=True,
                )
            )
        ),
        _response(SimpleNamespace(metrics={"backupSpaceUsedInGbs": 2.5})),
    ]

    protected_databases = server.list_protected_databases(
        compartment_id="compartment",
        lifecycle_state="ACTIVE",
        display_name="Protected 1",
        id="pd1",
        protection_policy_id="policy1",
        recovery_service_subnet_id="rss1",
        limit=1,
        page="page-1",
        sort_order="ASC",
        sort_by="displayName",
        opc_request_id="opc",
        region="us-ashburn-1",
    )

    assert [item["id"] for item in protected_databases] == ["pd1", "pd2"]
    assert protected_databases[0]["recovery_service_subnets"][0]["vcn_id"] == "vcn"
    assert (
        "lifecycle_details" not in protected_databases[0]["recovery_service_subnets"][0]
    )
    assert protected_databases[0]["metrics"]["backup-space-used-in-gbs"] == 9.5
    assert recovery_client.list_protected_databases.call_args_list[0].kwargs == {
        "compartment_id": "resolved-compartment",
        "page": "page-1",
        "lifecycle_state": "ACTIVE",
        "display_name": "Protected 1",
        "id": "pd1",
        "protection_policy_id": "policy1",
        "recovery_service_subnet_id": "rss1",
        "limit": 1,
        "sort_order": "ASC",
        "sort_by": "displayName",
        "opc_request_id": "opc",
    }
    assert (
        recovery_client.list_protected_databases.call_args_list[1].kwargs["page"]
        == "page-2"
    )

    recovery_client.get_protected_database.side_effect = None
    recovery_client.get_protected_database.return_value = _response(
        SimpleNamespace(
            id="pd3",
            display_name="Protected 3",
            change_rate=1.2,
            compression_ratio=3.4,
            recovery_service_subnets=[SimpleNamespace(id="rss2")],
            metrics=SimpleNamespace(
                backup_space_used_in_gbs=7,
                database_size_in_gbs=70,
                is_redo_logs_enabled=False,
            ),
        )
    )
    recovery_client.get_recovery_service_subnet.return_value = _response(
        SimpleNamespace(
            id="rss2",
            display_name="Subnet 2",
            compartment_id="compartment",
            vcn_id="vcn2",
            subnet_id="subnet2",
            freeform_tags={"drop": "me"},
        )
    )

    protected_database = server.get_protected_database(
        "pd3", opc_request_id="opc", region="us-ashburn-1"
    )
    assert protected_database["id"] == "pd3"
    assert "change_rate" not in protected_database
    assert protected_database["recovery_service_subnets"][0]["subnet_id"] == "subnet2"
    assert "freeform_tags" not in protected_database["recovery_service_subnets"][0]
    assert protected_database["metrics"]["db-size-in-gbs"] == 70

    recovery_client.list_protection_policies.side_effect = [
        _response(
            [SimpleNamespace(id="policy1", display_name="Policy 1")],
            has_next_page=True,
            next_page="next-policy",
        ),
        _response(SimpleNamespace(items=[SimpleNamespace(id="policy2")])),
    ]
    policies = server.list_protection_policies(
        "compartment",
        lifecycle_state="ACTIVE",
        display_name="Policy 1",
        id="policy1",
        limit=5,
        page="first",
        sort_order="DESC",
        sort_by="timeCreated",
        opc_request_id="opc",
        region="us-ashburn-1",
    )
    assert [policy.id for policy in policies] == ["policy1", "policy2"]
    assert (
        recovery_client.list_protection_policies.call_args_list[0].kwargs["limit"] == 5
    )

    recovery_client.get_protection_policy.return_value = _response(
        SimpleNamespace(id="policy1", display_name="Policy 1")
    )
    assert server.get_protection_policy("policy1", opc_request_id="opc").id == "policy1"

    recovery_client.list_recovery_service_subnets.return_value = _response(
        [
            SimpleNamespace(id="rss-list-1", display_name="RSS 1"),
            SimpleNamespace(
                id="rss-list-2", display_name="RSS 2", subnet_id="subnet-fallback"
            ),
        ]
    )
    recovery_client.get_recovery_service_subnet.side_effect = [
        _response(
            SimpleNamespace(
                id="rss-list-1",
                display_name="RSS 1",
                subnets=["subnet-full"],
            )
        ),
        RuntimeError("full subnet lookup failed"),
    ]
    subnets = server.list_recovery_service_subnets(
        "compartment",
        lifecycle_state="ACTIVE",
        display_name="RSS 1",
        id="rss-list-1",
        vcn_id="vcn",
        limit=2,
        page="page",
        sort_order="ASC",
        sort_by="displayName",
        opc_request_id="opc",
        region="us-ashburn-1",
    )
    assert subnets[0].subnets == ["subnet-full"]
    assert subnets[1].subnets == ["subnet-fallback"]

    recovery_client.get_recovery_service_subnet.side_effect = None
    recovery_client.get_recovery_service_subnet.return_value = _response(
        SimpleNamespace(id="rss-single", subnet_id="subnet-single")
    )
    assert server.get_recovery_service_subnet("rss-single").subnets == ["subnet-single"]


def test_protected_database_tools_cover_serialization_fallbacks(monkeypatch):
    recovery_client = MagicMock()
    monkeypatch.setattr(
        server,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        server, "_resolve_compartment_id", lambda value, **_kwargs: value
    )

    class FallbackSummary:
        def __init__(self):
            self.id = "pd-fallback"
            self.recovery_service_subnets = [SimpleNamespace(id="rss-fallback")]

        def model_dump(self, **_kwargs):
            raise RuntimeError("model dump unavailable")

        def dict(self, **_kwargs):
            raise RuntimeError("dict unavailable")

    monkeypatch.setattr(
        server,
        "map_protected_database_summary",
        MagicMock(side_effect=[None, FallbackSummary()]),
    )
    recovery_client.list_protected_databases.return_value = _response(
        [object(), object()]
    )
    recovery_client.get_recovery_service_subnet.side_effect = RuntimeError(
        "subnet lookup failed"
    )
    recovery_client.get_protected_database.side_effect = RuntimeError(
        "metrics lookup failed"
    )

    protected_databases = server.list_protected_databases("compartment")
    assert protected_databases == [
        {
            "id": "pd-fallback",
            "policyLockedDateTime": None,
            "recovery_service_subnets": [{"id": "rss-fallback"}],
        }
    ]

    class BadMetrics:
        def model_dump(self, **_kwargs):
            raise RuntimeError("model dump unavailable")

        def dict(self, **_kwargs):
            raise RuntimeError("dict unavailable")

    class FallbackProtectedDatabase:
        def __init__(self):
            self.id = "pd1"
            self.change_rate = 2.0
            self.compression_ratio = 3.0
            self.recovery_service_subnets = [SimpleNamespace(id="rss-partial")]
            self.metrics = BadMetrics()

        def model_dump(self, **_kwargs):
            raise RuntimeError("model dump unavailable")

        def dict(self, **_kwargs):
            raise RuntimeError("dict unavailable")

    monkeypatch.setattr(
        server,
        "map_protected_database",
        MagicMock(return_value=FallbackProtectedDatabase()),
    )
    recovery_client.get_protected_database.side_effect = None
    recovery_client.get_protected_database.return_value = _response(object())
    recovery_client.get_recovery_service_subnet.side_effect = RuntimeError(
        "subnet lookup failed"
    )

    protected_database = server.get_protected_database("pd1")
    assert protected_database["id"] == "pd1"
    assert "change_rate" not in protected_database
    assert "compression_ratio" not in protected_database
    assert protected_database["recovery_service_subnets"] == [{"id": "rss-partial"}]
    assert protected_database["metrics"] == {
        "backup-space-estimate-in-gbs": None,
        "backup-space-used-in-gbs": None,
        "current-retention-period-in-seconds": None,
        "db-size-in-gbs": None,
        "is-redo-logs-enabled": None,
        "minimum-recovery-needed-in-days": None,
        "retention-period-in-days": None,
        "unprotected-window-in-seconds": None,
    }


def test_summary_tools_cover_fallback_counts_and_metrics(monkeypatch):
    recovery_client = MagicMock()
    monkeypatch.setattr(
        server,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        server,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: compartment_id or "tenancy",
    )
    monkeypatch.setattr(server, "get_tenancy", lambda: "tenancy")

    recovery_client.list_protected_databases.return_value = _response(
        [
            SimpleNamespace(id="pd1", health="PROTECTED"),
            SimpleNamespace(id="pd2"),
            SimpleNamespace(data=SimpleNamespace(id="pd3")),
            SimpleNamespace(display_name="missing id"),
        ]
    )
    recovery_client.get_protected_database.side_effect = [
        _response(SimpleNamespace(health="ALERT")),
        _response(SimpleNamespace()),
    ]

    health = server.summarize_protected_database_health(
        compartment_id=None, region="us-ashburn-1"
    )
    assert health["aggregated"] == {
        "compartmentId": "tenancy",
        "region": "us-ashburn-1",
        "protected": 1,
        "warning": 0,
        "alert": 1,
        "unknown": 1,
        "total": 3,
    }
    assert health["per_compartment"] == [
        {
            "compartmentId": "tenancy",
            "region": "us-ashburn-1",
            "protected": 1,
            "warning": 0,
            "alert": 1,
            "unknown": 1,
            "total": 3,
        }
    ]

    recovery_client.list_protected_databases.return_value = _response(
        [
            SimpleNamespace(id="pd1"),
            SimpleNamespace(id="pd2"),
            SimpleNamespace(id="pd3"),
            SimpleNamespace(display_name="missing id"),
        ]
    )
    recovery_client.get_protected_database.side_effect = [
        _response(SimpleNamespace(is_redo_logs_shipped=True)),
        _response(SimpleNamespace(is_redo_logs_shipped=False)),
        _response(SimpleNamespace(metrics=SimpleNamespace(is_redo_logs_enabled=True))),
    ]

    redo = server.summarize_protected_database_redo_status(
        compartment_id="compartment", region="us-ashburn-1"
    )
    assert redo["aggregated"] == {
        "compartmentId": "compartment",
        "region": "us-ashburn-1",
        "enabled": 2,
        "disabled": 1,
        "total": 3,
    }
    assert redo["per_compartment"][0]["total"] == 3

    recovery_client.list_protected_databases.return_value = _response(
        [
            SimpleNamespace(
                id="pd1",
                lifecycle_state="ACTIVE",
                metrics=SimpleNamespace(backup_space_used_in_gbs=2.5),
            ),
            SimpleNamespace(id="deleted", lifecycle_state="DELETED"),
            SimpleNamespace(id="pd2", lifecycle_state="DELETE_SCHEDULED"),
            SimpleNamespace(lifecycle_state="ACTIVE"),
            SimpleNamespace(id="pd3", lifecycle_state="ACTIVE"),
        ]
    )
    recovery_client.get_protected_database.side_effect = [
        RuntimeError("fall back to summary metrics"),
        _response(SimpleNamespace(metrics={"backupSpaceUsedInGbs": 3.5})),
        _response(SimpleNamespace(metrics={})),
    ]

    backup_space = server.summarize_backup_space_used(
        compartment_id="compartment", region="us-ashburn-1"
    )
    assert backup_space["aggregated"]["compartmentId"] == "compartment"
    assert backup_space["aggregated"]["totalDatabasesScanned"] == 3
    assert backup_space["aggregated"]["sumBackupSpaceUsedInGBs"] == 6.0
    assert backup_space["missingMetricsCount"] == 1


def test_database_tools_cover_compartment_paths_and_backup_enrichment(monkeypatch):
    db_client = MagicMock()
    recovery_client = MagicMock()
    monkeypatch.setattr(
        models.oci.util,
        "to_dict",
        lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
    )
    monkeypatch.setattr(
        server,
        "get_database_client",
        lambda region=None, request_id=None: db_client,
    )
    monkeypatch.setattr(
        server,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        server,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: compartment_id or "tenancy",
    )
    monkeypatch.setattr(
        server,
        "_fetch_db_home_ids_for_compartment",
        lambda compartment_id, region=None: ["home1"],
    )

    recovery_client.list_protected_databases.return_value = _response(
        SimpleNamespace(items=[{"databaseId": "db1", "protectionPolicyId": "policy1"}])
    )
    db_client.list_databases.return_value = _response(
        SimpleNamespace(items=[SimpleNamespace(id="db1", db_name="DB1")])
    )
    db_client.get_database.return_value = _response(
        {
            "id": "db1",
            "compartmentId": "compartment",
            "dbBackupConfig": {"isAutoBackupEnabled": True},
        }
    )

    databases = server.list_databases(
        compartment_id="compartment",
        system_id="system1",
        limit=10,
        page="page",
        sort_by="DBNAME",
        sort_order="ASC",
        lifecycle_state="AVAILABLE",
        db_name="DB1",
        region="us-ashburn-1",
    )
    assert databases[0].id == "db1"
    assert databases[0].db_backup_config.is_auto_backup_enabled is True
    assert databases[0].protection_policy_id == "policy1"
    assert db_client.list_databases.call_args.kwargs["db_home_id"] == "home1"

    db_client.get_database.return_value = _response(
        {"id": "db1", "compartmentId": "compartment"}
    )
    recovery_client.list_protected_databases.return_value = _response(
        [{"databaseId": "db1", "protectionPolicyId": "policy2"}]
    )
    database = server.get_database("db1", region="us-ashburn-1")
    assert database.id == "db1"
    assert database.protection_policy_id == "policy2"

    db_client.list_databases.return_value = _response(
        SimpleNamespace(
            items=[
                {
                    "id": "db1",
                    "dbUniqueName": "DB1_UNQ",
                    "dbBackupConfig": {"isAutoBackupEnabled": True},
                }
            ]
        )
    )
    db_client.list_backups.side_effect = [
        _response(
            SimpleNamespace(
                items=[
                    SimpleNamespace(
                        id="backup1",
                        database_id="db1",
                        backup_destination_type="DBRS",
                    )
                ]
            ),
            has_next_page=True,
            next_page="backup-page-2",
        ),
        _response(
            SimpleNamespace(
                items=[
                    {
                        "id": "backup2",
                        "databaseId": "db1",
                        "databaseSizeInGbs": 11,
                    }
                ]
            )
        ),
    ]

    backups = server.list_backups(
        compartment_id="compartment",
        lifecycle_state="ACTIVE",
        type="FULL",
        region="us-ashburn-1",
    )
    assert [backup["id"] for backup in backups] == ["backup1", "backup2"]
    assert backups[0]["db_unique_name"] == "DB1_UNQ"
    assert backups[1]["database-size-in-gbs"] == 11
    assert db_client.list_backups.call_args_list[1].kwargs["page"] == "backup-page-2"

    db_client.get_backup.return_value = _response(
        SimpleNamespace(
            id="backup1",
            database_id="db1",
            database_size_in_gbs=8,
            retention_period_in_days=30,
        )
    )
    db_client.get_database.return_value = _response(
        {
            "dbUniqueName": "DB1_UNQ",
            "dbBackupConfig": {
                "backupDestinationDetails": [{"type": "RECOVERY_SERVICE"}]
            },
        }
    )
    backup = server.get_backup("backup1", region="us-ashburn-1")
    assert backup["database-size-in-gbs"] == 8
    assert backup["backup-destination-type"] == "DBRS"
    assert backup["db_unique_name"] == "DB1_UNQ"

    db_client.list_databases.return_value = _response(
        [
            {
                "id": "db1",
                "dbName": "DB1",
                "dbBackupConfig": {
                    "isAutoBackupEnabled": True,
                    "backupDestinationDetails": [
                        {"type": "RECOVERY_SERVICE", "id": "dest1"}
                    ],
                },
            },
            {"id": "db2", "dbName": "DB2"},
        ]
    )
    db_client.get_database.return_value = _response(
        {
            "id": "db2",
            "dbName": "DB2",
            "dbBackupConfig": {"isAutoBackupEnabled": False},
        }
    )
    db_client.list_backups.side_effect = None
    db_client.list_backups.return_value = _response(
        [SimpleNamespace(time_ended="2024-01-02T00:00:00Z")]
    )
    summary = server.summarize_protected_database_backup_destination(
        compartment_id="compartment",
        region="us-ashburn-1",
        include_last_backup_time=True,
        db_name="DB",
        limit_per_home=50,
        max_db_homes=1,
        max_total_databases=2,
    )
    assert summary.total_databases == 2
    assert summary.counts_by_destination_type == {"DBRS": 1}
    assert summary.unconfigured_count == 1
    assert [item.database_id for item in summary.items] == ["db1", "db2"]
    assert summary.items[0].last_backup_time.isoformat() == "2024-01-02T00:00:00+00:00"


def test_database_child_scope_tools_cover_deduplication(monkeypatch):
    db_client = MagicMock()
    recovery_client = MagicMock()
    monkeypatch.setattr(
        models.oci.util,
        "to_dict",
        lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
    )
    monkeypatch.setattr(
        server,
        "get_database_client",
        lambda region=None, request_id=None: db_client,
    )
    monkeypatch.setattr(
        server,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        server, "_resolve_compartment_id", lambda value, **_kwargs: value
    )
    monkeypatch.setattr(
        server,
        "_compartment_ids_for_tool",
        lambda compartment_id, fetch_for_child_compartment, request_id=None: [
            "compartment-a",
            "compartment-b",
        ],
    )
    monkeypatch.setattr(
        server,
        "_fetch_db_home_ids_for_compartment",
        lambda compartment_id, region=None: ["home1"],
    )
    recovery_client.list_protected_databases.return_value = _response([])

    db_client.list_databases.side_effect = [
        _response(
            SimpleNamespace(
                items=[
                    {
                        "id": "db1",
                        "dbName": "DB1",
                        "dbBackupConfig": {"isAutoBackupEnabled": True},
                    }
                ]
            )
        ),
        _response(
            SimpleNamespace(
                items=[
                    {
                        "id": "db1",
                        "dbName": "DB1 Duplicate",
                        "dbBackupConfig": {"isAutoBackupEnabled": True},
                    },
                    {
                        "id": "db2",
                        "dbName": "DB2",
                        "dbBackupConfig": {"isAutoBackupEnabled": True},
                    },
                ]
            )
        ),
    ]
    databases = server.list_databases(
        compartment_id="root",
        fetch_for_child_compartment=True,
    )
    assert [database.id for database in databases] == ["db1", "db2"]

    db_client.reset_mock()
    db_client.list_databases.side_effect = [
        _response(
            SimpleNamespace(
                items=[
                    {
                        "id": "db1",
                        "dbUniqueName": "DB1_UNQ",
                        "dbBackupConfig": {"isAutoBackupEnabled": True},
                    }
                ]
            )
        ),
        _response(
            SimpleNamespace(
                items=[
                    {
                        "id": "db2",
                        "dbUniqueName": "DB2_UNQ",
                        "dbBackupConfig": {"isAutoBackupEnabled": True},
                    }
                ]
            )
        ),
    ]
    db_client.list_backups.side_effect = [
        _response(SimpleNamespace(items=[{"id": "backup1", "databaseId": "db1"}])),
        _response(
            SimpleNamespace(
                items=[
                    {"id": "backup1", "databaseId": "db2"},
                    {"id": "backup2", "databaseId": "db2"},
                ]
            )
        ),
    ]
    backups = server.list_backups(
        compartment_id="root",
        fetch_for_child_compartment=True,
    )
    assert [backup["id"] for backup in backups] == ["backup1", "backup2"]

    db_client.reset_mock()
    db_client.list_databases.side_effect = [
        _response(
            [
                {
                    "id": "db1",
                    "dbName": "DB1",
                    "dbBackupConfig": {
                        "isAutoBackupEnabled": True,
                        "backupDestinationDetails": [
                            {"type": "RECOVERY_SERVICE", "id": "dest1"}
                        ],
                    },
                }
            ]
        ),
        _response(
            [
                {
                    "id": "db1",
                    "dbName": "DB1 Duplicate",
                    "dbBackupConfig": {
                        "isAutoBackupEnabled": True,
                        "backupDestinationDetails": [
                            {"type": "RECOVERY_SERVICE", "id": "dest1"}
                        ],
                    },
                },
                {
                    "id": "db2",
                    "dbName": "DB2",
                    "dbBackupConfig": {"isAutoBackupEnabled": False},
                },
            ]
        ),
    ]
    summary = server.summarize_protected_database_backup_destination(
        compartment_id="root",
        fetch_for_child_compartment=True,
        db_home_id="home1",
        include_last_backup_time=False,
    )
    assert [item.database_id for item in summary.items] == ["db1", "db2"]
    assert summary.total_databases == 3

    db_client.reset_mock()
    db_client.list_db_homes.side_effect = [
        _response([SimpleNamespace(id="home1")]),
        _response([SimpleNamespace(id="home1"), SimpleNamespace(id="home2")]),
    ]
    homes = server.list_db_homes(
        compartment_id="root",
        fetch_for_child_compartment=True,
    )
    assert [home.id for home in homes] == ["home1", "home2"]

    db_client.reset_mock()
    db_client.list_db_systems.side_effect = [
        _response([SimpleNamespace(id="system1")]),
        _response([SimpleNamespace(id="system1"), SimpleNamespace(id="system2")]),
    ]
    systems = server.list_db_systems(
        compartment_id="root",
        fetch_for_child_compartment=True,
    )
    assert [system.id for system in systems] == ["system1", "system2"]


def test_database_home_and_system_tools_cover_pagination_and_defaults(monkeypatch):
    db_client = MagicMock()
    monkeypatch.setattr(
        models.oci.util,
        "to_dict",
        lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
    )
    monkeypatch.setattr(
        server,
        "get_database_client",
        lambda region=None, request_id=None: db_client,
    )
    monkeypatch.setattr(server, "get_tenancy", lambda: "tenancy")
    monkeypatch.setattr(
        server,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: f"resolved-{compartment_id}",
    )

    db_client.list_db_homes.side_effect = [
        _response(
            SimpleNamespace(items=[SimpleNamespace(id="home1", display_name="Home 1")]),
            has_next_page=True,
            next_page="home-page-2",
        ),
        _response([SimpleNamespace(id="home2", display_name="Home 2")]),
    ]
    homes = server.list_db_homes(
        compartment_id=None,
        db_system_id=None,
        limit=1,
        page="home-page-1",
        region="us-ashburn-1",
    )
    assert [home.id for home in homes] == ["home1", "home2"]
    assert (
        db_client.list_db_homes.call_args_list[0].kwargs["compartment_id"]
        == "resolved-tenancy"
    )
    assert db_client.list_db_homes.call_args_list[1].kwargs["page"] == "home-page-2"

    db_client.get_db_home.return_value = _response(
        SimpleNamespace(id="home1", display_name="Home 1")
    )
    assert server.get_db_home("home1", region="us-ashburn-1").id == "home1"

    db_client.list_db_systems.side_effect = [
        _response(
            [SimpleNamespace(id="system1", display_name="System 1")],
            has_next_page=True,
            next_page="system-page-2",
        ),
        _response(SimpleNamespace(items=[SimpleNamespace(id="system2")])),
    ]
    systems = server.list_db_systems(
        compartment_id="compartment",
        lifecycle_state="AVAILABLE",
        limit=1,
        page="system-page-1",
        region="us-ashburn-1",
    )
    assert [system.id for system in systems] == ["system1", "system2"]
    assert (
        db_client.list_db_systems.call_args_list[0].kwargs["lifecycle_state"]
        == "AVAILABLE"
    )
    assert db_client.list_db_systems.call_args_list[1].kwargs["page"] == "system-page-2"

    db_client.get_db_system.return_value = _response(
        SimpleNamespace(id="system1", display_name="System 1")
    )
    assert server.get_db_system("system1", region="us-ashburn-1").id == "system1"


def test_logging_tool_wrapper_tenancy_and_apikey_client_paths(monkeypatch, tmp_path):
    root_logger = server.logging.getLogger()
    original_handlers = list(root_logger.handlers)
    try:
        root_logger.handlers = []
        monkeypatch.setenv("ORACLE_MCP_LOG_DIR", str(tmp_path))
        monkeypatch.setenv("ORACLE_MCP_LOG_TO_STDOUT", "yes")
        server.setup_logging()
        assert any(
            isinstance(handler, server.RotatingFileHandler)
            for handler in root_logger.handlers
        )
        assert any(
            isinstance(handler, server.logging.StreamHandler)
            and not isinstance(handler, server.RotatingFileHandler)
            for handler in root_logger.handlers
        )
        server.setup_logging()
    finally:
        root_logger.handlers = original_handlers

    phases = []
    monkeypatch.setattr(
        server,
        "_log_event",
        lambda _event, **kwargs: phases.append(kwargs["phase"]),
    )

    @server._tool_logger("boom")
    def failing_tool():
        raise ValueError("bad input")

    with pytest.raises(ValueError, match="bad input"):
        failing_tool()
    assert phases == ["start", "error"]

    monkeypatch.setenv("TENANCY_ID_OVERRIDE", "tenancy-override")
    assert server.get_tenancy() == "tenancy-override"
    monkeypatch.delenv("TENANCY_ID_OVERRIDE", raising=False)
    monkeypatch.setattr(server, "_get_profile_value", lambda _key: None)
    with pytest.raises(RuntimeError, match="Tenancy lookup"):
        server.get_tenancy()

    monkeypatch.setattr(
        server, "_get_http_config_and_signer", lambda region=None: (None, None)
    )
    monkeypatch.setattr(
        server, "_load_oci_config_for_server", lambda: {"region": "home"}
    )
    monkeypatch.setattr(server, "_effective_auth_method", lambda: "apikey")
    monkeypatch.setattr(
        server,
        "_wrap_oci_client",
        lambda client, **kwargs: (client, kwargs["client_name"]),
    )
    identity_client = MagicMock(return_value="identity-client")
    database_client = MagicMock(return_value="database-client")
    monitoring_client = MagicMock(return_value="monitoring-client")
    monkeypatch.setattr(server.oci.identity, "IdentityClient", identity_client)
    monkeypatch.setattr(server.oci.database, "DatabaseClient", database_client)
    monkeypatch.setattr(server.oci.monitoring, "MonitoringClient", monitoring_client)

    assert server.get_identity_client()[1] == "identity"
    assert server.get_database_client(region="us-phoenix-1")[1] == "database"
    assert server.get_monitoring_client(region="us-phoenix-1")[1] == "monitoring"
    assert "signer" not in identity_client.call_args.kwargs
    assert database_client.call_args.args[0]["region"] == "us-phoenix-1"
    assert "signer" not in monitoring_client.call_args.kwargs

    recovery_client = MagicMock(return_value="recovery-client")
    monkeypatch.setattr(server.oci.recovery, "DatabaseRecoveryClient", recovery_client)
    monkeypatch.setattr(server, "_effective_auth_method", lambda: "session")
    monkeypatch.setattr(
        server, "_build_signer_for_session", lambda _config: "session-signer"
    )
    assert server.get_recovery_client(region="us-ashburn-1")[1] == "recovery"
    assert recovery_client.call_args.kwargs["signer"] == "session-signer"


def test_summary_serialization_fallbacks_and_error_paths(monkeypatch):
    recovery_client = MagicMock()
    monkeypatch.setattr(
        server,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        server,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: compartment_id or "tenancy",
    )
    recovery_client.list_protected_databases.return_value = _response([])

    monkeypatch.setattr(
        models.ProtectedDatabaseHealthCounts,
        "model_dump",
        lambda self, **_kwargs: _raise(RuntimeError("model_dump failed")),
    )
    monkeypatch.setattr(
        models.ProtectedDatabaseHealthCounts,
        "dict",
        lambda self, **_kwargs: _raise(RuntimeError("dict failed")),
    )
    assert server.summarize_protected_database_health("compartment")["aggregated"] == {
        "compartmentId": "compartment",
        "region": None,
        "protected": 0,
        "warning": 0,
        "alert": 0,
        "unknown": 0,
        "total": 0,
    }

    monkeypatch.setattr(
        models.ProtectedDatabaseRedoCounts,
        "model_dump",
        lambda self, **_kwargs: _raise(RuntimeError("model_dump failed")),
    )
    monkeypatch.setattr(
        models.ProtectedDatabaseRedoCounts,
        "dict",
        lambda self, **_kwargs: _raise(RuntimeError("dict failed")),
    )
    assert server.summarize_protected_database_redo_status("compartment")["aggregated"] == {
        "compartmentId": "compartment",
        "region": None,
        "enabled": 0,
        "disabled": 0,
        "total": 0,
    }

    recovery_client.list_protected_databases.side_effect = RuntimeError("service down")
    with pytest.raises(RuntimeError, match="service down"):
        server.summarize_backup_space_used("compartment")


def test_backup_tools_cover_manual_paging_errors_and_destination_variants(monkeypatch):
    db_client = MagicMock()
    monkeypatch.setattr(
        models.oci.util,
        "to_dict",
        lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
    )
    monkeypatch.setattr(
        server,
        "get_database_client",
        lambda region=None, request_id=None: db_client,
    )
    monkeypatch.setattr(
        server,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: compartment_id or "tenancy",
    )

    db_client.list_backups.return_value = _response(
        SimpleNamespace(
            items=[
                {
                    "id": "manual-backup",
                    "databaseId": "db1",
                    "retentionPeriodInYears": 2,
                }
            ]
        ),
        has_next_page=True,
        next_page="ignored-when-not-aggregating",
    )
    db_client.get_database.side_effect = RuntimeError("database lookup failed")
    backups = server.list_backups(
        database_id="db1",
        lifecycle_state="ACTIVE",
        type="FULL",
        limit=25,
        page="start",
        region="us-ashburn-1",
        aggregate_pages=False,
    )
    assert backups[0]["id"] == "manual-backup"
    assert backups[0]["retention-period-in-years"] == 2
    assert backups[0]["db_unique_name"] is None
    assert db_client.list_backups.call_args.kwargs == {
        "database_id": "db1",
        "lifecycle_state": "ACTIVE",
        "type": "FULL",
        "limit": 25,
        "page": "start",
    }

    with pytest.raises(ValueError, match="Provide database_id"):
        server.list_backups(region="us-ashburn-1")

    db_client.get_database.side_effect = None
    for destination_type, expected in (
        ("OBJECT_STORE", "OBJECT_STORE"),
        ("NFS", "NFS"),
    ):
        db_client.get_backup.return_value = _response(
            {"id": f"backup-{expected}", "databaseId": f"db-{expected}"}
        )
        db_client.get_database.return_value = _response(
            {
                "dbUniqueName": f"{expected}_UNQ",
                "backupDestinationDetails": [{"destinationType": destination_type}],
            }
        )
        backup = server.get_backup(f"backup-{expected}", region="us-ashburn-1")
        assert backup["backup-destination-type"] == expected
        assert backup["db_unique_name"] == f"{expected}_UNQ"


def test_backup_destination_summary_covers_object_store_paging_and_errors(monkeypatch):
    db_client = MagicMock()
    monkeypatch.setattr(
        models.oci.util,
        "to_dict",
        lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
    )
    monkeypatch.setattr(
        server,
        "get_database_client",
        lambda region=None, request_id=None: db_client,
    )
    monkeypatch.setattr(
        server,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: compartment_id or "tenancy",
    )

    db_client.list_databases.side_effect = [
        _response(
            [
                {
                    "id": "db-object",
                    "dbName": "Object DB",
                    "dbBackupConfig": {
                        "isAutoBackupEnabled": True,
                        "backupDestinationDetails": [
                            {
                                "destinationType": "OBJECT_STORE",
                                "backupDestinationId": "dest-object",
                            }
                        ],
                    },
                }
            ],
            has_next_page=True,
            next_page="db-page-2",
        ),
        _response(
            [
                {
                    "id": "db-nfs",
                    "dbName": "NFS DB",
                    "autoBackupEnabled": True,
                    "backupDestinationDetails": [{"type": "NFS"}],
                },
                {"dbName": "Missing Id"},
            ]
        ),
    ]
    summary = server.summarize_protected_database_backup_destination(
        compartment_id="compartment",
        region="us-ashburn-1",
        db_home_id="home-explicit",
        include_last_backup_time=False,
    )
    assert summary.total_databases == 3
    assert summary.counts_by_destination_type == {"OBJECT_STORE": 1}
    assert summary.db_names_by_destination_type == {"OBJECT_STORE": ["Object DB"]}
    assert [item.database_id for item in summary.items] == ["db-object", "db-nfs"]
    assert db_client.list_databases.call_args_list[1].kwargs["page"] == "db-page-2"

    db_client.list_databases.side_effect = RuntimeError("list databases failed")
    with pytest.raises(RuntimeError, match="list databases failed"):
        server.summarize_protected_database_backup_destination(
            compartment_id="compartment",
            db_home_id="home-explicit",
        )


def test_database_list_branches_and_tool_error_paths(monkeypatch):
    db_client = MagicMock()
    recovery_client = MagicMock()
    monkeypatch.setattr(
        models.oci.util,
        "to_dict",
        lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
    )
    monkeypatch.setattr(
        server,
        "get_database_client",
        lambda region=None, request_id=None: db_client,
    )
    monkeypatch.setattr(
        server,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        server,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: compartment_id or "tenancy",
    )
    recovery_client.list_protected_databases.return_value = _response([])

    with pytest.raises(ValueError, match="Either db_home_id"):
        server.list_databases()

    monkeypatch.setattr(
        server,
        "_fetch_db_home_ids_for_compartment",
        lambda compartment_id, region=None: [],
    )
    assert server.list_databases(compartment_id="compartment") == []

    monkeypatch.setattr(
        server,
        "_fetch_db_home_ids_for_compartment",
        lambda compartment_id, region=None: ["home1"],
    )
    recovery_client.list_protected_databases.side_effect = RuntimeError(
        "recovery unavailable"
    )
    db_client.list_databases.return_value = _response(
        [
            {
                "id": "db1",
                "dbName": "DB1",
                "dbBackupConfig": {"isAutoBackupEnabled": True},
            }
        ]
    )
    databases = server.list_databases(compartment_id="compartment")
    assert databases[0].protection_policy_id is None

    db_client.list_databases.return_value = _response([{"id": "db2", "dbName": "DB2"}])
    db_client.get_database.side_effect = RuntimeError("backup config unavailable")
    databases = server.list_databases(compartment_id="compartment", db_home_id="home1")
    assert databases[0].id == "db2"
    assert databases[0].db_backup_config is None

    error_cases = [
        (
            server.list_protection_policies,
            {"compartment_id": "compartment"},
            "list_protection_policies",
        ),
        (
            server.get_protection_policy,
            {"protection_policy_id": "policy1"},
            "get_protection_policy",
        ),
        (
            server.list_recovery_service_subnets,
            {"compartment_id": "compartment"},
            "list_recovery_service_subnets",
        ),
        (
            server.get_recovery_service_subnet,
            {"recovery_service_subnet_id": "rss1"},
            "get_recovery_service_subnet",
        ),
    ]
    for tool, kwargs, method_name in error_cases:
        getattr(recovery_client, method_name).side_effect = RuntimeError(
            f"{method_name} failed"
        )
        with pytest.raises(RuntimeError, match=f"{method_name} failed"):
            tool(**kwargs)
        getattr(recovery_client, method_name).side_effect = None

    db_error_cases = [
        (server.get_database, {"database_id": "db1"}, "get_database"),
        (server.get_backup, {"backup_id": "backup1"}, "get_backup"),
        (server.list_db_homes, {"compartment_id": "compartment"}, "list_db_homes"),
        (server.get_db_home, {"db_home_id": "home1"}, "get_db_home"),
        (server.list_db_systems, {"compartment_id": "compartment"}, "list_db_systems"),
        (server.get_db_system, {"db_system_id": "system1"}, "get_db_system"),
    ]
    for tool, kwargs, method_name in db_error_cases:
        getattr(db_client, method_name).side_effect = RuntimeError(
            f"{method_name} failed"
        )
        with pytest.raises(RuntimeError, match=f"{method_name} failed"):
            tool(**kwargs)
        getattr(db_client, method_name).side_effect = None

    assert server.oci_recovery_service_dashboard_prompt()[0]["role"] == "system"


class TestServer:
    def test_http_signer_requires_region(self, monkeypatch):
        monkeypatch.setattr(
            server, "get_access_token", lambda: SimpleNamespace(token="token")
        )
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8080")
        monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")

        with pytest.raises(RuntimeError, match="OCI_REGION"):
            server._get_http_config_and_signer()

    @patch("oracle.oci_recovery_mcp_server.server.OCIProvider")
    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run, mock_provider):
        mock_env = {
            "ORACLE_MCP_HOST": "127.0.0.1",
            "ORACLE_MCP_PORT": "8080",
            "IDCS_DOMAIN": "idcs.example.com",
            "IDCS_CLIENT_ID": "client-id",
            "IDCS_CLIENT_SECRET": "client-secret",
            "IDCS_AUDIENCE": "mcp-audience",
            "ORACLE_MCP_BASE_URL": "http://127.0.0.1:8080",
        }
        # Return configured values for known keys, and default for others
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)
        mock_provider.return_value = MagicMock()

        import oracle.oci_recovery_mcp_server.server as server

        server.main()
        mock_provider.assert_called_once_with(
            config_url="https://idcs.example.com/.well-known/openid-configuration",
            client_id="client-id",
            client_secret="client-secret",
            audience="mcp-audience",
            required_scopes=f"openid profile email oci_mcp.{server.__project__.removeprefix('oracle.oci-').removesuffix('-mcp-server').replace('-', '_')}.invoke".split(),
            base_url="http://127.0.0.1:8080",
        )
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=int(mock_env["ORACLE_MCP_PORT"]),
        )

    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        # Return None for host/port keys, otherwise pass through default (for log dir/file)
        mock_getenv.side_effect = lambda k, d=None: (
            None if k in ("ORACLE_MCP_HOST", "ORACLE_MCP_PORT") else d
        )

        import oracle.oci_recovery_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {"ORACLE_MCP_HOST": "127.0.0.1"}
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)

        import oracle.oci_recovery_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {"ORACLE_MCP_PORT": "8080"}
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)

        import oracle.oci_recovery_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_http_missing_idcs_config_raises(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "127.0.0.1",
            "ORACLE_MCP_PORT": "8080",
        }
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)

        import oracle.oci_recovery_mcp_server.server as server

        with pytest.raises(RuntimeError, match="HTTP transport requires"):
            server.main()
        mock_mcp_run.assert_not_called()
