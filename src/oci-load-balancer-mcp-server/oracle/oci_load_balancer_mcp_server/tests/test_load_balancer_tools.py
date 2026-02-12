"""
Unit tests for the OCI Load Balancer MCP server tools (server.py).

The tests mock the underlying OCI client returned by ``get_load_balancer_client`` and
verify that each tool forwards the correct parameters and returns the mapped
Pydantic models.  All tests are asynchronous and marked with ``@pytest.mark.asyncio``.
"""

import types
from unittest.mock import MagicMock, patch

import pytest

# Import the server module where the tools are defined
from oracle.oci_load_balancer_mcp_server import server


class MockResponse:
    """Simple mock of an OCI response object."""

    def __init__(
        self, data=None, headers=None, status=200, request_id=None, next_page=None
    ):
        self.data = data
        self.headers = headers or {}
        self.status = status
        self.request_id = request_id
        self.next_page = next_page


@pytest.fixture(autouse=True)
def mock_client(monkeypatch):
    """Patch ``get_load_balancer_client`` to return a MagicMock client and stub OCI model classes."""
    # Stub OCI SDK model constructors to accept any kwargs (avoid strict validations during tests)
    import oci

    class _Dummy:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    m = oci.load_balancer.models
    for name in [
        "ShapeDetails",
        "CreateLoadBalancerDetails",
        "UpdateLoadBalancerDetails",
        "UpdateLoadBalancerShapeDetails",
        "SSLConfigurationDetails",
        "ConnectionConfiguration",
        "CreateListenerDetails",
        "UpdateListenerDetails",
        "HealthCheckerDetails",
        "SessionPersistenceConfigurationDetails",
        "LBCookieSessionPersistenceConfigurationDetails",
        "BackendDetails",
        "CreateBackendSetDetails",
        "UpdateBackendSetDetails",
        "CreateBackendDetails",
        "UpdateBackendDetails",
        "CreateCertificateDetails",
        "CreateSSLCipherSuiteDetails",
        "UpdateSSLCipherSuiteDetails",
        "CreateHostnameDetails",
        "UpdateHostnameDetails",
        "CreateRuleSetDetails",
        "UpdateRuleSetDetails",
        "CreateRoutingPolicyDetails",
        "UpdateRoutingPolicyDetails",
    ]:
        monkeypatch.setattr(m, name, _Dummy, raising=True)

    with patch.object(server, "get_load_balancer_client") as get_client:
        mock = MagicMock()
        get_client.return_value = mock
        yield mock


# ----------------------------------------------------------------------
# Load Balancer tools
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_load_balancers(mock_client):
    mock_lb = types.SimpleNamespace(id="lb_ocid")
    mock_client.list_load_balancers.return_value = MockResponse(data=[mock_lb])

    result = server.list_load_balancers.fn(
        compartment_id="compartment_ocid",
        limit=None,
        lifecycle_state=None,
        display_name=None,
        sort_by=None,
        sort_order=None,
    )

    mock_client.list_load_balancers.assert_called_once()
    assert isinstance(result, list)
    assert result[0].id == "lb_ocid"


@pytest.mark.asyncio
async def test_list_load_balancers_pagination(mock_client):
    # First page with next_page, second page without
    page1 = MockResponse(data=[types.SimpleNamespace(id="lb1")], next_page="token")
    page2 = MockResponse(data=[types.SimpleNamespace(id="lb2")], next_page=None)
    mock_client.list_load_balancers.side_effect = [page1, page2]

    result = server.list_load_balancers.fn(
        compartment_id="compartment_ocid",
        limit=None,
    )
    assert [lb.id for lb in result] == ["lb1", "lb2"]


@pytest.mark.asyncio
async def test_list_load_balancers_limit_stops_early(mock_client):
    # next_page provided but limit should stop pagination after first page slice
    page1 = MockResponse(
        data=[types.SimpleNamespace(id="lb1"), types.SimpleNamespace(id="lb2")],
        next_page="token",
    )
    mock_client.list_load_balancers.return_value = page1
    out = server.list_load_balancers.fn(compartment_id="c", limit=1)
    assert [lb.id for lb in out] == ["lb1"]
    mock_client.list_load_balancers.assert_called_once()


@pytest.mark.asyncio
async def test_get_load_balancer_listener_not_found(mock_client):
    mock_client.get_load_balancer.return_value = MockResponse(
        data=types.SimpleNamespace(listeners={})
    )
    with pytest.raises(ValueError):
        server.get_load_balancer_listener.fn(
            load_balancer_id="lb_ocid", listener_name="missing"
        )


@pytest.mark.asyncio
async def test_create_listener_with_ssl_and_conn_config(mock_client):
    mock_client.create_listener.return_value = MockResponse(data={})
    result = server.create_load_balancer_listener.fn(
        load_balancer_id="lb_ocid",
        name="lsn",
        default_backend_set_name="bs1",
        port=443,
        protocol="HTTP",
        ssl_protocols=["TLSv1.2"],
        ssl_cipher_suite_name="suite",
        ssl_server_order_preference="ENABLED",
        ssl_certificate_name="cert",
        ssl_has_session_resumption=True,
        ssl_verify_peer_certificate=False,
        ssl_verify_depth=3,
        idle_timeout=60,
        backend_tcp_proxy_protocol_version=1,
        backend_tcp_proxy_protocol_options=["PP2_TYPE_AUTHORITY"],
    )
    assert result is not None


@pytest.mark.asyncio
async def test_update_load_balancer_shape_and_nsgs(mock_client):
    mock_client.update_load_balancer_shape.return_value = MockResponse(data={})
    mock_client.update_network_security_groups.return_value = MockResponse(data={})

    r1 = server.update_load_balancer_shape.fn(
        load_balancer_id="lb_ocid",
        shape_name="Flexible",
        minimum_bandwidth_in_mbps=10,
        maximum_bandwidth_in_mbps=100,
    )
    r2 = server.update_load_balancer_network_security_groups.fn(
        load_balancer_id="lb_ocid", network_security_group_ids=["nsg1"]
    )
    assert r1 is not None and r2 is not None


