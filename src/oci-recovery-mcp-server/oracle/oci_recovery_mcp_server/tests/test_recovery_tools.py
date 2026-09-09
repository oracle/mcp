"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_recovery_mcp_server import auth
from oracle.oci_recovery_mcp_server import recovery_tools
from oracle.oci_recovery_mcp_server import cache
from oracle.oci_recovery_mcp_server import clients
from oracle.oci_recovery_mcp_server import compartments
from oracle.oci_recovery_mcp_server import regions
from oracle.oci_recovery_mcp_server import telemetry
import oracle.oci_recovery_mcp_server.server as server
from oracle.oci_recovery_mcp_server.server import mcp


class TestGetClientFactories:
    """
    Request marking and client construction: the opc-request-id every OCI call
    carries, the pseudonyms inside it, and the auth each client factory resolves.
    """
    def test_oci_client_wrapper_adds_mcp_request_marker(self, monkeypatch):
        """
        Every wrapped SDK call carries an opc-request-id naming this installation, the
        caller and the tool. A caller-supplied id is re-marked; one already carrying the
        marker is left alone.
        """

        class FakeClient:
            """A client whose one operation echoes back the request id it was given."""

            def get_resource(self, **kwargs):
                """Return the opc_request_id the wrapper injected."""
                return kwargs["opc_request_id"]

        installation_id = "installation-id"
        monkeypatch.setenv("ORACLE_MCP_INSTALLATION_ID", installation_id)
        actor_id_token = telemetry._MCP_ACTOR_ID_CONTEXT.set("abcdef")
        tool_id_token = telemetry._MCP_TOOL_ID_CONTEXT.set("list_protected_databases")
        try:
            client = telemetry._wrap_oci_client(FakeClient(), request_id="generated-id", client_name="recovery")

            expected_prefix = f"rcvmcp-{telemetry._marker_fragment(installation_id, 8)}-abcdef-lpd"
            assert client.get_resource() == f"{expected_prefix}{telemetry._marker_fragment('generated-id', 6)}"
            assert client.get_resource(opc_request_id="client-id") == f"{expected_prefix}{telemetry._marker_fragment('client-id', 6)}"
            assert client.get_resource(opc_request_id=f"{expected_prefix}deadbeef"[:32]) == f"{expected_prefix}deadbeef"[:32]
        finally:
            telemetry._MCP_TOOL_ID_CONTEXT.reset(tool_id_token)
            telemetry._MCP_ACTOR_ID_CONTEXT.reset(actor_id_token)

    def test_mcp_id_is_a_pseudonym_of_the_authenticated_subject(self, monkeypatch):
        """
        The actor id is derived from the token's subject: stable across calls, six
        characters wide, and never the subject itself.
        """
        access = SimpleNamespace(claims={"iss": "https://idcs-abc", "sub": "user@example.com"})
        monkeypatch.setattr(auth, "get_access_token", lambda: access)

        actor_id = telemetry._mcp_actor_id()

        assert len(actor_id) == 6
        assert actor_id != "user@example.com"
        assert actor_id == telemetry._mcp_actor_id()

    def test_mcp_id_uses_token_jti_when_subject_is_unavailable(self, monkeypatch):
        """A token with no subject falls back to its jti, still pseudonymized."""
        access = SimpleNamespace(claims={"iss": "https://idcs-abc", "jti": "session-token-id"})
        monkeypatch.setattr(auth, "get_access_token", lambda: access)

        actor_id = telemetry._mcp_actor_id()

        assert len(actor_id) == 6
        assert actor_id != "session-token-id"

    def test_mcp_id_uses_fastmcp_session_when_the_token_has_no_principal(self, monkeypatch):
        """
        A token naming neither subject nor jti falls back to the issuer and the FastMCP
        session id, which is likewise not carried through in the clear.
        """
        access = SimpleNamespace(claims={"iss": "https://idcs-abc"})
        monkeypatch.setattr(auth, "get_access_token", lambda: access)
        monkeypatch.setattr(
            "fastmcp.server.dependencies.get_context",
            lambda: SimpleNamespace(session_id="fastmcp-session-id"),
            raising=False,
        )

        actor_id = telemetry._mcp_actor_id()

        assert actor_id == telemetry._marker_fragment("https://idcs-abc:fastmcp-session-id", 6)
        assert actor_id != "fastmcp-session-id"

    def test_mcp_actor_id_prefers_fastmcp_session_for_shared_local_credentials(self, monkeypatch):
        """
        Under a shared local credential the OCI user is the same for everyone, so the
        FastMCP session is what distinguishes one caller from another.
        """
        monkeypatch.setenv("ORACLE_MCP_AUTH_METHOD", "session")
        monkeypatch.setattr(
            "fastmcp.server.dependencies.get_context",
            lambda: SimpleNamespace(session_id="fastmcp-session-id"),
            raising=False,
        )
        monkeypatch.setattr(
            auth,
            "_load_oci_config_for_server",
            lambda: {"user": "shared-oci-user", "tenancy": "tenant-a"},
        )

        assert telemetry._mcp_actor_id() == telemetry._marker_fragment("mcp-session:fastmcp-session-id", 6)

    def test_mcp_id_uses_server_instance_when_no_mcp_context_is_available(self, monkeypatch):
        """
        With no token, no MCP context and no readable OCI config, the actor id falls
        back to this process's own instance id -- which is not persisted, so it cannot
        identify a person across restarts.
        """
        monkeypatch.setattr(auth, "get_access_token", lambda: None)
        monkeypatch.setattr(
            "fastmcp.server.dependencies.get_context",
            lambda: (_ for _ in ()).throw(RuntimeError("no MCP context")),
            raising=False,
        )
        monkeypatch.setattr(
            auth,
            "_load_oci_config_for_server",
            lambda: (_ for _ in ()).throw(RuntimeError("no OCI config")),
        )
        monkeypatch.setattr(telemetry, "_MCP_SERVER_INSTANCE_ID", "server-instance-id")

        assert telemetry._mcp_actor_id() == telemetry._marker_fragment("mcp-server:server-instance-id", 6)

    def test_mcp_installation_id_is_persisted_locally(self, monkeypatch, tmp_path):
        """
        The installation id is generated once, written to the state file, and reused on
        every later call.
        """
        id_file = tmp_path / "state" / "installation-id"
        monkeypatch.delenv("ORACLE_MCP_INSTALLATION_ID", raising=False)
        monkeypatch.setenv("ORACLE_MCP_INSTALLATION_ID_FILE", str(id_file))

        installation_id = telemetry._mcp_installation_id()

        assert len(installation_id) == 8
        assert id_file.exists()
        assert installation_id == telemetry._mcp_installation_id()

    def test_mcp_installation_id_uses_server_configuration(self, monkeypatch):
        """
        A configured installation id is used as given, pseudonymized to eight
        characters.
        """
        monkeypatch.setenv("ORACLE_MCP_INSTALLATION_ID", "hosted-deployment-a")

        assert telemetry._mcp_installation_id() == telemetry._marker_fragment("hosted-deployment-a", 8)

    def test_tool_logger_propagates_mcp_and_tool_ids_to_oci_calls(self, monkeypatch):
        """
        The tool decorator puts the actor and tool ids in scope for the OCI calls the
        tool makes, and clears both once it returns.
        """
        monkeypatch.setattr(telemetry, "_mcp_actor_id", lambda: "abcdef")
        monkeypatch.setenv("ORACLE_MCP_INSTALLATION_ID", "installation-id")

        class FakeClient:
            """A client whose one operation echoes back the request id it was given."""

            def get_resource(self, **kwargs):
                """Return the opc_request_id the wrapper injected."""
                return kwargs["opc_request_id"]

        @telemetry._tool_logger("list_protected_databases")
        def fake_tool():
            """Make one wrapped OCI call and return the request id it carried."""
            client = telemetry._wrap_oci_client(FakeClient(), request_id="generated-id", client_name="recovery")
            return client.get_resource()

        assert fake_tool() == (
            f"rcvmcp-{telemetry._marker_fragment('installation-id', 8)}-abcdef-lpd{telemetry._marker_fragment('generated-id', 6)}"
        )
        assert telemetry._MCP_ACTOR_ID_CONTEXT.get() == "unknown"
        assert telemetry._MCP_TOOL_ID_CONTEXT.get() == "unknown"

    def test_oci_client_wrapper_skips_operations_without_opc_request_id(self):
        """
        An SDK operation that does not accept the kwarg is called without it, rather
        than failing on an argument it does not know.
        """

        class FakeClient:
            """A client whose operation echoes back the kwargs it received."""

            def list_compartments(self, **kwargs):
                """Return the kwargs, so the test can see what the wrapper passed."""
                return kwargs

        client = telemetry._wrap_oci_client(FakeClient(), request_id="generated-id", client_name="identity")

        assert client.list_compartments() == {}
        assert not telemetry._operation_supports_opc_request_id(oci.identity.IdentityClient.list_compartments)

    def test_oci_client_wrapper_marks_operations_without_opc_request_id_kwarg(self, monkeypatch):
        """
        An operation that takes no opc_request_id kwarg is still marked, by way of the
        header the generated SDK code sends.
        """

        class FakeBaseClient:
            """A base client that records the call_api kwargs the operation passed down."""

            def __init__(self):
                """Start with no recorded call."""
                self.call_kwargs = None

            def call_api(self, *args, **kwargs):
                """Record the kwargs and return a canned response."""
                self.call_kwargs = kwargs
                return "response"

        class FakeClient:
            """A generated-style client that reaches the service through its base client."""

            def __init__(self):
                """Attach the recording base client."""
                self.base_client = FakeBaseClient()

            def list_compartments(self, **kwargs):
                """Call through the base client the way generated SDK operations do."""
                return self.base_client.call_api(header_params={"accept": "application/json"})

        monkeypatch.setenv("ORACLE_MCP_INSTALLATION_ID", "installation-id")
        actor_id_token = telemetry._MCP_ACTOR_ID_CONTEXT.set("abcdef")
        tool_id_token = telemetry._MCP_TOOL_ID_CONTEXT.set("list_protected_databases")
        try:
            client = telemetry._wrap_oci_client(FakeClient(), request_id="generated-id", client_name="identity")

            assert client.list_compartments() == "response"
            assert client._inner.base_client.call_kwargs["header_params"]["opc-request-id"] == (
                f"rcvmcp-{telemetry._marker_fragment('installation-id', 8)}-abcdef-lpd{telemetry._marker_fragment('generated-id', 6)}"
            )
        finally:
            telemetry._MCP_TOOL_ID_CONTEXT.reset(tool_id_token)
            telemetry._MCP_ACTOR_ID_CONTEXT.reset(actor_id_token)

    def test_mcp_opc_request_id_fits_oci_preserved_prefix(self, monkeypatch):
        """
        The assembled marker is exactly 32 characters -- the prefix OCI preserves -- so
        no part of it is truncated in the service's own logs.
        """
        monkeypatch.setenv("ORACLE_MCP_INSTALLATION_ID", "installation-id")
        actor_id_token = telemetry._MCP_ACTOR_ID_CONTEXT.set("abcdef")
        tool_id_token = telemetry._MCP_TOOL_ID_CONTEXT.set("list_backups")
        try:
            marker = telemetry._mcp_opc_request_id("generated-id")

            assert marker == f"rcvmcp-{telemetry._marker_fragment('installation-id', 8)}-abcdef-lbk{telemetry._marker_fragment('generated-id', 6)}"
            assert len(marker) == 32
        finally:
            telemetry._MCP_TOOL_ID_CONTEXT.reset(tool_id_token)
            telemetry._MCP_ACTOR_ID_CONTEXT.reset(actor_id_token)

    @patch("oracle.oci_recovery_mcp_server.telemetry._wrap_oci_client", side_effect=lambda client, **_: client)
    @patch("oracle.oci_recovery_mcp_server.recovery_tools.oci.recovery.DatabaseRecoveryClient")
    @patch("oracle.oci_recovery_mcp_server.auth._build_profile_auth_context")
    def test_get_recovery_client_apikey_uses_oracle_mcp_common(
        self,
        mock_build_auth_context,
        mock_client,
        _mock_wrap,
    ):
        """
        The recovery client takes its config and signer from the shared auth context,
        with the caller's region and the derived user agent applied.
        """
        signer = object()
        mock_build_auth_context.return_value = SimpleNamespace(
            config={"region": "us-ashburn-1"}, signer=signer
        )

        result = clients.get_recovery_client(region="us-phoenix-1", request_id="rid")

        mock_build_auth_context.assert_called_once_with()
        args, kwargs = mock_client.call_args
        assert args[0]["region"] == "us-phoenix-1"
        assert args[0]["additional_user_agent"] == f"oci-recovery-mcp/{server.__version__}"
        assert kwargs["signer"] is signer
        assert result is mock_client.return_value

    @patch("oracle.oci_recovery_mcp_server.telemetry._wrap_oci_client", side_effect=lambda client, **_: client)
    @patch("oracle.oci_recovery_mcp_server.recovery_tools.oci.monitoring.MonitoringClient")
    @patch("oracle.oci_recovery_mcp_server.auth._build_profile_auth_context")
    def test_get_monitoring_client_session_uses_oracle_mcp_common_signer(
        self,
        mock_build_auth_context,
        mock_client,
        _mock_wrap,
    ):
        """The monitoring client follows the same path as the recovery client."""
        signer = object()
        mock_build_auth_context.return_value = SimpleNamespace(
            config={"region": "us-ashburn-1"}, signer=signer
        )

        result = clients.get_monitoring_client(region="us-phoenix-1", request_id="rid")

        args, kwargs = mock_client.call_args
        assert args[0]["region"] == "us-phoenix-1"
        assert args[0]["additional_user_agent"] == f"oci-recovery-mcp/{server.__version__}"
        assert kwargs["signer"] is signer
        assert result is mock_client.return_value

    @patch("oracle.oci_recovery_mcp_server.recovery_tools.oci.config.from_file")
    def test_legacy_auth_method_spellings_all_keep_working(
        self, mock_from_file, monkeypatch
    ):
        """
        Every ORACLE_MCP_AUTH_METHOD spelling this server has documented still works.

        oracle-mcp-common reads the variable itself and understands "session",
        "api_key" and "api-key". It does NOT understand the unseparated "apikey" this
        server documented in 2.x -- an unrecognized value is a hard error there -- so
        only that one is translated here.
        """
        from oracle_mcp_common import AuthType

        captured = {}

        def fake_build_auth_context(*args):
            """Record what the server forces, if anything."""
            captured["args"] = args
            return SimpleNamespace(config={}, signer=object())

        monkeypatch.setattr(
            "oracle.oci_recovery_mcp_server.auth.build_auth_context",
            fake_build_auth_context,
        )

        monkeypatch.setenv("ORACLE_MCP_AUTH_METHOD", "apikey")
        auth._build_profile_auth_context()
        assert captured["args"][0].auth_type == AuthType.API_KEY

        for shared_spelling in ("api_key", "api-key", "session"):
            captured.clear()
            monkeypatch.setenv("ORACLE_MCP_AUTH_METHOD", shared_spelling)
            auth._build_profile_auth_context()
            # Passed through untouched: the library resolves it from the same env var.
            assert captured["args"] == ()

    def test_profile_name_resolution_follows_the_shared_library(self, monkeypatch):
        """
        The informational config read resolves the same profile the signer used.

        The library resolves OCI_CONFIG_PROFILE before ORACLE_MCP_AUTH_PROFILE;
        resolving them in the opposite order here would read a different profile than
        the credentials whenever both are set.
        """
        from oracle_mcp_common import resolve_profile_name

        monkeypatch.setenv("OCI_CONFIG_PROFILE", "FROM_OCI")
        monkeypatch.setenv("ORACLE_MCP_AUTH_PROFILE", "FROM_ORACLE")
        seen = {}

        def fake_from_file(file_location, profile_name):
            """Record which profile the config read asked for."""
            seen["profile"] = profile_name
            return {"region": "us-ashburn-1"}

        monkeypatch.setattr(recovery_tools.oci.config, "from_file", fake_from_file)
        auth._load_oci_config_for_server()

        assert seen["profile"] == resolve_profile_name() == "FROM_OCI"


