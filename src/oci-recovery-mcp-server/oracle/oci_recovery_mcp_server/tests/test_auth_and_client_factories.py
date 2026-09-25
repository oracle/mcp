"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Credential resolution and OCI client construction: the profile auth context,
the informational config read, and every client factory.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch


from oracle.oci_recovery_mcp_server import auth
from oracle.oci_recovery_mcp_server import recovery_tools
from oracle.oci_recovery_mcp_server import clients
from oracle.oci_recovery_mcp_server import telemetry


class TestProfileClientFactories:
    """Client factories now resolve apikey/session credentials through
    oracle_mcp_common.build_auth_context() (see auth._build_profile_auth_context),
    so these assert the config/signer handed to the SDK constructor.
    """

    @patch(
        "oracle.oci_recovery_mcp_server.telemetry._wrap_oci_client",
        side_effect=lambda client, **_: client,
    )
    @patch("oracle.oci_recovery_mcp_server.recovery_tools.oci.recovery.DatabaseRecoveryClient")
    @patch("oracle.oci_recovery_mcp_server.auth._build_profile_auth_context")
    def test_get_recovery_client_apikey_uses_profile_auth_context(
        self,
        mock_auth_context,
        mock_client,
        _mock_wrap,
    ):
        """
        The recovery client is built from the shared auth context's config and signer,
        with the caller's region overriding the profile's and the user agent stamped on.
        """
        signer = object()
        mock_auth_context.return_value = SimpleNamespace(
            config={"region": "us-ashburn-1", "tenancy": "ocid1.tenancy.oc1..t"},
            signer=signer,
        )

        result = clients.get_recovery_client(region="us-phoenix-1", request_id="rid")

        args, kwargs = mock_client.call_args
        assert args[0]["region"] == "us-phoenix-1"
        assert args[0]["tenancy"] == "ocid1.tenancy.oc1..t"
        assert args[0]["additional_user_agent"].startswith(auth._USER_AGENT_NAME)
        assert kwargs["signer"] is signer
        assert result is mock_client.return_value

    @patch(
        "oracle.oci_recovery_mcp_server.telemetry._wrap_oci_client",
        side_effect=lambda client, **_: client,
    )
    @patch("oracle.oci_recovery_mcp_server.recovery_tools.oci.monitoring.MonitoringClient")
    @patch("oracle.oci_recovery_mcp_server.auth._build_profile_auth_context")
    def test_get_monitoring_client_session_uses_profile_auth_context(
        self,
        mock_auth_context,
        mock_client,
        _mock_wrap,
    ):
        """
        The monitoring client follows the same path, taking the caller's region and
        the shared auth context's signer.
        """
        signer = object()
        mock_auth_context.return_value = SimpleNamespace(
            config={"region": "us-ashburn-1"}, signer=signer
        )

        result = clients.get_monitoring_client(region="us-phoenix-1", request_id="rid")

        args, kwargs = mock_client.call_args
        assert args[0]["region"] == "us-phoenix-1"
        assert kwargs["signer"] is signer
        assert result is mock_client.return_value

    @patch(
        "oracle.oci_recovery_mcp_server.telemetry._wrap_oci_client",
        side_effect=lambda client, **_: client,
    )
    @patch("oracle.oci_recovery_mcp_server.recovery_tools.oci.recovery.DatabaseRecoveryClient")
    @patch("oracle.oci_recovery_mcp_server.auth._http_config_and_signer")
    @patch("oracle.oci_recovery_mcp_server.auth._serving_http", return_value=True)
    def test_http_client_uses_request_scoped_token_exchange_signer(
        self,
        _mock_serving_http,
        mock_http_auth,
        mock_client,
        _mock_wrap,
    ):
        """
        Under HTTP each call gets a freshly exchanged signer.

        UPST signers are short-lived and scoped to one caller's token, so caching one
        would sign a later request as an earlier caller, and keep signing after the
        token behind it expired.
        """
        first, second = object(), object()
        mock_http_auth.side_effect = [
            ({"region": "us-phoenix-1"}, first),
            ({"region": "us-phoenix-1"}, second),
        ]

        clients.get_recovery_client(region="us-phoenix-1", request_id="rid")
        clients.get_recovery_client(region="us-phoenix-1", request_id="rid")

        # A fresh signer per call: UPST signers are never cached.
        assert [call.kwargs["signer"] for call in mock_client.call_args_list] == [
            first,
            second,
        ]
        assert mock_client.call_args_list[0].args[0]["region"] == "us-phoenix-1"