@pytest.mark.asyncio
async def test_update_load_balancer_shape_name_only(mock_client):
    mock_client.update_load_balancer_shape.return_value = MockResponse(data={})
    out = server.update_load_balancer_shape.fn(
        load_balancer_id="lb", shape_name="100Mbps"
    )
    assert out is not None


@pytest.mark.asyncio
async def test_update_load_balancer_shape_bandwidth_only(mock_client):
    mock_client.update_load_balancer_shape.return_value = MockResponse(data={})
    out = server.update_load_balancer_shape.fn(
        load_balancer_id="lb",
        minimum_bandwidth_in_mbps=10,
        maximum_bandwidth_in_mbps=20,
    )
    assert out is not None


@pytest.mark.asyncio
async def test_update_load_balancer_network_security_groups_none(mock_client):
    mock_client.update_network_security_groups.return_value = MockResponse(data={})
    out = server.update_load_balancer_network_security_groups.fn(
        load_balancer_id="lb", network_security_group_ids=None
    )
    assert out is not None


@pytest.mark.asyncio
async def test_limits_on_listing_helpers(mock_client):
    # listeners limit
    mock_listener = types.SimpleNamespace(name="listener1")
    mock_client.get_load_balancer.return_value = MockResponse(
        data=types.SimpleNamespace(
            listeners={"listener1": mock_listener, "l2": mock_listener}
        )
    )
    ls = server.list_load_balancer_listeners.fn(load_balancer_id="lb", limit=1)
    assert len(ls) == 1

    # backend sets limit
    mock_bs = types.SimpleNamespace(name="bs1")
    mock_client.list_backend_sets.return_value = MockResponse(data=[mock_bs, mock_bs])
    bss = server.list_load_balancer_backend_sets.fn(load_balancer_id="lb", limit=1)
    assert len(bss) == 1

    # backends limit
    mock_backend = types.SimpleNamespace(name="b1")
    mock_client.list_backends.return_value = MockResponse(
        data=[mock_backend, mock_backend]
    )
    bs = server.list_backends.fn(load_balancer_id="lb", backend_set_name="bs", limit=1)
    assert len(bs) == 1

    # certificates limit
    mock_cert = types.SimpleNamespace(certificate_name="c1")
    mock_client.list_certificates.return_value = MockResponse(
        data=[mock_cert, mock_cert]
    )
    certs = server.list_load_balancer_certificates.fn(load_balancer_id="lb", limit=1)
    assert len(certs) == 1

    # cipher suites limit
    mock_suite = types.SimpleNamespace(name="s")
    mock_client.list_ssl_cipher_suites.return_value = MockResponse(
        data=[mock_suite, mock_suite]
    )
    suites = server.list_ssl_cipher_suites.fn(load_balancer_id="lb", limit=1)
    assert len(suites) == 1

    # hostnames limit
    mock_host = types.SimpleNamespace(name="h")
    mock_client.list_hostnames.return_value = MockResponse(data=[mock_host, mock_host])
    hosts = server.list_hostnames.fn(load_balancer_id="lb", limit=1)
    assert len(hosts) == 1

    # rule sets limit
    mock_rs = types.SimpleNamespace(name="rs")
    mock_client.list_rule_sets.return_value = MockResponse(data=[mock_rs, mock_rs])
    rss = server.list_rule_sets.fn(load_balancer_id="lb", limit=1)
    assert len(rss) == 1


@pytest.mark.asyncio
async def test_pagination_helpers(mock_client):
    # routing policies pagination
    rp1 = MockResponse(data=[types.SimpleNamespace(name="p1")], next_page="n1")
    rp2 = MockResponse(data=[types.SimpleNamespace(name="p2")], next_page=None)
    mock_client.list_routing_policies.side_effect = [rp1, rp2]
    rps = server.list_routing_policies.fn(load_balancer_id="lb", limit=None)
    assert [p.name for p in rps] == ["p1", "p2"]

    # health summaries pagination
    hs1 = MockResponse(
        data=[types.SimpleNamespace(load_balancer_id="a")], next_page="n1"
    )
    hs2 = MockResponse(
        data=[types.SimpleNamespace(load_balancer_id="b")], next_page=None
    )
    mock_client.list_load_balancer_healths.side_effect = [hs1, hs2]
    healths = server.list_load_balancer_healths.fn(compartment_id="c", limit=None)
    assert [h.load_balancer_id for h in healths] == ["a", "b"]

    # work requests pagination
    wr1 = MockResponse(data=[types.SimpleNamespace(id="w1")], next_page="n1")
    wr2 = MockResponse(data=[types.SimpleNamespace(id="w2")], next_page=None)
    mock_client.list_work_requests.side_effect = [wr1, wr2]
    wrs = server.list_load_balancer_work_requests.fn(load_balancer_id="lb", limit=None)
    assert [w.id for w in wrs] == ["w1", "w2"]


@pytest.mark.asyncio
async def test_limit_helpers_stop_after_first_page(mock_client):
    # routing policies
    mock_client.list_routing_policies.return_value = MockResponse(
        data=[types.SimpleNamespace(name="p1"), types.SimpleNamespace(name="p2")],
        next_page="n1",
    )
    rps = server.list_routing_policies.fn(load_balancer_id="lb", limit=1)
    assert [p.name for p in rps] == ["p1"]
    mock_client.list_routing_policies.assert_called_once()

    # health summaries
    mock_client.list_load_balancer_healths.return_value = MockResponse(
        data=[
            types.SimpleNamespace(load_balancer_id="a"),
            types.SimpleNamespace(load_balancer_id="b"),
        ],
        next_page="n1",
    )
    hs = server.list_load_balancer_healths.fn(compartment_id="c", limit=1)
    assert [h.load_balancer_id for h in hs] == ["a"]
    mock_client.list_load_balancer_healths.assert_called_once()

    # work requests
    mock_client.list_work_requests.return_value = MockResponse(
        data=[types.SimpleNamespace(id="w1"), types.SimpleNamespace(id="w2")],
        next_page="n1",
    )
    wrs = server.list_load_balancer_work_requests.fn(load_balancer_id="lb", limit=1)
    assert [w.id for w in wrs] == ["w1"]
    mock_client.list_work_requests.assert_called_once()