def _fake_oci_provider(captured):
    """Stand in for FastMCP's OCIProvider, mirroring the hooks the server overrides."""

    class FakeOCIProvider:
        """A stand-in for FastMCP's OCIProvider, recording what the server hands it."""

        # _cimd_manager mirrors the real provider: the server clears it so client
        # registration never depends on an outbound metadata fetch.
        _cimd_manager = object()

        def __init__(self, **kwargs):
            """Seed required_scopes from the verifier's copy, as the real provider does."""
            # The real provider seeds required_scopes from the verifier's copy, and
            # FastMCP hands this same list to RequireAuthMiddleware, so it has to
            # stay bare.
            self.required_scopes: list[str] = list(kwargs.get("required_scopes") or [])
            captured.update(kwargs)
            captured["provider"] = self

        def update_default_scopes(self, scopes):
            """Record the scopes advertised to clients."""
            captured["default_scopes"] = list(scopes)

        def _build_upstream_authorize_url(self, txn_id, transaction):
            """Record the scopes the /authorize request would carry."""
            # Stands in for the real URL builder: only the scopes it was handed
            # matter here.
            captured["authorize_scopes"] = list(transaction.get("scopes") or [])
            return f"https://idcs.example.com/authorize?state={txn_id}"

        def _prepare_scopes_for_upstream_refresh(self, scopes):
            """Return the scopes unchanged, letting the server's override qualify them."""
            return scopes

    return FakeOCIProvider