def test_informational_config_reads_same_file_as_the_credentials(monkeypatch, tmp_path):
    """The OCI SDK only falls back to OCI_CONFIG_FILE when ~/.oci/config is absent,
    while oracle_mcp_common.resolve_config_file() always prefers it. Tenancy and
    region lookups must follow the credentials, not the default path.
    """
    key_file = tmp_path / "api_key.pem"
    key_file.write_text("not-a-real-key", encoding="utf-8")
    alt_config = tmp_path / "alt_config"
    alt_config.write_text(
        "[PROFILE1]\n"
        "tenancy=ocid1.tenancy.oc1..alt\n"
        "region=eu-frankfurt-1\n"
        "user=ocid1.user.oc1..alt\n"
        "fingerprint=aa:bb\n"
        f"key_file={key_file}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OCI_CONFIG_FILE", str(alt_config))
    monkeypatch.setenv("ORACLE_MCP_AUTH_PROFILE", "PROFILE1")
    monkeypatch.setenv("ORACLE_MCP_AUTH_METHOD", "apikey")
    monkeypatch.delenv("TENANCY_ID_OVERRIDE", raising=False)
    monkeypatch.delenv("ORACLE_MCP_TENANCY_ID", raising=False)

    config = auth._load_oci_config_for_server()

    assert config["tenancy"] == "ocid1.tenancy.oc1..alt"
    assert config["additional_user_agent"].startswith(auth._USER_AGENT_NAME)
    assert auth.get_tenancy() == "ocid1.tenancy.oc1..alt"
    assert auth._effective_region() == "eu-frankfurt-1"


def test_profile_auth_context_defers_to_the_shared_library(monkeypatch):
    """
    Only the deprecated unseparated "apikey" spelling is translated locally;
    every other value -- including unset, which means auto-detect -- is passed
    through untouched so oracle-mcp-common resolves type and profile itself.
    """
    captured = []

    def fake_build_auth_context(*args):
        """Record the arguments the server hands the shared library."""
        captured.append(args)
        return SimpleNamespace(config={"region": "home"}, signer=object())

    monkeypatch.setattr(auth, "build_auth_context", fake_build_auth_context)
    monkeypatch.setenv("ORACLE_MCP_AUTH_PROFILE", "PROFILE1")
    for name in auth._CANONICAL_AUTH_TYPE_ENV:
        monkeypatch.delenv(name, raising=False)

    # Only the deprecated unseparated spelling is translated.
    monkeypatch.setenv("ORACLE_MCP_AUTH_METHOD", "apikey")
    auth._build_profile_auth_context()
    # Everything else -- including an unset value, which means auto-detect -- is
    # passed through so the library resolves type and profile itself.
    monkeypatch.setenv("ORACLE_MCP_AUTH_METHOD", "session")
    auth._build_profile_auth_context()
    monkeypatch.delenv("ORACLE_MCP_AUTH_METHOD", raising=False)
    auth._build_profile_auth_context()

    assert captured[0][0].auth_type == auth.AuthType.API_KEY
    assert captured[1] == ()
    assert captured[2] == ()