@pytest.mark.asyncio
async def test_get_load_balancer(mock_client):
    mock_lb = types.SimpleNamespace(id="lb_ocid")
    mock_client.get_load_balancer.return_value = MockResponse(data=mock_lb)

    result = server.get_load_balancer.fn(load_balancer_id="lb_ocid")
    mock_client.get_load_balancer.assert_called_once_with("lb_ocid")
    assert result.id == "lb_ocid"


@pytest.mark.asyncio
async def test_error_paths_raise_and_log(mock_client):
    # Simulate client raising to drive except blocks
    mock_client.get_backend.side_effect = RuntimeError("boom")
    with pytest.raises(RuntimeError):
        server.get_backend.fn(
            load_balancer_id="lb", backend_set_name="bs", backend_name="ip:1"
        )

    mock_client.create_ssl_cipher_suite.side_effect = ValueError("bad")
    with pytest.raises(ValueError):
        server.create_ssl_cipher_suite.fn(
            load_balancer_id="lb", name="s", ciphers=["c"]
        )


@pytest.mark.asyncio
async def test_create_load_balancer(mock_client):
    mock_resp = MagicMock()
    mock_client.create_load_balancer.return_value = MockResponse(data=mock_resp)

    result = server.create_load_balancer.fn(
        compartment_id="compartment_ocid",
        display_name="test-lb",
        shape_name="100Mbps",
        subnet_ids=["subnet_ocid"],
        is_private=False,
        ip_mode=None,
        is_delete_protection_enabled=False,
        is_request_id_enabled=False,
        request_id_header=None,
        network_security_group_ids=None,
        minimum_bandwidth_in_mbps=None,
        maximum_bandwidth_in_mbps=None,
    )
    mock_client.create_load_balancer.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_update_load_balancer(mock_client):
    mock_resp = MagicMock()
    mock_client.update_load_balancer.return_value = MockResponse(data=mock_resp)

    result = server.update_load_balancer.fn(
        load_balancer_id="lb_ocid",
        display_name="new-name",
        is_delete_protection_enabled=True,
        is_request_id_enabled=True,
        request_id_header="X-Request-Id",
        freeform_tags={"env": "test"},
        defined_tags=None,
        defined_tags_extended=None,
    )
    mock_client.update_load_balancer.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_update_load_balancer_minimal(mock_client):
    mock_client.update_load_balancer.return_value = MockResponse(data={})
    res = server.update_load_balancer.fn(load_balancer_id="lb")
    assert res is not None


@pytest.mark.asyncio
async def test_delete_load_balancer(mock_client):
    mock_resp = MagicMock()
    mock_client.delete_load_balancer.return_value = MockResponse(data=mock_resp)

    result = server.delete_load_balancer.fn(load_balancer_id="lb_ocid")
    mock_client.delete_load_balancer.assert_called_once_with("lb_ocid")
    assert result is not None


# ----------------------------------------------------------------------
# Listener tools
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_load_balancer_listeners(mock_client):
    mock_listener = types.SimpleNamespace(name="listener1")
    mock_client.get_load_balancer.return_value = MockResponse(
        data=types.SimpleNamespace(listeners={"listener1": mock_listener})
    )

    result = server.list_load_balancer_listeners.fn(
        load_balancer_id="lb_ocid", limit=None
    )
    mock_client.get_load_balancer.assert_called_once()
    assert isinstance(result, list)
    assert result[0].name == "listener1"


@pytest.mark.asyncio
async def test_create_load_balancer_listener(mock_client):
    mock_resp = MagicMock()
    mock_client.create_listener.return_value = MockResponse(data=mock_resp)

    result = server.create_load_balancer_listener.fn(
        load_balancer_id="lb_ocid",
        name="listener1",
        default_backend_set_name="backendset1",
        port=80,
        protocol="HTTP",
    )
    mock_client.create_listener.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_get_load_balancer_listener(mock_client):
    mock_listener = types.SimpleNamespace(name="listener1")
    mock_client.get_load_balancer.return_value = MockResponse(
        data=types.SimpleNamespace(listeners={"listener1": mock_listener})
    )

    result = server.get_load_balancer_listener.fn(
        load_balancer_id="lb_ocid", listener_name="listener1"
    )
    mock_client.get_load_balancer.assert_called_once()
    assert result.name == "listener1"


@pytest.mark.asyncio
async def test_update_load_balancer_listener(mock_client):
    mock_resp = MagicMock()
    mock_client.update_listener.return_value = MockResponse(data=mock_resp)

    result = server.update_load_balancer_listener.fn(
        load_balancer_id="lb_ocid",
        listener_name="listener1",
        default_backend_set_name="backendset2",
        port=443,
        protocol="HTTPS",
    )
    mock_client.update_listener.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_update_load_balancer_listener_no_optional(mock_client):
    mock_client.update_listener.return_value = MockResponse(data={})
    res = server.update_load_balancer_listener.fn(
        load_balancer_id="lb_ocid", listener_name="l1"
    )
    assert res is not None