class TestHttpTransportAuth:
    """HTTP transport authenticates each caller against an OCI IAM (IDCS) domain."""

    @pytest.fixture(autouse=True)
    def _reset_http_auth(self):
        """Clear the module-level HTTP auth policy around each test."""
        auth._http_auth = None
        yield
        auth._http_auth = None

    def _idcs_env(self, monkeypatch):
        """Set the IDCS environment a hosted deployment is configured with."""
        for name, value in {
            "IDCS_DOMAIN": "idcs-abc.identity.oraclecloud.com",
            "IDCS_CLIENT_ID": "cid",
            "IDCS_CLIENT_SECRET": "csec",
            "IDCS_AUDIENCE": "https://recovery.example.com",
            "ORACLE_MCP_BASE_URL": "https://mcp.example.com",
            "OCI_REGION": "us-ashburn-1",
        }.items():
            monkeypatch.setenv(name, value)
        monkeypatch.delenv("IDCS_REQUIRED_SCOPES", raising=False)

    def test_unset_auth_method_leaves_auto_detection_to_the_shared_library(
        self, monkeypatch
    ):
        """
        With ORACLE_MCP_AUTH_METHOD unset, nothing is forced and the library auto-detects.

        Forcing an auth type here would defeat oracle-mcp-common's "auto" mode, which
        picks security-token only when the profile directly declares a
        security_token_file. An API-key-only profile would then be rejected for not
        declaring one.
        """
        monkeypatch.delenv("ORACLE_MCP_AUTH_METHOD", raising=False)
        captured = {}

        def fake_build_auth_context(*args):
            """Record what the server forces, if anything."""
            captured["args"] = args
            return SimpleNamespace(config={}, signer=object())

        monkeypatch.setattr(
            "oracle.oci_recovery_mcp_server.auth.build_auth_context",
            fake_build_auth_context,
        )
        auth._build_profile_auth_context()
        assert captured["args"] == ()  # nothing forced; the library decides
        assert auth._resolved_auth_type_label() == "auto"

    def test_canonical_auth_type_outranks_the_deprecated_spelling(self, monkeypatch):
        """
        A canonical auth-type variable wins over the deprecated "apikey" spelling.

        The translated value is passed as an explicit AuthOptions, which outranks every
        environment variable inside resolve_auth_type(). Applying it while
        OCI_MCP_AUTH_TYPE is set would let the deprecated name win -- and
        security_token + apikey would then sign requests with the profile's API key,
        which OCI rejects with 401 after an apparently successful startup.
        """
        captured = {}

        def fake_build_auth_context(*args):
            """Record what the server forces, if anything."""
            captured["args"] = args
            return SimpleNamespace(config={}, signer=object())

        monkeypatch.setattr(
            "oracle.oci_recovery_mcp_server.auth.build_auth_context",
            fake_build_auth_context,
        )
        monkeypatch.setenv("ORACLE_MCP_AUTH_METHOD", "apikey")

        for canonical in auth._CANONICAL_AUTH_TYPE_ENV:
            for name in auth._CANONICAL_AUTH_TYPE_ENV:
                monkeypatch.delenv(name, raising=False)
            monkeypatch.setenv(canonical, "security_token")

            assert auth._deprecated_auth_method_override() is None
            auth._build_profile_auth_context()
            assert captured["args"] == ()  # the library resolves security_token
            assert auth._resolved_auth_type_label() == "security_token"

        # With no canonical variable set, the deprecated spelling still works.
        for name in auth._CANONICAL_AUTH_TYPE_ENV:
            monkeypatch.delenv(name, raising=False)
        auth._build_profile_auth_context()
        assert captured["args"][0].auth_type is auth.AuthType.API_KEY

    def test_default_scopes_gate_on_the_recovery_invoke_scope(self, monkeypatch):
        """
        With no override configured, the required scopes include the Recovery Service
        invoke scope alongside the OIDC defaults.
        """
        monkeypatch.delenv("IDCS_REQUIRED_SCOPES", raising=False)
        assert auth._required_scopes() == [
            "openid",
            "profile",
            "email",
            "oci_mcp.recovery.invoke",
        ]

    def test_required_scopes_can_be_overridden(self, monkeypatch):
        """IDCS_REQUIRED_SCOPES replaces the default list entirely."""
        monkeypatch.setenv("IDCS_REQUIRED_SCOPES", "openid offline_access")
        assert auth._required_scopes() == ["openid", "offline_access"]

    def test_serving_http_is_false_outside_a_request(self, monkeypatch):
        """
        With neither an access token nor an HTTP request in scope, the server is not
        serving HTTP.
        """
        monkeypatch.setattr(auth, "get_access_token", lambda: None)
        monkeypatch.setattr(
            auth,
            "get_http_request",
            lambda: (_ for _ in ()).throw(RuntimeError("no http request")),
        )
        assert auth._serving_http() is False

    def test_serving_http_is_true_for_an_authenticated_caller(self, monkeypatch):
        """An access token in scope means the server is serving HTTP."""
        monkeypatch.setattr(
            auth, "get_access_token", lambda: SimpleNamespace(token="tok", claims={})
        )
        assert auth._serving_http() is True

    def test_get_tenancy_over_http_requires_an_explicit_tenancy(self, monkeypatch):
        """
        Over HTTP the tenancy must be configured; there is no fallback.

        A hosted deployment has no OCI config file, so falling back to one would
        silently serve whatever tenancy happens to be configured on the host.
        """
        monkeypatch.setattr(auth, "_serving_http", lambda: True)
        for name in ("OCI_MCP_TENANCY_ID_OVERRIDE", "ORACLE_MCP_TENANCY_ID", "TENANCY_ID_OVERRIDE"):
            monkeypatch.delenv(name, raising=False)
        with pytest.raises(RuntimeError, match="OCI_MCP_TENANCY_ID_OVERRIDE"):
            auth.get_tenancy()

        monkeypatch.setenv("ORACLE_MCP_TENANCY_ID", "ocid1.tenancy.oc1..hosted")
        assert auth.get_tenancy() == "ocid1.tenancy.oc1..hosted"

    def test_get_tenancy_reads_the_name_the_shared_library_documents(self, monkeypatch):
        """
        OCI_MCP_TENANCY_ID_OVERRIDE is honored, and outranks the older spellings.

        That is the name oracle-mcp-common reads and documents, with the other two
        listed there as its legacy aliases. This server read only the aliases, so a
        deployment configured from the shared library's own documentation set a
        variable nothing here looked at, and the tenancy lookup fell through to a
        RuntimeError over HTTP.
        """
        monkeypatch.setattr(auth, "_serving_http", lambda: True)
        for name in ("OCI_MCP_TENANCY_ID_OVERRIDE", "ORACLE_MCP_TENANCY_ID", "TENANCY_ID_OVERRIDE"):
            monkeypatch.delenv(name, raising=False)

        monkeypatch.setenv("OCI_MCP_TENANCY_ID_OVERRIDE", "ocid1.tenancy.oc1..canonical")
        assert auth.get_tenancy() == "ocid1.tenancy.oc1..canonical"

        # Set alongside the older names, the canonical one still wins.
        monkeypatch.setenv("ORACLE_MCP_TENANCY_ID", "ocid1.tenancy.oc1..oracle")
        monkeypatch.setenv("TENANCY_ID_OVERRIDE", "ocid1.tenancy.oc1..legacy")
        assert auth.get_tenancy() == "ocid1.tenancy.oc1..canonical"

        # And the legacy names keep working for deployments already using them.
        monkeypatch.delenv("OCI_MCP_TENANCY_ID_OVERRIDE")
        assert auth.get_tenancy() == "ocid1.tenancy.oc1..oracle"
        monkeypatch.delenv("ORACLE_MCP_TENANCY_ID")
        assert auth.get_tenancy() == "ocid1.tenancy.oc1..legacy"

    @patch(
        "oracle.oci_recovery_mcp_server.telemetry._wrap_oci_client",
        side_effect=lambda client, **_: client,
    )
    @patch("oracle.oci_recovery_mcp_server.recovery_tools.oci.recovery.DatabaseRecoveryClient")
    def test_make_client_over_http_uses_the_shared_idcs_request_context(
        self, mock_client, _mock_wrap, monkeypatch
    ):
        """
        Over HTTP the client is built from the shared library's per-request context
        rather than from any local profile.
        """
        signer = object()
        monkeypatch.setattr(auth, "_serving_http", lambda: True)
        monkeypatch.setattr(
            auth,
            "_http_config_and_signer",
            lambda region=None: ({"region": region}, signer),
        )

        result = clients.get_recovery_client(region="us-phoenix-1", request_id="rid")

        args, kwargs = mock_client.call_args
        assert args[0]["region"] == "us-phoenix-1"
        assert kwargs["signer"] is signer
        assert result is mock_client.return_value

    def test_http_token_exchange_carries_the_derived_user_agent(self, monkeypatch):
        """
        The token-exchange config carries the derived additional_user_agent.

        BEST_PRACTICES requires it on every client-construction path, HTTP included.
        context_for() returns only {"region": ...}, so the server must add it here or
        the hosted deployment's OCI calls go out untagged.
        """
        from oracle_mcp_common import IDCSHttpAuth

        auth._http_auth = IDCSHttpAuth(
            provider=object(),
            _identity_domain_url="https://idcs-abc.identity.oraclecloud.com",
            _client_id="cid",
            _client_secret="csec",
            _configured_region="us-ashburn-1",
        )
        monkeypatch.setattr(
            auth, "get_access_token", lambda: SimpleNamespace(token="tok", claims={})
        )
        with patch("oci.auth.signers.TokenExchangeSigner"):
            config, _signer = auth._http_config_and_signer(region="us-phoenix-1")

        assert config["additional_user_agent"] == f"oci-recovery-mcp/{server.__version__}"
        assert config["additional_user_agent"] == auth._ADDITIONAL_UA
        assert config["region"] == "us-phoenix-1"

    def test_http_client_construction_carries_the_derived_user_agent(self, monkeypatch):
        """
        The same check end to end through _make_client, so a regression in either the
        policy or the client factory is caught.
        """
        from oracle_mcp_common import IDCSHttpAuth

        auth._http_auth = IDCSHttpAuth(
            provider=object(),
            _identity_domain_url="https://idcs-abc.identity.oraclecloud.com",
            _client_id="cid",
            _client_secret="csec",
            _configured_region="us-ashburn-1",
        )
        monkeypatch.setattr(
            auth, "get_access_token", lambda: SimpleNamespace(token="tok", claims={})
        )
        monkeypatch.setattr(telemetry, "_wrap_oci_client", lambda client, **_: client)

        with patch("oci.auth.signers.TokenExchangeSigner"), patch(
            "oracle.oci_recovery_mcp_server.recovery_tools.oci.recovery.DatabaseRecoveryClient"
        ) as mock_client:
            clients.get_recovery_client(region="us-phoenix-1", request_id="rid")

        args, _kwargs = mock_client.call_args
        assert args[0]["additional_user_agent"] == f"oci-recovery-mcp/{server.__version__}"

    def test_request_signer_is_never_reused_across_calls(self, monkeypatch):
        """
        Every HTTP call gets its own signer -- there is no process-wide cache.

        Each call asks oracle-mcp-common's context_for() for a signer scoped to the
        request that established the caller's identity, even for the same token jti.
        Only the policy (provider plus server-side credentials) is long-lived, built
        once in main().
        """
        from oracle_mcp_common import IDCSHttpAuth

        made = []

        class FakeTES:
            """A token-exchange signer that records each construction."""

            def __init__(self, *args, **kwargs):
                """Record the arguments this signer was built from."""
                made.append((args, kwargs))

        auth._http_auth = IDCSHttpAuth(
            provider=object(),
            _identity_domain_url="https://idcs-abc.identity.oraclecloud.com",
            _client_id="cid",
            _client_secret="csec",
            _configured_region="us-ashburn-1",
        )
        monkeypatch.setattr(
            auth, "get_access_token", lambda: SimpleNamespace(token="tok", claims={"jti": "j"})
        )
        with patch("oci.auth.signers.TokenExchangeSigner", FakeTES):
            _, s1 = auth._http_config_and_signer()
            _, s2 = auth._http_config_and_signer()

        assert s1 is not s2  # same caller + jti -> still a new signer, no cache
        assert len(made) == 2
        assert not hasattr(server, "_signer_cache")
        # the exchange runs on the deployment's own credentials, via the shared library
        assert made[0][0] == ("tok", "https://idcs-abc.identity.oraclecloud.com", "cid", "csec")

    def test_http_signer_requires_an_initialized_policy(self, monkeypatch):
        """
        Asking for a signer before the HTTP auth policy is built is an error, not a
        silent fallback.
        """
        auth._http_auth = None
        with pytest.raises(RuntimeError, match="has not been initialized"):
            auth._http_config_and_signer()

    def test_http_signer_requires_an_authenticated_caller(self, monkeypatch):
        """An unauthenticated HTTP caller cannot obtain a signer."""

        class RejectingAuth:
            """An auth policy that refuses every unauthenticated caller."""

            def context_for(self, token, *, region=None):
                """Refuse, the way the real policy does for a missing token."""
                raise ValueError("HTTP requests require an authenticated IDCS access token.")

        auth._http_auth = RejectingAuth()
        monkeypatch.setattr(auth, "get_access_token", lambda: None)
        monkeypatch.setattr(auth, "get_http_request", lambda: object())
        with pytest.raises(RuntimeError, match="OCI UPST token exchange failed"):
            auth._http_config_and_signer()

    def test_http_signer_surfaces_the_iam_error_body(self, monkeypatch):
        """
        The IAM response body reaches the operator-facing message.

        context_for() wraps SDK failures, so the body hangs off the wrapped cause; it
        must still be surfaced.
        """
        cause = RuntimeError("boom")
        cause.response = SimpleNamespace(status_code=401, text="invalid_grant")
        wrapped = ValueError("Unable to construct the HTTP IDCS token-exchange signer")
        wrapped.__cause__ = cause

        class FailingAuth:
            """An auth policy that fails with an IAM rejection wrapped in a cause."""

            def context_for(self, _token, *, region=None):
                """Raise the pre-built wrapped failure."""
                raise wrapped

        auth._http_auth = FailingAuth()
        monkeypatch.setattr(
            auth, "get_access_token", lambda: SimpleNamespace(token="tok", claims={})
        )
        with pytest.raises(RuntimeError, match="IAM 401: invalid_grant"):
            auth._http_config_and_signer()

    def test_http_signer_error_never_leaks_the_client_secret(self, monkeypatch):
        """
        Neither the raised message, the log record, nor the policy's repr carries the
        client secret or the caller's token.

        The IAM diagnostic body is surfaced to the operator, so the failure path must
        not also carry the confidential application's credentials or the caller's own
        token along with it.
        """
        from oracle_mcp_common import IDCSHttpAuth

        secret = "super-secret-client-value"
        policy = IDCSHttpAuth(
            provider=object(),
            _identity_domain_url="https://idcs-abc.identity.oraclecloud.com",
            _client_id="cid",
            _client_secret=secret,
            _configured_region="us-ashburn-1",
        )
        auth._http_auth = policy
        monkeypatch.setattr(
            auth, "get_access_token", lambda: SimpleNamespace(token="caller-jwt", claims={})
        )

        records = []
        monkeypatch.setattr(
            server.logger, "error", lambda *a, **k: records.append((a, k))
        )

        def _boom(*_a, **_k):
            """Fail the way a real IAM rejection does, with the response on the cause."""
            # context_for() wraps this once, so the response hangs off __cause__,
            # exactly as it does for a real IAM rejection.
            error = RuntimeError("boom")
            error.response = SimpleNamespace(status_code=401, text="invalid_grant")
            raise error

        with patch("oci.auth.signers.TokenExchangeSigner", _boom):
            with pytest.raises(RuntimeError) as excinfo:
                auth._http_config_and_signer()

        message = str(excinfo.value)
        assert "IAM 401: invalid_grant" in message
        assert secret not in message
        assert "caller-jwt" not in message
        assert all(secret not in str(r) and "caller-jwt" not in str(r) for r in records)
        # The frozen dataclass keeps the secret out of its own repr as well.
        assert secret not in repr(policy)

    def test_build_http_auth_configures_the_shared_library_provider(self, monkeypatch):
        """
        The shared builder constructs the provider with this deployment's IDCS
        settings, and the verifier's scope copy stays bare -- IDCS returns the scope
        unqualified in the access token, which is what each request is validated
        against.
        """
        self._idcs_env(monkeypatch)
        monkeypatch.setenv("IDCS_REQUIRED_SCOPES", "openid offline_access")
        captured = {}

        # Patch the provider inside oracle-mcp-common: the shared builder, not this
        # server, is what constructs it.
        with patch("oracle_mcp_common.auth.OCIProvider", _fake_oci_provider(captured)):
            http_auth = auth._build_http_auth()

        assert http_auth.provider is captured["provider"]
        assert captured["base_url"] == "https://mcp.example.com"
        assert captured["audience"] == "https://recovery.example.com"
        assert captured["client_id"] == "cid"
        assert (
            captured["config_url"]
            == "https://idcs-abc.identity.oraclecloud.com/.well-known/openid-configuration"
        )
        # The verifier's copy stays bare: IDCS returns the scope unqualified in the
        # access token, and that is what every request is re-validated against.
        assert list(captured["required_scopes"]) == ["openid", "offline_access"]

    def test_build_http_auth_requires_the_idcs_settings(self, monkeypatch):
        """
        Missing IDCS configuration fails the build rather than starting an
        unauthenticated listener.
        """
        for name in (
            "IDCS_DOMAIN",
            "IDCS_CLIENT_ID",
            "IDCS_CLIENT_SECRET",
            "IDCS_AUDIENCE",
            "ORACLE_MCP_BASE_URL",
        ):
            monkeypatch.delenv(name, raising=False)

        with pytest.raises(ValueError, match="IDCS_DOMAIN"):
            auth._build_http_auth()

    def test_resource_scopes_are_qualified_with_the_audience_upstream(self, monkeypatch):
        """
        Every surface that reaches IDCS carries the qualified scope; everything
        compared against an issued token stays bare.

        IDCS names a resource scope as audience+scope with no separator and rejects the
        bare form at /authorize with invalid_scope.
        """
        self._idcs_env(monkeypatch)
        monkeypatch.setenv(
            "IDCS_REQUIRED_SCOPES", "openid offline_access oci_mcp.recovery.invoke"
        )
        captured = {}

        with patch("oracle_mcp_common.auth.OCIProvider", _fake_oci_provider(captured)):
            http_auth = auth._build_http_auth()

        provider = http_auth.provider
        bare = ["openid", "offline_access", "oci_mcp.recovery.invoke"]
        qualified = "https://recovery.example.comoci_mcp.recovery.invoke"
        # advertised to clients (DCR defaults, valid_scopes, metadata)
        assert captured["default_scopes"] == ["openid", "offline_access", qualified]
        # the /authorize request itself, built from what the client asked for
        provider._build_upstream_authorize_url("txn", {"scopes": list(bare)})
        assert captured["authorize_scopes"] == ["openid", "offline_access", qualified]
        # and from required_scopes when the client sends no scope parameter at all
        provider._build_upstream_authorize_url("txn", {})
        assert captured["authorize_scopes"] == ["openid", "offline_access", qualified]
        # and the refresh request, which is built from the bare scopes IDCS stored
        assert provider._prepare_scopes_for_upstream_refresh(
            ["openid", "oci_mcp.recovery.invoke"]
        ) == ["openid", qualified]
        # a refresh token carrying no scopes falls back to the configured list
        assert provider._prepare_scopes_for_upstream_refresh([]) == [
            "openid",
            "offline_access",
            qualified,
        ]
        # the verifier's copy stays bare: IDCS returns the scope unqualified in the
        # access token, and that is what every request is re-validated against
        assert captured["required_scopes"] == bare

    def test_request_time_scope_checks_are_left_bare(self, monkeypatch):
        """
        The provider's required_scopes stay bare.

        FastMCP builds its transport routes from that list (fastmcp/server/http.py) and
        hands it to RequireAuthMiddleware, which compares it to the bare scope claim of
        the IDCS access token. Qualifying it would return insufficient_scope on every
        request of a session that signed in successfully.
        """
        self._idcs_env(monkeypatch)
        monkeypatch.setenv(
            "IDCS_REQUIRED_SCOPES", "openid offline_access oci_mcp.recovery.invoke"
        )
        captured = {}

        with patch("oracle_mcp_common.auth.OCIProvider", _fake_oci_provider(captured)):
            http_auth = auth._build_http_auth()

        assert http_auth.provider.required_scopes == list(captured["required_scopes"])

    def test_startup_fails_if_fastmcp_drops_a_scope_hook(self, monkeypatch):
        """
        A provider missing the scope hooks fails startup loudly.

        Silently skipping the qualification would fail every sign-in with
        invalid_scope, far from the upgrade that caused it.
        """
        self._idcs_env(monkeypatch)

        class ProviderWithoutScopeHooks:
            """A provider that has lost the hooks the server overrides."""

            _cimd_manager = object()

            def __init__(self, **kwargs):
                """Accept any configuration and keep none of it."""
                pass

        with patch("oracle_mcp_common.auth.OCIProvider", ProviderWithoutScopeHooks):
            with pytest.raises(RuntimeError, match="update_default_scopes"):
                auth._build_http_auth()

    def test_cimd_client_registration_is_disabled(self, monkeypatch):
        """
        Client registration never depends on an outbound metadata fetch.

        CIMD would make registration depend on this host reaching the client's metadata
        URL, which a VPN-only deployment cannot do. DCR is used instead.
        """
        self._idcs_env(monkeypatch)
        captured = {}

        with patch("oracle_mcp_common.auth.OCIProvider", _fake_oci_provider(captured)):
            http_auth = auth._build_http_auth()

        assert http_auth.provider._cimd_manager is None

    def test_startup_fails_if_cimd_cannot_be_disabled(self, monkeypatch):
        """
        A provider whose CIMD manager cannot be cleared fails startup rather than
        serving with client registration silently depending on an outbound fetch.
        """
        self._idcs_env(monkeypatch)

        class ProviderWithoutCimd:
            """A provider carrying the scope hooks but no clearable CIMD manager."""

            def __init__(self, **kwargs):
                """Start with an empty scope list."""
                self.required_scopes = []

            def update_default_scopes(self, scopes):
                """Accept the advertised scopes and discard them."""
                pass

            def _build_upstream_authorize_url(self, txn_id, transaction):
                """Return an empty URL; only the hook's presence matters here."""
                return ""

            def _prepare_scopes_for_upstream_refresh(self, scopes):
                """Return the scopes unchanged."""
                return scopes

        with patch("oracle_mcp_common.auth.OCIProvider", ProviderWithoutCimd):
            with pytest.raises(RuntimeError, match="_cimd_manager"):
                auth._build_http_auth()