def test_client_factories_use_profile_and_http_auth_paths(monkeypatch):
    """
    Every client factory names itself correctly to the logging wrapper and honors
    the caller's region -- except get_identity_client, which passes none so the
    profile's home region stands. Under stdio the signer comes from the shared
    auth context; under HTTP, from the per-request token exchange.
    """
    monkeypatch.setattr(
        telemetry,
        "_wrap_oci_client",
        lambda client, **kwargs: (client, kwargs["client_name"]),
    )

    recovery_client = MagicMock(return_value="recovery-client")
    database_client = MagicMock(return_value="database-client")
    identity_client = MagicMock(return_value="identity-client")
    monitoring_client = MagicMock(return_value="monitoring-client")
    monkeypatch.setattr(recovery_tools.oci.recovery, "DatabaseRecoveryClient", recovery_client)
    monkeypatch.setattr(recovery_tools.oci.database, "DatabaseClient", database_client)
    monkeypatch.setattr(recovery_tools.oci.identity, "IdentityClient", identity_client)
    monkeypatch.setattr(recovery_tools.oci.monitoring, "MonitoringClient", monitoring_client)

    # apikey/session: config + signer come from the shared auth context.
    profile_signer = object()
    monkeypatch.setattr(auth, "_serving_http", lambda: False)
    monkeypatch.setattr(
        auth,
        "_build_profile_auth_context",
        lambda: SimpleNamespace(config={"region": "home"}, signer=profile_signer),
    )

    assert clients.get_recovery_client(region="us-ashburn-1")[1] == "recovery"
    assert clients.get_database_client(region="us-chicago-1")[1] == "database"
    assert clients.get_identity_client()[1] == "identity"
    assert clients.get_monitoring_client(region="us-ashburn-1")[1] == "monitoring"
    assert recovery_client.call_args.args[0]["region"] == "us-ashburn-1"
    assert database_client.call_args.args[0]["region"] == "us-chicago-1"
    # get_identity_client passes no region, so the profile's home region stands.
    assert identity_client.call_args.args[0]["region"] == "home"
    for client in (recovery_client, database_client, identity_client, monitoring_client):
        assert client.call_args.kwargs["signer"] is profile_signer

    # HTTP: regional config + per-request token-exchange signer.
    http_signer = object()
    monkeypatch.setattr(auth, "_serving_http", lambda: True)
    monkeypatch.setenv("OCI_REGION", "us-ashburn-1")
    monkeypatch.setattr(
        auth,
        "_http_config_and_signer",
        lambda region=None: ({"region": region or "us-ashburn-1"}, http_signer),
    )

    assert clients.get_recovery_client(region="us-phoenix-1")[1] == "recovery"
    assert clients.get_database_client()[1] == "database"
    assert recovery_client.call_args.args[0]["region"] == "us-phoenix-1"
    assert database_client.call_args.args[0]["region"] == "us-ashburn-1"
    assert recovery_client.call_args.kwargs["signer"] is http_signer
    assert database_client.call_args.kwargs["signer"] is http_signer


def test_limits_work_request_and_subscription_client_factories(monkeypatch):
    """
    The remaining three factories follow the same contract: the caller's region
    when given, the resolved home region when not, and the right signer for the
    transport in use.
    """
    profile_signer = object()
    monkeypatch.setattr(auth, "_serving_http", lambda: False)
    monkeypatch.setattr(
        auth,
        "_build_profile_auth_context",
        lambda: SimpleNamespace(config={"region": "home-region"}, signer=profile_signer),
    )
    monkeypatch.setattr(
        telemetry,
        "_wrap_oci_client",
        lambda client, **kwargs: (client, kwargs["client_name"]),
    )

    limits_client = MagicMock(return_value="limits-client")
    work_request_client = MagicMock(return_value="work-request-client")
    monkeypatch.setattr(recovery_tools.oci.limits, "LimitsClient", limits_client)
    monkeypatch.setattr(
        recovery_tools.oci.work_requests, "WorkRequestClient", work_request_client
    )

    assert clients.get_limits_client(region="us-phoenix-1")[1] == "limits"
    assert (
        clients.get_work_request_client(region="us-chicago-1")[1] == "work_requests"
    )
    assert limits_client.call_args.args[0]["region"] == "us-phoenix-1"
    assert work_request_client.call_args.args[0]["region"] == "us-chicago-1"
    assert limits_client.call_args.kwargs["signer"] is profile_signer

    # No explicit region falls back to the resolved profile's home region.
    assert clients.get_limits_client()[1] == "limits"
    assert limits_client.call_args.args[0]["region"] == "home-region"

    http_signer = object()
    monkeypatch.setattr(auth, "_serving_http", lambda: True)
    monkeypatch.setenv("OCI_REGION", "us-ashburn-1")
    monkeypatch.setattr(
        auth,
        "_http_config_and_signer",
        lambda region=None: ({"region": region or "us-ashburn-1"}, http_signer),
    )
    assert clients.get_work_request_client(region="us-sanjose-1")[1] == "work_requests"
    assert clients.get_limits_client(region="us-sanjose-1")[1] == "limits"
    assert work_request_client.call_args.kwargs["signer"] is http_signer
    assert limits_client.call_args.kwargs["signer"] is http_signer