@pytest.mark.asyncio
async def test_delete_load_balancer_listener(mock_client):
    mock_resp = MagicMock()
    mock_client.delete_listener.return_value = MockResponse(data=mock_resp)

    result = server.delete_load_balancer_listener.fn(
        load_balancer_id="lb_ocid", listener_name="listener1"
    )
    mock_client.delete_listener.assert_called_once_with("lb_ocid", "listener1")
    assert result is not None


# ----------------------------------------------------------------------
# Backend set tools
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_load_balancer_backend_sets(mock_client):
    mock_bs = types.SimpleNamespace(name="backendset1")
    mock_client.list_backend_sets.return_value = MockResponse(data=[mock_bs])

    result = server.list_load_balancer_backend_sets.fn(
        load_balancer_id="lb_ocid", limit=None
    )
    mock_client.list_backend_sets.assert_called_once_with("lb_ocid")
    assert isinstance(result, list)
    assert result[0].name == "backendset1"


@pytest.mark.asyncio
async def test_create_load_balancer_backend_set(mock_client):
    mock_resp = MagicMock()
    mock_client.create_backend_set.return_value = MockResponse(data=mock_resp)

    result = server.create_load_balancer_backend_set.fn(
        load_balancer_id="lb_ocid",
        name="backendset1",
        policy="ROUND_ROBIN",
        health_checker_protocol="HTTP",
        backends=[],
    )
    mock_client.create_backend_set.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_create_backend_set_without_backends(mock_client):
    mock_client.create_backend_set.return_value = MockResponse(data={})
    out = server.create_load_balancer_backend_set.fn(
        load_balancer_id="lb",
        name="bs",
        policy="ROUND_ROBIN",
        health_checker_protocol="HTTP",
        backends=None,
    )
    assert out is not None


@pytest.mark.asyncio
async def test_update_load_balancer_backend_set(mock_client):
    mock_resp = MagicMock()
    mock_client.update_backend_set.return_value = MockResponse(data=mock_resp)

    result = server.update_load_balancer_backend_set.fn(
        load_balancer_id="lb_ocid",
        name="backendset1",
        policy="LEAST_CONNECTIONS",
        backends=[],
    )
    mock_client.update_backend_set.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_delete_load_balancer_backend_set(mock_client):
    mock_resp = MagicMock()
    mock_client.delete_backend_set.return_value = MockResponse(data=mock_resp)

    result = server.delete_load_balancer_backend_set.fn(
        load_balancer_id="lb_ocid", name="backendset1"
    )
    mock_client.delete_backend_set.assert_called_once_with("lb_ocid", "backendset1")
    assert result is not None


# ----------------------------------------------------------------------
# Backend tools
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_backends(mock_client):
    mock_backend = types.SimpleNamespace(name="backend1")
    mock_client.list_backends.return_value = MockResponse(data=[mock_backend])

    result = server.list_backends.fn(
        load_balancer_id="lb_ocid", backend_set_name="bs1", limit=None
    )
    mock_client.list_backends.assert_called_once_with("lb_ocid", "bs1")
    assert isinstance(result, list)
    assert result[0].name == "backend1"


@pytest.mark.asyncio
async def test_create_backend(mock_client):
    mock_resp = MagicMock()
    mock_client.create_backend.return_value = MockResponse(data=mock_resp)

    result = server.create_backend.fn(
        load_balancer_id="lb_ocid",
        backend_set_name="bs1",
        ip_address="10.0.0.1",
        port=8080,
    )
    mock_client.create_backend.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_get_backend(mock_client):
    mock_backend = types.SimpleNamespace(name="backend1")
    mock_client.get_backend.return_value = MockResponse(data=mock_backend)

    result = server.get_backend.fn(
        load_balancer_id="lb_ocid",
        backend_set_name="bs1",
        backend_name="10.0.0.1:8080",
    )
    mock_client.get_backend.assert_called_once()
    assert result.name == "backend1"


@pytest.mark.asyncio
async def test_update_backend(mock_client):
    mock_resp = MagicMock()
    mock_client.update_backend.return_value = MockResponse(data=mock_resp)

    result = server.update_backend.fn(
        load_balancer_id="lb_ocid",
        backend_set_name="bs1",
        backend_name="10.0.0.1:8080",
        weight=10,
    )
    mock_client.update_backend.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_delete_backend(mock_client):
    mock_resp = MagicMock()
    mock_client.delete_backend.return_value = MockResponse(data=mock_resp)

    result = server.delete_backend.fn(
        load_balancer_id="lb_ocid",
        backend_set_name="bs1",
        backend_name="10.0.0.1:8080",
    )
    mock_client.delete_backend.assert_called_once()
    assert result is not None


# ----------------------------------------------------------------------
# Certificate tools
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_load_balancer_certificates(mock_client):
    mock_cert = types.SimpleNamespace(certificate_name="cert1")
    mock_client.list_certificates.return_value = MockResponse(data=[mock_cert])

    result = server.list_load_balancer_certificates.fn(
        load_balancer_id="lb_ocid", limit=None
    )
    mock_client.list_certificates.assert_called_once_with("lb_ocid")
    assert isinstance(result, list)
    assert result[0].certificate_name == "cert1"


@pytest.mark.asyncio
async def test_create_load_balancer_certificate(mock_client):
    mock_resp = MagicMock()
    mock_client.create_certificate.return_value = MockResponse(data=mock_resp)

    result = server.create_load_balancer_certificate.fn(
        load_balancer_id="lb_ocid",
        certificate_name="cert1",
        public_certificate="---PUBLIC---",
        private_key="---PRIVATE---",
    )
    mock_client.create_certificate.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_delete_load_balancer_certificate(mock_client):
    mock_resp = MagicMock()
    mock_client.delete_certificate.return_value = MockResponse(data=mock_resp)

    result = server.delete_load_balancer_certificate.fn(
        load_balancer_id="lb_ocid", certificate_name="cert1"
    )
    mock_client.delete_certificate.assert_called_once_with("lb_ocid", "cert1")
    assert result is not None