class TestCachePartitioning:
    """In-process caches must never serve one tenancy's or one caller's data to another."""

    def test_region_subscriptions_are_never_served_from_a_cache(self, monkeypatch):
        """
        Subscribed regions are re-read from IAM on every call.

        Whether a caller may list them is decided by their own IAM policy, and that
        decision is only made by the IAM call itself -- so answering from a cache
        would let a caller who never had the permission, or who has since lost it,
        keep reading. One tenancy's list must never reach another either.
        """
        calls = []

        def fake_identity(*, request_id=None):
            """Serve a different region per tenancy, recording who asked."""

            def list_region_subscriptions(tenancy_id):
                """Return this tenancy's one subscribed region."""
                calls.append(tenancy_id)
                name = "us-ashburn-1" if tenancy_id == "tA" else "us-phoenix-1"
                return SimpleNamespace(
                    data=[SimpleNamespace(region_name=name, status="READY")]
                )

            return SimpleNamespace(list_region_subscriptions=list_region_subscriptions)

        monkeypatch.setattr(clients, "get_identity_client", fake_identity)

        monkeypatch.setattr(auth, "get_tenancy", lambda: "tA")
        a1 = regions._iam_subscribed_regions_with_status(request_id="r")
        monkeypatch.setattr(auth, "get_tenancy", lambda: "tB")
        b1 = regions._iam_subscribed_regions_with_status(request_id="r")
        monkeypatch.setattr(auth, "get_tenancy", lambda: "tA")
        a2 = regions._iam_subscribed_regions_with_status(request_id="r")

        assert a1 == [{"region": "us-ashburn-1", "status": "READY"}]
        assert b1 == [{"region": "us-phoenix-1", "status": "READY"}]  # no leak from tA
        assert a1 == a2
        # tA's second lookup goes back to IAM rather than reusing its first answer,
        # so the caller's current permissions decide it.
        assert calls == ["tA", "tB", "tA"]

    def test_compartment_cache_partitioned_by_tenant(self, monkeypatch):
        """One tenancy's compartment listing is never served to another."""
        compartments._STORE.clear()
        seq = {"tA": [SimpleNamespace(id="cA")], "tB": [SimpleNamespace(id="cB")]}
        calls = []

        def fake_list(only_one_page, limit=100):
            """Serve the current tenancy's compartments, recording who asked."""
            t = auth.get_tenancy()
            calls.append(t)
            return list(seq[t])

        monkeypatch.setattr(compartments, "list_all_compartments_internal", fake_list)
        monkeypatch.setattr(
            clients,
            "get_identity_client",
            lambda **k: SimpleNamespace(
                get_compartment=lambda compartment_id: SimpleNamespace(
                    data=SimpleNamespace(id=compartment_id)
                )
            ),
        )

        monkeypatch.setattr(auth, "get_tenancy", lambda: "tA")
        a = compartments._list_all_compartments_cached(request_id="r")
        monkeypatch.setattr(auth, "get_tenancy", lambda: "tB")
        b = compartments._list_all_compartments_cached(request_id="r")
        monkeypatch.setattr(auth, "get_tenancy", lambda: "tA")
        compartments._list_all_compartments_cached(request_id="r")

        ids_a = [getattr(c, "id", None) for c in a]
        ids_b = [getattr(c, "id", None) for c in b]
        assert "cA" in ids_a and "cB" in ids_b
        assert "cB" not in ids_a  # tenant B never leaks into tenant A
        assert calls == ["tA", "tB"]  # tA's 2nd call served from its own cache

    def test_compartment_cache_partitioned_by_caller_within_a_tenant(self, monkeypatch):
        """
        Two callers in the same tenancy never share a compartment cache entry.

        The listing is fetched with access_level="ACCESSIBLE", so it reflects the
        calling identity's permissions: sharing an entry would serve a
        broadly-permissioned user's compartment tree to a restricted one.
        """
        compartments._STORE.clear()
        current = {"sub": "alice"}
        visible = {"alice": [SimpleNamespace(id="c-all")], "bob": [SimpleNamespace(id="c-few")]}
        calls = []

        def fake_list(only_one_page, limit=100):
            """Serve the current caller's visible compartments, recording who asked."""
            calls.append(current["sub"])
            return list(visible[current["sub"]])

        monkeypatch.setattr(compartments, "list_all_compartments_internal", fake_list)
        monkeypatch.setattr(auth, "get_tenancy", lambda: "same-tenancy")
        monkeypatch.setattr(auth, "_serving_http", lambda: True)
        monkeypatch.setattr(
            clients,
            "get_identity_client",
            lambda **k: SimpleNamespace(
                get_compartment=lambda compartment_id: SimpleNamespace(
                    data=SimpleNamespace(id=compartment_id)
                )
            ),
        )
        monkeypatch.setattr(
            auth,
            "get_access_token",
            lambda: SimpleNamespace(claims={"sub": current["sub"]}, token="tok"),
        )

        alice = compartments._list_all_compartments_cached(request_id="r")
        current["sub"] = "bob"
        bob = compartments._list_all_compartments_cached(request_id="r")
        current["sub"] = "alice"
        compartments._list_all_compartments_cached(request_id="r")

        assert "c-all" in [getattr(c, "id", None) for c in alice]
        ids_bob = [getattr(c, "id", None) for c in bob]
        assert "c-few" in ids_bob
        assert "c-all" not in ids_bob  # alice's compartments never reach bob
        assert calls == ["alice", "bob"]  # alice's 2nd call served from her own entry

    def test_compartment_cache_partitioned_when_tokens_omit_sub(self, monkeypatch):
        """
        Two callers whose tokens carry no subject and share a registered client_id are
        still kept apart, by their per-session tokens.
        """
        compartments._STORE.clear()
        current = {"token": "token-alice"}
        visible = {
            "token-alice": [SimpleNamespace(id="c-all")],
            "token-bob": [SimpleNamespace(id="c-few")],
        }
        calls = []

        def fake_list(only_one_page, limit=100):
            """Serve the current token's visible compartments, recording who asked."""
            calls.append(current["token"])
            return list(visible[current["token"]])

        monkeypatch.setattr(compartments, "list_all_compartments_internal", fake_list)
        monkeypatch.setattr(auth, "get_tenancy", lambda: "same-tenancy")
        monkeypatch.setattr(auth, "_serving_http", lambda: True)
        monkeypatch.setattr(
            clients,
            "get_identity_client",
            lambda **k: SimpleNamespace(
                get_compartment=lambda compartment_id: SimpleNamespace(
                    data=SimpleNamespace(id=compartment_id)
                )
            ),
        )
        monkeypatch.setattr(
            auth,
            "get_access_token",
            lambda: SimpleNamespace(
                claims={}, client_id="shared-client", token=current["token"]
            ),
        )

        alice = compartments._list_all_compartments_cached(request_id="r")
        current["token"] = "token-bob"
        bob = compartments._list_all_compartments_cached(request_id="r")

        ids_bob = [getattr(c, "id", None) for c in bob]
        assert "c-all" in [getattr(c, "id", None) for c in alice]
        assert "c-few" in ids_bob
        assert "c-all" not in ids_bob  # the shared client_id must not merge them
        assert calls == ["token-alice", "token-bob"]  # bob got no cache hit

    def test_caller_cache_key_never_shares_an_entry_without_an_identity(self, monkeypatch):
        """
        With no usable caller identity in oauth mode the key isolates rather than
        falling back to a shared one -- that fallback is the failure this partitioning
        exists to prevent.
        """
        monkeypatch.setattr(auth, "_serving_http", lambda: True)
        monkeypatch.setattr(auth, "get_access_token", lambda: None)
        assert cache._caller_cache_key() != cache._caller_cache_key()

    def test_caller_cache_key_isolates_tokens_sharing_one_oauth_client_id(self, monkeypatch):
        """
        A client_id names the registered application, not the human, so several users
        of one MCP client share it. It never reaches the key.
        """
        monkeypatch.setattr(auth, "_serving_http", lambda: True)
        current = {"token": "token-alice"}
        monkeypatch.setattr(
            "fastmcp.server.dependencies.get_access_token",
            lambda: SimpleNamespace(claims={}, client_id="shared-client", token=current["token"]),
            raising=False,
        )
        alice = cache._caller_cache_key()
        current["token"] = "token-bob"
        bob = cache._caller_cache_key()

        assert alice and bob
        assert alice != bob
        assert "shared-client" not in alice + bob

    def test_caller_cache_key_uses_jti_when_the_token_omits_sub(self, monkeypatch):
        """
        For distinct sessions of one registered client, jti separates the callers and,
        unlike the raw token, stays stable for that token's life.
        """
        monkeypatch.setattr(auth, "_serving_http", lambda: True)
        current = {"jti": "jti-alice"}
        monkeypatch.setattr(
            auth,
            "get_access_token",
            lambda: SimpleNamespace(
                claims={"jti": current["jti"]}, client_id="shared-client", token="tok"
            ),
        )
        alice = cache._caller_cache_key()
        assert alice == cache._caller_cache_key()  # stable across calls
        current["jti"] = "jti-bob"
        assert cache._caller_cache_key() != alice

    def test_caller_cache_key_is_inert_for_profile_auth(self, monkeypatch):
        """
        Under stdio there is one process and one operator credential, so there is
        nothing to partition.
        """
        monkeypatch.setattr(auth, "_serving_http", lambda: False)
        assert cache._caller_cache_key() == ""