# ----------------------------------------------------------------------
# SSL Cipher Suite tools
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_ssl_cipher_suites(mock_client):
    mock_suite = types.SimpleNamespace(name="suite1")
    mock_client.list_ssl_cipher_suites.return_value = MockResponse(data=[mock_suite])
    out = server.list_ssl_cipher_suites.fn(load_balancer_id="lb", limit=None)
    mock_client.list_ssl_cipher_suites.assert_called_once_with("lb")
    assert [s.name for s in out] == ["suite1"]


@pytest.mark.asyncio
async def test_create_ssl_cipher_suite(mock_client):
    mock_client.create_ssl_cipher_suite.return_value = MockResponse(data={})
    res = server.create_ssl_cipher_suite.fn(
        load_balancer_id="lb", name="suite1", ciphers=["TLS_AES_128_GCM_SHA256"]
    )
    assert res is not None


@pytest.mark.asyncio
async def test_update_ssl_cipher_suite(mock_client):
    mock_resp = MagicMock()
    mock_client.update_ssl_cipher_suite.return_value = MockResponse(data=mock_resp)

    result = server.update_ssl_cipher_suite.fn(
        load_balancer_id="lb_ocid", name="suite1", ciphers=["TLS_AES_256_GCM_SHA384"]
    )
    mock_client.update_ssl_cipher_suite.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_delete_ssl_cipher_suite(mock_client):
    mock_resp = MagicMock()
    mock_client.delete_ssl_cipher_suite.return_value = MockResponse(data=mock_resp)

    result = server.delete_ssl_cipher_suite.fn(
        load_balancer_id="lb_ocid", name="suite1"
    )
    mock_client.delete_ssl_cipher_suite.assert_called_once_with("lb_ocid", "suite1")
    assert result is not None


# ----------------------------------------------------------------------
# Hostname tools
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_hostnames(mock_client):
    mock_host = types.SimpleNamespace(name="host1")
    mock_client.list_hostnames.return_value = MockResponse(data=[mock_host])

    result = server.list_hostnames.fn(load_balancer_id="lb_ocid", limit=None)
    mock_client.list_hostnames.assert_called_once_with("lb_ocid")
    assert isinstance(result, list)
    assert result[0].name == "host1"


@pytest.mark.asyncio
async def test_create_hostname(mock_client):
    mock_resp = MagicMock()
    mock_client.create_hostname.return_value = MockResponse(data=mock_resp)

    result = server.create_hostname.fn(
        load_balancer_id="lb_ocid", name="host1", hostname="app.example.com"
    )
    mock_client.create_hostname.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_get_hostname(mock_client):
    mock_host = types.SimpleNamespace(name="host1")
    mock_client.get_hostname.return_value = MockResponse(data=mock_host)

    result = server.get_hostname.fn(load_balancer_id="lb_ocid", name="host1")
    mock_client.get_hostname.assert_called_once_with("lb_ocid", "host1")
    assert result.name == "host1"


@pytest.mark.asyncio
async def test_update_hostname(mock_client):
    mock_resp = MagicMock()
    mock_client.update_hostname.return_value = MockResponse(data=mock_resp)

    result = server.update_hostname.fn(
        load_balancer_id="lb_ocid", name="host1", hostname="new.example.com"
    )
    mock_client.update_hostname.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_delete_hostname(mock_client):
    mock_resp = MagicMock()
    mock_client.delete_hostname.return_value = MockResponse(data=mock_resp)

    result = server.delete_hostname.fn(load_balancer_id="lb_ocid", name="host1")
    mock_client.delete_hostname.assert_called_once_with("lb_ocid", "host1")
    assert result is not None


# ----------------------------------------------------------------------
# Rule Set tools
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_rule_sets(mock_client):
    mock_rs = types.SimpleNamespace(name="ruleset1")
    mock_client.list_rule_sets.return_value = MockResponse(data=[mock_rs])

    result = server.list_rule_sets.fn(load_balancer_id="lb_ocid", limit=None)
    mock_client.list_rule_sets.assert_called_once_with("lb_ocid")
    assert isinstance(result, list)
    assert result[0].name == "ruleset1"


@pytest.mark.asyncio
async def test_create_rule_set(mock_client):
    mock_resp = MagicMock()
    mock_client.create_rule_set.return_value = MockResponse(data=mock_resp)

    result = server.create_rule_set.fn(
        load_balancer_id="lb_ocid", name="ruleset1", items=[]
    )
    mock_client.create_rule_set.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_get_rule_set(mock_client):
    mock_rs = types.SimpleNamespace(name="ruleset1")
    mock_client.get_rule_set.return_value = MockResponse(data=mock_rs)

    result = server.get_rule_set.fn(load_balancer_id="lb_ocid", name="ruleset1")
    mock_client.get_rule_set.assert_called_once_with("lb_ocid", "ruleset1")
    assert result.name == "ruleset1"


@pytest.mark.asyncio
async def test_update_rule_set(mock_client):
    mock_resp = MagicMock()
    mock_client.update_rule_set.return_value = MockResponse(data=mock_resp)

    result = server.update_rule_set.fn(
        load_balancer_id="lb_ocid", name="ruleset1", items=[]
    )
    mock_client.update_rule_set.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_delete_rule_set(mock_client):
    mock_resp = MagicMock()
    mock_client.delete_rule_set.return_value = MockResponse(data=mock_resp)

    result = server.delete_rule_set.fn(load_balancer_id="lb_ocid", name="ruleset1")
    mock_client.delete_rule_set.assert_called_once_with("lb_ocid", "ruleset1")
    assert result is not None


# ----------------------------------------------------------------------
# Routing Policy tools
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_routing_policies(mock_client):
    mock_rp = types.SimpleNamespace(name="policy1")
    mock_client.list_routing_policies.return_value = MockResponse(data=[mock_rp])

    result = server.list_routing_policies.fn(load_balancer_id="lb_ocid", limit=None)
    mock_client.list_routing_policies.assert_called_once_with(
        "lb_ocid", limit=None, page=None
    )
    assert isinstance(result, list)
    assert result[0].name == "policy1"


@pytest.mark.asyncio
async def test_create_routing_policy(mock_client):
    mock_client.create_routing_policy.return_value = MockResponse(data={})
    out = server.create_routing_policy.fn(
        load_balancer_id="lb", name="rp1", condition_language_version="V1", rules=[]
    )
    assert out is not None


@pytest.mark.asyncio
async def test_update_backend_all_flags(mock_client):
    mock_client.update_backend.return_value = MockResponse(data={})
    out = server.update_backend.fn(
        load_balancer_id="lb",
        backend_set_name="bs",
        backend_name="1.1.1.1:80",
        weight=5,
        max_connections=200,
        backup=True,
        drain=True,
        offline=False,
    )
    assert out is not None


@pytest.mark.asyncio
async def test_get_routing_policy(mock_client):
    mock_rp = types.SimpleNamespace(name="policy1")
    mock_client.get_routing_policy.return_value = MockResponse(data=mock_rp)

    result = server.get_routing_policy.fn(load_balancer_id="lb_ocid", name="policy1")
    mock_client.get_routing_policy.assert_called_once_with("lb_ocid", "policy1")
    assert result.name == "policy1"


@pytest.mark.asyncio
async def test_update_routing_policy(mock_client):
    mock_resp = MagicMock()
    mock_client.update_routing_policy.return_value = MockResponse(data=mock_resp)

    result = server.update_routing_policy.fn(
        load_balancer_id="lb_ocid",
        name="policy1",
        condition_language_version=None,
        rules=[],
    )
    mock_client.update_routing_policy.assert_called_once()
    assert result is not None


@pytest.mark.asyncio
async def test_delete_routing_policy(mock_client):
    mock_resp = MagicMock()
    mock_client.delete_routing_policy.return_value = MockResponse(data=mock_resp)

    result = server.delete_routing_policy.fn(load_balancer_id="lb_ocid", name="policy1")
    mock_client.delete_routing_policy.assert_called_once_with("lb_ocid", "policy1")
    assert result is not None


# ----------------------------------------------------------------------
# Health and Work Request tools
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_load_balancer_health(mock_client):
    mock_health = types.SimpleNamespace(status="OK")
    mock_client.get_load_balancer_health.return_value = MockResponse(data=mock_health)

    result = server.get_load_balancer_health.fn(load_balancer_id="lb_ocid")
    mock_client.get_load_balancer_health.assert_called_once_with("lb_ocid")
    assert result.status == "OK"


@pytest.mark.asyncio
async def test_get_backend_set_health(mock_client):
    mock_h = types.SimpleNamespace(status="WARNING")
    mock_client.get_backend_set_health.return_value = MockResponse(data=mock_h)

    result = server.get_backend_set_health.fn(
        load_balancer_id="lb_ocid", backend_set_name="bs1"
    )
    mock_client.get_backend_set_health.assert_called_once_with("lb_ocid", "bs1")
    assert result.status == "WARNING"


@pytest.mark.asyncio
async def test_get_backend_health(mock_client):
    mock_h = types.SimpleNamespace(status="CRITICAL")
    mock_client.get_backend_health.return_value = MockResponse(data=mock_h)

    result = server.get_backend_health.fn(
        load_balancer_id="lb_ocid", backend_set_name="bs1", backend_name="10.0.0.1:8080"
    )
    mock_client.get_backend_health.assert_called_once_with(
        "lb_ocid", "bs1", "10.0.0.1:8080"
    )
    assert result.status == "CRITICAL"


@pytest.mark.asyncio
async def test_list_load_balancer_healths(mock_client):
    mock_sum = types.SimpleNamespace(load_balancer_id="lb_ocid")
    mock_client.list_load_balancer_healths.return_value = MockResponse(data=[mock_sum])

    result = server.list_load_balancer_healths.fn(
        compartment_id="compartment_ocid", limit=None
    )
    mock_client.list_load_balancer_healths.assert_called_once()
    assert isinstance(result, list)
    assert result[0].load_balancer_id == "lb_ocid"


@pytest.mark.asyncio
async def test_list_load_balancer_work_requests(mock_client):
    mock_wr = types.SimpleNamespace(id="wr_ocid")
    mock_client.list_work_requests.return_value = MockResponse(data=[mock_wr])

    result = server.list_load_balancer_work_requests.fn(
        load_balancer_id="lb_ocid", limit=None
    )
    mock_client.list_work_requests.assert_called_once()
    assert isinstance(result, list)
    assert result[0].id == "wr_ocid"


@pytest.mark.asyncio
async def test_get_load_balancer_work_request(mock_client):
    mock_wr = types.SimpleNamespace(id="wr_ocid")
    mock_client.get_work_request.return_value = MockResponse(data=mock_wr)

    result = server.get_load_balancer_work_request.fn(work_request_id="wr_ocid")
    mock_client.get_work_request.assert_called_once_with("wr_ocid")
    assert result.id == "wr_ocid"


# Additional coverage-focused tests exercising optional branches