class TestRecoveryTools:
    """
    The Recovery Service tools driven end to end through a FastMCP client, so each
    assertion covers the JSON a real client receives rather than the tool's return
    value alone.
    """

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_list_protected_databases(self, mock_get_client):
        """
        Listing protected databases returns the mapped summaries, with metrics read
        from the summary itself when the per-database GET adds nothing.
        """
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
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_get_protected_database(self, mock_get_client):
        """
        get_protected_database returns the mapped protected database, including its
        health and nested metrics.
        """
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
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_list_protection_policies(self, mock_get_client):
        """Listing protection policies returns the mapped policy summaries."""
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
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_get_protection_policy(self, mock_get_client):
        """get_protection_policy returns the mapped policy."""
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
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_list_recovery_service_subnets(self, mock_get_client):
        """Listing Recovery Service subnets returns the mapped subnet summaries."""
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
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_get_recovery_service_subnet(self, mock_get_client):
        """get_recovery_service_subnet returns the mapped subnet."""
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
    @patch("oracle.oci_recovery_mcp_server.auth.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_summarize_protected_database_health(
        self, mock_get_client, mock_get_tenancy
    ):
        """
        The health summary reads each protected database's health from its own GET and
        counts them into the aggregated buckets.
        """
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

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.auth.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_summarize_protected_database_redo_status(
        self, mock_get_client, mock_get_tenancy
    ):
        """
        The redo summary counts each protected database as enabled or disabled from its
        redo-shipped flag.
        """
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

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.auth.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_summarize_backup_space_used(self, mock_get_client, mock_get_tenancy):
        """
        The space-used summary sums each protected database's backup space, falling
        back to the metrics carried on the list summary.
        """
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

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.auth.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.auth._load_oci_config_for_server")
    @patch("oracle.oci_recovery_mcp_server.clients.get_limits_client")
    async def test_check_recovery_service_limits(
        self, mock_get_limits_client, mock_load_config, mock_get_tenancy
    ):
        """
        The limits tool reports both Recovery Service limits, always scoped to the
        tenancy OCID from config rather than to any compartment the caller passes.
        """
        mock_get_tenancy.return_value = "ocid1.tenancy.oc1..tenancy"
        mock_load_config.return_value = {
            "region": "us-ashburn-1",
            "tenancy": "ocid1.tenancy.oc1..tenancy",
        }
        mock_client = MagicMock()
        mock_get_limits_client.return_value = mock_client

        avail_storage = create_autospec(oci.response.Response)
        avail_storage.data = {
            "scope_type": "AD",
            "available": 1000,
            "used": 150,
            "fractional_availability": 0.86,
            "fractional_usage": 0.14,
            "effective_quota_value": 1150,
            "policy_name": "default",
        }
        avail_count = create_autospec(oci.response.Response)
        avail_count.data = {
            "scope_type": "AD",
            "available": 20,
            "used": 7,
            "fractional_availability": 0.74,
            "fractional_usage": 0.26,
            "effective_quota_value": 27,
            "policy_name": "default",
        }
        mock_client.get_resource_availability.side_effect = [avail_storage, avail_count]

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "check_recovery_service_limits",
                {},
            )
            result = call_tool_result.structured_content

        # compartmentId is always the tenancy OCID from config, not the input
        assert result["compartmentId"] == "ocid1.tenancy.oc1..tenancy"
        assert result["limits"]["protectedDatabaseBackupStorageGb"]["available"] == 1000
        assert result["limits"]["protectedDatabaseCount"]["used"] == 7

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.regions._iam_subscribed_regions_with_status")
    @patch("oracle.oci_recovery_mcp_server.auth.get_tenancy")
    async def test_fetch_regions_subscribed(self, mock_get_tenancy, mock_regions):
        """The regions tool reports the tenancy's subscribed regions and their count."""
        mock_get_tenancy.return_value = "ocid1.tenancy.oc1..test"
        mock_regions.return_value = [
            {"region": "us-ashburn-1", "status": "READY"},
            {"region": "us-phoenix-1", "status": "READY"},
        ]

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool("fetch_regions_subscribed", {})
            result = call_tool_result.structured_content

            assert result["tenancyId"] == "ocid1.tenancy.oc1..test"
            assert result["total"] == 2
            assert result["regions"][0]["region"] == "us-ashburn-1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.clients.get_monitoring_client")
    async def test_get_recovery_service_metrics(self, mock_get_monitoring_client):
        """
        The metrics tool returns one series per dimension set, each carrying its
        aggregated datapoints as {timestamp, value} pairs.
        """
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
                    "protected_database_id": "ocid1.protecteddatabase.oc1.iad.pd1",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["dimensions"]["resourceId"] == "pd1"
            assert len(result[0]["datapoints"]) == 2
            assert result[0]["datapoints"][0]["value"] == 1.0

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.clients.get_monitoring_client")
    async def test_get_recovery_service_metrics_no_pd_filter(self, mock_get_monitoring_client):
        """
        With no protected_database_id, the assembled query carries no resourceId filter
        clause at all.
        """
        mock_client = MagicMock()
        mock_get_monitoring_client.return_value = mock_client

        series = SimpleNamespace(
            dimensions={"resourceId": "pd1"}, aggregated_datapoints=[]
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
                    "end_time": "2024-01-01T01:00:00Z",
                },
            )
            result = call_tool_result.structured_content["result"]

        assert isinstance(result, list)
        assert len(result) == 1
        # No protected_database_id filter — query must NOT include a resourceId filter clause
        call_args = mock_client.summarize_metrics_data.call_args
        query = call_args.kwargs["summarize_metrics_data_details"].query
        assert "resourceId" not in query

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_list_protected_databases_pagination(self, mock_get_client):
        """
        Listing follows the paging token until the service reports no next page,
        returning the union of every page.
        """
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        page1 = create_autospec(oci.response.Response)
        page1.data = [oci.recovery.models.ProtectedDatabaseSummary(id="pd1")]
        page1.has_next_page = True
        page1.next_page = "token2"

        page2 = create_autospec(oci.response.Response)
        page2.data = [oci.recovery.models.ProtectedDatabaseSummary(id="pd2")]
        page2.has_next_page = False
        page2.next_page = None

        mock_client.list_protected_databases.side_effect = [page1, page2]
        mock_client.get_protected_database.return_value = create_autospec(oci.response.Response)
        mock_client.get_protected_database.return_value.data = (
            oci.recovery.models.ProtectedDatabase(id="pd1")
        )

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_protected_databases",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content["result"]

        assert len(result) == 2
        ids = {r["id"] for r in result}
        assert ids == {"pd1", "pd2"}
        assert mock_client.list_protected_databases.call_count == 2

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.compartments._compartment_ids_for_tool")
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_list_protected_databases_dedup_child_compartments(
        self, mock_get_client, mock_comp_ids
    ):
        """
        A protected database visible from two compartments of a scanned subtree is
        returned once.
        """
        mock_comp_ids.return_value = ["comp1", "comp2"]
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Both compartments return the same PD OCID -> dedup should yield 1 result
        resp = create_autospec(oci.response.Response)
        resp.data = [oci.recovery.models.ProtectedDatabaseSummary(id="pd1")]
        resp.has_next_page = False
        resp.next_page = None
        mock_client.list_protected_databases.return_value = resp

        get_resp = create_autospec(oci.response.Response)
        get_resp.data = oci.recovery.models.ProtectedDatabase(id="pd1")
        mock_client.get_protected_database.return_value = get_resp

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_protected_databases",
                {
                    "compartment_id": "ocid1.compartment.oc1..test",
                    "fetch_for_child_compartment": True,
                },
            )
            result = call_tool_result.structured_content["result"]

        assert len(result) == 1
        assert result[0]["id"] == "pd1"

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.auth.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_summarize_health_alert_and_unknown_states(
        self, mock_get_client, mock_get_tenancy
    ):
        """
        A protected database with no health value counts as unknown rather than being
        dropped from the total.
        """
        mock_get_tenancy.return_value = "ocid1.compartment.oc1..test"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list = create_autospec(oci.response.Response)
        mock_list.data = [
            oci.recovery.models.ProtectedDatabaseSummary(id="pd1"),
            oci.recovery.models.ProtectedDatabaseSummary(id="pd2"),
        ]
        mock_list.has_next_page = False
        mock_list.next_page = None
        mock_client.list_protected_databases.return_value = mock_list

        r1 = create_autospec(oci.response.Response)
        r1.data = oci.recovery.models.ProtectedDatabase(id="pd1", health="ALERT")
        r2 = create_autospec(oci.response.Response)
        # health=None triggers unknown counter
        r2.data = oci.recovery.models.ProtectedDatabase(id="pd2", health=None)
        mock_client.get_protected_database.side_effect = [r1, r2]

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "summarize_protected_database_health",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content

        agg = result["aggregated"]
        assert agg["alert"] == 1
        assert agg["unknown"] == 1
        assert agg["protected"] == 0
        assert agg["warning"] == 0
        assert agg["total"] == 2

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.auth.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_summarize_redo_none_not_counted(
        self, mock_get_client, mock_get_tenancy
    ):
        """
        A protected database whose redo-shipped flag is None counts as neither enabled
        nor disabled.
        """
        mock_get_tenancy.return_value = "ocid1.compartment.oc1..test"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list = create_autospec(oci.response.Response)
        mock_list.data = [oci.recovery.models.ProtectedDatabaseSummary(id="pd1")]
        mock_list.has_next_page = False
        mock_list.next_page = None
        mock_client.list_protected_databases.return_value = mock_list

        pd = oci.recovery.models.ProtectedDatabase(id="pd1")
        pd.is_redo_logs_shipped = None  # unknown -> must not count
        r = create_autospec(oci.response.Response)
        r.data = pd
        mock_client.get_protected_database.return_value = r

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "summarize_protected_database_redo_status",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content

        agg = result["aggregated"]
        assert agg["enabled"] == 0
        assert agg["disabled"] == 0
        assert agg["unknown"] == 1
        # In scope but unreadable: it stays in total so the fleet size is right.
        assert agg["total"] == 1

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.auth.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_summarize_redo_get_failure_is_non_fatal(
        self, mock_get_client, mock_get_tenancy
    ):
        """A single GET failure must not abort the whole tool."""
        mock_get_tenancy.return_value = "ocid1.compartment.oc1..test"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list = create_autospec(oci.response.Response)
        mock_list.data = [
            oci.recovery.models.ProtectedDatabaseSummary(id="pd1"),
            oci.recovery.models.ProtectedDatabaseSummary(id="pd2"),
        ]
        mock_list.has_next_page = False
        mock_list.next_page = None
        mock_client.list_protected_databases.return_value = mock_list

        pd2_resp = create_autospec(oci.response.Response)
        pd2 = oci.recovery.models.ProtectedDatabase(id="pd2")
        pd2.is_redo_logs_shipped = True
        pd2_resp.data = pd2

        # pd1 GET raises; pd2 succeeds
        mock_client.get_protected_database.side_effect = [
            Exception("transient error"),
            pd2_resp,
        ]

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "summarize_protected_database_redo_status",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content

        agg = result["aggregated"]
        assert agg["enabled"] == 1
        assert agg["disabled"] == 0

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.auth.get_tenancy")
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_summarize_backup_space_skips_deleted_lifecycle(
        self, mock_get_client, mock_get_tenancy
    ):
        """
        A deleted protected database is left out of the scan entirely -- not counted,
        and never fetched.
        """
        mock_get_tenancy.return_value = "ocid1.compartment.oc1..test"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        active_pd = oci.recovery.models.ProtectedDatabaseSummary(
            id="pd1", lifecycle_state="ACTIVE"
        )
        deleted_pd = oci.recovery.models.ProtectedDatabaseSummary(
            id="pd2", lifecycle_state="DELETED"
        )
        mock_list = create_autospec(oci.response.Response)
        mock_list.data = [active_pd, deleted_pd]
        mock_list.has_next_page = False
        mock_list.next_page = None
        mock_client.list_protected_databases.return_value = mock_list

        pd1 = oci.recovery.models.ProtectedDatabase(id="pd1")
        pd1.metrics = {"backup_space_used_in_gbs": 20.0}
        r1 = create_autospec(oci.response.Response)
        r1.data = pd1
        mock_client.get_protected_database.return_value = r1

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "summarize_backup_space_used",
                {"compartment_id": "ocid1.compartment.oc1..test"},
            )
            result = call_tool_result.structured_content

        agg = result["aggregated"]
        total = agg.get("total_databases_scanned") or agg.get("totalDatabasesScanned")
        sum_gb = agg.get("sum_backup_space_used_in_gbs") or agg.get("sumBackupSpaceUsedInGBs")
        assert total == 1  # DELETED is excluded
        assert abs(sum_gb - 20.0) < 1e-9
        # GET must only be called for ACTIVE PD, not for DELETED
        assert mock_client.get_protected_database.call_count == 1

    @pytest.mark.asyncio
    @patch("oracle.oci_recovery_mcp_server.clients.get_recovery_client")
    async def test_list_protection_policies_with_lifecycle_filter(self, mock_get_client):
        """
        The lifecycle filter is forwarded to the SDK call rather than applied after the
        fact.
        """
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list = create_autospec(oci.response.Response)
        mock_list.data = [
            oci.recovery.models.ProtectionPolicySummary(
                id="pp1", display_name="Policy 1", lifecycle_state="ACTIVE"
            )
        ]
        mock_list.has_next_page = False
        mock_list.next_page = None
        mock_client.list_protection_policies.return_value = mock_list

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_protection_policies",
                {
                    "compartment_id": "ocid1.compartment.oc1..test",
                    "lifecycle_state": "ACTIVE",
                },
            )
            result = call_tool_result.structured_content["result"]

        assert len(result) == 1
        call_kwargs = mock_client.list_protection_policies.call_args.kwargs
        assert call_kwargs.get("lifecycle_state") == "ACTIVE"