@pytest.mark.asyncio
async def test_error_paths_all_tools(monkeypatch):
    # Override client getter to force exceptions in each tool to hit except/log paths
    def _raise():
        raise RuntimeError("forced error")

    monkeypatch.setattr(server, "get_load_balancer_client", _raise)

    cases = [
        (server.list_load_balancers.fn, {"compartment_id": "c"}),
        (server.get_load_balancer.fn, {"load_balancer_id": "lb"}),
        (
            server.create_load_balancer.fn,
            {
                "compartment_id": "c",
                "display_name": "d",
                "shape_name": "s",
                "subnet_ids": ["s1"],
            },
        ),
        (server.update_load_balancer.fn, {"load_balancer_id": "lb"}),
        (server.update_load_balancer_shape.fn, {"load_balancer_id": "lb"}),
        (server.delete_load_balancer.fn, {"load_balancer_id": "lb"}),
        (
            server.update_load_balancer_network_security_groups.fn,
            {"load_balancer_id": "lb"},
        ),
        (server.list_load_balancer_listeners.fn, {"load_balancer_id": "lb"}),
        (
            server.create_load_balancer_listener.fn,
            {
                "load_balancer_id": "lb",
                "name": "n",
                "default_backend_set_name": "b",
                "port": 80,
                "protocol": "HTTP",
            },
        ),
        (
            server.get_load_balancer_listener.fn,
            {"load_balancer_id": "lb", "listener_name": "n"},
        ),
        (
            server.update_load_balancer_listener.fn,
            {"load_balancer_id": "lb", "listener_name": "n"},
        ),
        (
            server.delete_load_balancer_listener.fn,
            {"load_balancer_id": "lb", "listener_name": "n"},
        ),
        (server.list_load_balancer_backend_sets.fn, {"load_balancer_id": "lb"}),
        (
            server.get_load_balancer_backend_set.fn,
            {"load_balancer_id": "lb", "backend_set_name": "bs"},
        ),
        (
            server.create_load_balancer_backend_set.fn,
            {
                "load_balancer_id": "lb",
                "name": "bs",
                "policy": "ROUND_ROBIN",
                "health_checker_protocol": "HTTP",
            },
        ),
        (
            server.update_load_balancer_backend_set.fn,
            {"load_balancer_id": "lb", "name": "bs"},
        ),
        (
            server.delete_load_balancer_backend_set.fn,
            {"load_balancer_id": "lb", "name": "bs"},
        ),
        (
            server.list_backends.fn,
            {"load_balancer_id": "lb", "backend_set_name": "bs"},
        ),
        (
            server.create_backend.fn,
            {
                "load_balancer_id": "lb",
                "backend_set_name": "bs",
                "ip_address": "1.1.1.1",
                "port": 80,
            },
        ),
        (
            server.get_backend.fn,
            {
                "load_balancer_id": "lb",
                "backend_set_name": "bs",
                "backend_name": "1.1.1.1:80",
            },
        ),
        (
            server.update_backend.fn,
            {
                "load_balancer_id": "lb",
                "backend_set_name": "bs",
                "backend_name": "1.1.1.1:80",
            },
        ),
        (
            server.delete_backend.fn,
            {
                "load_balancer_id": "lb",
                "backend_set_name": "bs",
                "backend_name": "1.1.1.1:80",
            },
        ),
        (server.list_load_balancer_certificates.fn, {"load_balancer_id": "lb"}),
        (
            server.create_load_balancer_certificate.fn,
            {
                "load_balancer_id": "lb",
                "certificate_name": "c",
                "public_certificate": "p",
                "private_key": "k",
            },
        ),
        (
            server.delete_load_balancer_certificate.fn,
            {"load_balancer_id": "lb", "certificate_name": "c"},
        ),
        (server.list_ssl_cipher_suites.fn, {"load_balancer_id": "lb"}),
        (
            server.create_ssl_cipher_suite.fn,
            {"load_balancer_id": "lb", "name": "n", "ciphers": ["c"]},
        ),
        (
            server.get_ssl_cipher_suite.fn,
            {"load_balancer_id": "lb", "name": "n"},
        ),
        (
            server.update_ssl_cipher_suite.fn,
            {"load_balancer_id": "lb", "name": "n"},
        ),
        (
            server.delete_ssl_cipher_suite.fn,
            {"load_balancer_id": "lb", "name": "n"},
        ),
        (server.list_hostnames.fn, {"load_balancer_id": "lb"}),
        (
            server.create_hostname.fn,
            {"load_balancer_id": "lb", "name": "h", "hostname": "x"},
        ),
        (
            server.get_hostname.fn,
            {"load_balancer_id": "lb", "name": "h"},
        ),
        (
            server.update_hostname.fn,
            {"load_balancer_id": "lb", "name": "h"},
        ),
        (
            server.delete_hostname.fn,
            {"load_balancer_id": "lb", "name": "h"},
        ),
        (server.list_rule_sets.fn, {"load_balancer_id": "lb"}),
        (
            server.create_rule_set.fn,
            {"load_balancer_id": "lb", "name": "rs"},
        ),
        (
            server.get_rule_set.fn,
            {"load_balancer_id": "lb", "name": "rs"},
        ),
        (
            server.update_rule_set.fn,
            {"load_balancer_id": "lb", "name": "rs"},
        ),
        (
            server.delete_rule_set.fn,
            {"load_balancer_id": "lb", "name": "rs"},
        ),
        (server.list_routing_policies.fn, {"load_balancer_id": "lb"}),
        (
            server.create_routing_policy.fn,
            {"load_balancer_id": "lb", "name": "rp"},
        ),
        (
            server.get_routing_policy.fn,
            {"load_balancer_id": "lb", "name": "rp"},
        ),
        (
            server.update_routing_policy.fn,
            {"load_balancer_id": "lb", "name": "rp"},
        ),
        (
            server.delete_routing_policy.fn,
            {"load_balancer_id": "lb", "name": "rp"},
        ),
        (server.get_load_balancer_health.fn, {"load_balancer_id": "lb"}),
        (
            server.get_backend_set_health.fn,
            {"load_balancer_id": "lb", "backend_set_name": "bs"},
        ),
        (
            server.get_backend_health.fn,
            {
                "load_balancer_id": "lb",
                "backend_set_name": "bs",
                "backend_name": "1.1.1.1:80",
            },
        ),
        (server.list_load_balancer_healths.fn, {"compartment_id": "c"}),
        (server.list_load_balancer_work_requests.fn, {"load_balancer_id": "lb"}),
        (server.get_load_balancer_work_request.fn, {"work_request_id": "wr"}),
    ]

    for func, kwargs in cases:
        with pytest.raises(RuntimeError):
            func(**kwargs)


@pytest.mark.asyncio
async def test_get_load_balancer_backend_set(mock_client):
    mock_bs = types.SimpleNamespace(name="bs1")
    mock_client.get_backend_set.return_value = MockResponse(data=mock_bs)
    res = server.get_load_balancer_backend_set.fn(
        load_balancer_id="lb_ocid", backend_set_name="bs1"
    )
    mock_client.get_backend_set.assert_called_once_with("lb_ocid", "bs1")
    assert res.name == "bs1"


@pytest.mark.asyncio
async def test_get_ssl_cipher_suite(mock_client):
    mock_s = types.SimpleNamespace(name="s1", ciphers=["C1"])
    mock_client.get_ssl_cipher_suite.return_value = MockResponse(data=mock_s)
    res = server.get_ssl_cipher_suite.fn(load_balancer_id="lb_ocid", name="s1")
    mock_client.get_ssl_cipher_suite.assert_called_once_with("lb_ocid", "s1")
    assert res.name == "s1"


@pytest.mark.asyncio
async def test_create_backend_set_full_options(mock_client):
    mock_client.create_backend_set.return_value = MockResponse(data={})
    res = server.create_load_balancer_backend_set.fn(
        load_balancer_id="lb",
        name="bs",
        policy="ROUND_ROBIN",
        health_checker_protocol="HTTP",
        health_checker_url_path="/health",
        health_checker_port=8080,
        health_checker_return_code=200,
        health_checker_retries=2,
        health_checker_timeout_in_millis=5000,
        health_checker_interval_in_millis=10000,
        health_checker_response_body_regex="OK",
        health_checker_is_force_plain_text=True,
        backends=[],
        backend_max_connections=300,
        ssl_protocols=["TLSv1.2"],
        ssl_cipher_suite_name="suite",
        ssl_server_order_preference="ENABLED",
        ssl_certificate_name="cert",
        ssl_certificate_ids=["cid"],
        ssl_trusted_certificate_authority_ids=["tid"],
        ssl_has_session_resumption=True,
        ssl_verify_peer_certificate=False,
        ssl_verify_depth=3,
        session_persistence_cookie_name="app",
        session_persistence_disable_fallback=True,
        lb_cookie_cookie_name="lb",
        lb_cookie_disable_fallback=True,
        lb_cookie_domain="example.com",
        lb_cookie_path="/",
        lb_cookie_max_age_in_seconds=60,
        lb_cookie_is_secure=True,
        lb_cookie_is_http_only=True,
    )
    assert res is not None


@pytest.mark.asyncio
async def test_update_backend_set_full_options(mock_client):
    # Provide current backend set with health checker for preservation logic
    current_bs = types.SimpleNamespace(
        policy="ROUND_ROBIN",
        backends=[],
        health_checker=types.SimpleNamespace(
            protocol="HTTP",
            url_path="/h",
            port=80,
            return_code=200,
            retries=3,
            timeout_in_millis=3000,
            interval_in_millis=5000,
            response_body_regex="OK",
            is_force_plain_text=False,
        ),
    )
    mock_client.get_backend_set.return_value = MockResponse(data=current_bs)
    mock_client.update_backend_set.return_value = MockResponse(data={})

    res = server.update_load_balancer_backend_set.fn(
        load_balancer_id="lb",
        name="bs",
        policy="LEAST_CONNECTIONS",
        backends=[],
        health_checker_protocol="HTTP",
        health_checker_url_path="/health",
        health_checker_port=8080,
        health_checker_return_code=200,
        health_checker_retries=2,
        health_checker_timeout_in_millis=5000,
        health_checker_interval_in_millis=10000,
        health_checker_response_body_regex="OK",
        health_checker_is_force_plain_text=True,
        ssl_protocols=["TLSv1.2"],
        ssl_cipher_suite_name="suite",
        ssl_server_order_preference="DISABLED",
        ssl_certificate_name="cert",
        ssl_certificate_ids=["cid"],
        ssl_trusted_certificate_authority_ids=["tid"],
        ssl_has_session_resumption=True,
        ssl_verify_peer_certificate=True,
        ssl_verify_depth=4,
        session_persistence_cookie_name="app",
        session_persistence_disable_fallback=False,
        lb_cookie_cookie_name="lb",
        lb_cookie_disable_fallback=False,
        lb_cookie_domain="example.com",
        lb_cookie_path="/",
        lb_cookie_max_age_in_seconds=120,
        lb_cookie_is_secure=True,
        lb_cookie_is_http_only=False,
    )
    assert res is not None


@pytest.mark.asyncio
async def test_update_backend_set_preserve_existing(mock_client):
    existing_backend = types.SimpleNamespace(
        ip_address="1.1.1.1",
        port=80,
        weight=1,
        max_connections=256,
        backup=False,
        drain=False,
        offline=False,
    )
    current_bs = types.SimpleNamespace(
        policy="ROUND_ROBIN",
        backends=[existing_backend],
        health_checker=types.SimpleNamespace(
            protocol="HTTP",
            url_path="/h",
            port=80,
            return_code=200,
            retries=3,
            timeout_in_millis=3000,
            interval_in_millis=5000,
            response_body_regex="OK",
            is_force_plain_text=False,
        ),
    )
    mock_client.get_backend_set.return_value = MockResponse(data=current_bs)
    mock_client.update_backend_set.return_value = MockResponse(data={})

    # Do not pass backends or HC details so preservation paths are used
    out = server.update_load_balancer_backend_set.fn(
        load_balancer_id="lb", name="bs", backends=None
    )
    assert out is not None