class TestServer:
    """The entrypoint's transport selection and the validation guarding it."""

    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port_serves_http_behind_idcs_auth(
        self, mock_getenv, mock_mcp_run
    ):
        """
        Host plus port selects the HTTP listener, and that listener never starts
        without an IAM auth provider attached: local profile credentials must not back
        a network listener.
        """
        mock_env = {
            "ORACLE_MCP_HOST": "127.0.0.1",
            "ORACLE_MCP_PORT": "8080",
        }
        # Return configured values for known keys, and default for others
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)

        import oracle.oci_recovery_mcp_server.server as server

        http_auth = SimpleNamespace(provider=object())
        with patch.object(auth, "_build_http_auth", return_value=http_auth):
            with patch.object(server.mcp, "auth", None, create=True):
                server.main()
                assert server.mcp.auth is http_auth.provider
        assert auth._http_auth is http_auth
        mock_mcp_run.assert_called_once_with(
            transport="http", host="127.0.0.1", port=8080
        )
        auth._http_auth = None

    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_refuses_to_serve_http_without_an_auth_provider(
        self, mock_getenv, mock_mcp_run
    ):
        """
        The listener fails closed. If the IDCS policy cannot be built -- missing or
        malformed configuration -- it never starts, rather than leaving the operator's
        own OCI credentials backing an unauthenticated network listener.
        """
        mock_env = {
            "ORACLE_MCP_HOST": "0.0.0.0",
            "ORACLE_MCP_PORT": "8080",
        }
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)

        import oracle.oci_recovery_mcp_server.server as server

        with patch.object(
            auth,
            "_build_http_auth",
            side_effect=ValueError("HTTP IDCS authentication requires: IDCS_DOMAIN"),
        ):
            with patch.object(server.mcp, "auth", None, create=True):
                with pytest.raises(ValueError, match="IDCS_DOMAIN"):
                    server.main()
                assert server.mcp.auth is None
        mock_mcp_run.assert_not_called()
        assert auth._http_auth is None

    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        """With neither host nor port set, the server runs over stdio."""
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
        """Host without port is rejected rather than half-configuring a listener."""
        mock_env = {"ORACLE_MCP_HOST": "127.0.0.1"}
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)

        import oracle.oci_recovery_mcp_server.server as server

        with pytest.raises(ValueError, match="must either both be set or both be unset"):
            server.main()
        mock_mcp_run.assert_not_called()

    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        """Port without host is rejected rather than half-configuring a listener."""
        mock_env = {"ORACLE_MCP_PORT": "8080"}
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)

        import oracle.oci_recovery_mcp_server.server as server

        with pytest.raises(ValueError, match="must either both be set or both be unset"):
            server.main()
        mock_mcp_run.assert_not_called()

    @pytest.mark.parametrize("port", ["not-a-port", "0", "65536"])
    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_rejects_invalid_http_port(self, mock_getenv, mock_mcp_run, port):
        """
        A port that is not an integer from 1 to 65535 is rejected before the listener
        starts.
        """
        mock_env = {"ORACLE_MCP_HOST": "127.0.0.1", "ORACLE_MCP_PORT": port}
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)

        import oracle.oci_recovery_mcp_server.server as server

        with pytest.raises(ValueError, match="integer from 1 to 65535"):
            server.main()
        mock_mcp_run.assert_not_called()

    @patch("oracle.oci_recovery_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_http_honors_host_and_port(self, mock_getenv, mock_mcp_run):
        """The configured host and port reach the HTTP transport as given."""
        mock_env = {
            "ORACLE_MCP_HOST": "0.0.0.0",
            "ORACLE_MCP_PORT": "9001",
        }
        mock_getenv.side_effect = lambda k, d=None: mock_env.get(k, d)

        import oracle.oci_recovery_mcp_server.server as server

        http_auth = SimpleNamespace(provider=object())
        with patch.object(auth, "_build_http_auth", return_value=http_auth):
            with patch.object(server.mcp, "auth", None, create=True):
                server.main()
        mock_mcp_run.assert_called_once_with(transport="http", host="0.0.0.0", port=9001)
        auth._http_auth = None


class TestToolContract:
    """The tool surface a client sees before it calls anything."""

    @pytest.mark.asyncio
    async def test_every_tool_declares_itself_read_only(self):
        """
        Every tool declares itself read-only, non-destructive and idempotent, and only
        the guidance tools declare that they never reach the network.

        The server's central claim -- that it never creates, updates or deletes an OCI
        resource -- is only in the README otherwise, where a host cannot act on it.
        """
        async with Client(mcp) as client:
            tools = await client.list_tools()

        assert len(tools) == 25
        for tool in tools:
            annotations = tool.annotations
            assert annotations is not None, f"{tool.name} declares no annotations"
            assert annotations.readOnlyHint is True, tool.name
            assert annotations.destructiveHint is False, tool.name
            assert annotations.idempotentHint is True, tool.name

        # The guidance tools return static text and never reach the network.
        local = {
            "oci_recovery_service_dashboard_prompt",
            "onboard_database_to_recovery_service",
            "diagnose_recovery_service_issue",
        }
        for tool in tools:
            expected = tool.name not in local
            assert tool.annotations.openWorldHint is expected, tool.name

    @pytest.mark.asyncio
    async def test_summary_tools_advertise_the_shape_they_return(self, monkeypatch):
        """
        The two summary tools return exactly the keys their outputSchema declares.

        Both once declared a counts model but returned a wrapper around it, so any
        client trusting outputSchema was given the wrong contract.
        """
        recovery_client = MagicMock()
        monkeypatch.setattr(
            clients, "get_recovery_client", lambda region=None, request_id=None: recovery_client
        )
        monkeypatch.setattr(
            compartments, "_resolve_compartment_id", lambda compartment_id, **_kwargs: compartment_id
        )
        monkeypatch.setattr(compartments, "_compartment_ids_for_tool", lambda cid, **_kwargs: [cid])
        recovery_client.list_protected_databases.return_value = SimpleNamespace(
            data=SimpleNamespace(items=[]), has_next_page=False, next_page=None
        )

        async with Client(mcp) as client:
            tools = {tool.name: tool for tool in await client.list_tools()}
            for name in (
                "summarize_protected_database_health",
                "summarize_protected_database_redo_status",
            ):
                declared = set(tools[name].outputSchema["properties"])
                result = await client.call_tool(
                    name, {"compartment_id": "ocid1.compartment.oc1..c"}
                )
                assert set(result.structured_content) == declared, name
