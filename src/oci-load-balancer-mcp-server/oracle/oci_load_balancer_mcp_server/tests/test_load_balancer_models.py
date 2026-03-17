"""
Unit tests for the model mapping functions in ``models.py`` of the OCI Load Balancer MCP server.

The tests construct lightweight mock objects that mimic the attributes of OCI SDK models
and verify that the ``map_*`` functions correctly translate them into the corresponding
Pydantic models. All tests are asynchronous and marked with ``@pytest.mark.asyncio``.
"""

import types

import pytest
from oracle.oci_load_balancer_mcp_server import models


def make_obj(**attrs):
    """Utility to create a simple object with given attributes."""
    return types.SimpleNamespace(**attrs)


@pytest.mark.asyncio
async def test_map_ip_address():
    ip_obj = make_obj(
        ip_address="10.0.0.1", is_public=True, reserved_ip=make_obj(id="reserved_ocid")
    )
    result = models.map_ip_address(ip_obj)
    assert result.ip_address == "10.0.0.1"
    assert result.is_public is True
    assert result.reserved_ip.id == "reserved_ocid"


@pytest.mark.asyncio
async def test_map_shape_details():
    shape_obj = make_obj(minimum_bandwidth_in_mbps=100, maximum_bandwidth_in_mbps=200)
    result = models.map_shape_details(shape_obj)
    assert result.minimum_bandwidth_in_mbps == 100
    assert result.maximum_bandwidth_in_mbps == 200


@pytest.mark.asyncio
async def test_map_connection_configuration():
    conn_obj = make_obj(
        idle_timeout=30,
        backend_tcp_proxy_protocol_version=1,
        backend_tcp_proxy_protocol_options=["PP2_TYPE_AUTHORITY"],
    )
    result = models.map_connection_configuration(conn_obj)
    assert result.idle_timeout == 30
    assert result.backend_tcp_proxy_protocol_version == 1
    assert result.backend_tcp_proxy_protocol_options == ["PP2_TYPE_AUTHORITY"]


@pytest.mark.asyncio
async def test_map_ssl_configuration():
    ssl_obj = make_obj(
        verify_depth=3,
        verify_peer_certificate=True,
        has_session_resumption=False,
        trusted_certificate_authority_ids=["ca1"],
        certificate_ids=["cert1"],
        certificate_name="mycert",
        server_order_preference="ENABLED",
        cipher_suite_name="TLS_AES_128_GCM_SHA256",
        protocols=["TLSv1.2", "TLSv1.3"],
    )
    result = models.map_ssl_configuration(ssl_obj)
    assert result.verify_depth == 3
    assert result.verify_peer_certificate is True
    assert result.has_session_resumption is False
    assert result.trusted_certificate_authority_ids == ["ca1"]
    assert result.certificate_ids == ["cert1"]
    assert result.certificate_name == "mycert"
    assert result.server_order_preference == "ENABLED"
    assert result.cipher_suite_name == "TLS_AES_128_GCM_SHA256"
    assert result.protocols == ["TLSv1.2", "TLSv1.3"]


@pytest.mark.asyncio
async def test_map_backend():
    backend_obj = make_obj(
        name="backend1",
        ip_address="10.0.0.2",
        port=8080,
        weight=5,
        max_connections=100,
        drain=False,
        backup=True,
        offline=False,
    )
    result = models.map_backend(backend_obj)
    assert result.name == "backend1"
    assert result.ip_address == "10.0.0.2"
    assert result.port == 8080
    assert result.weight == 5
    assert result.max_connections == 100
    assert result.drain is False
    assert result.backup is True
    assert result.offline is False


@pytest.mark.asyncio
async def test_map_health_checker():
    hc_obj = make_obj(
        protocol="HTTP",
        url_path="/health",
        port=8080,
        return_code=200,
        retries=3,
        timeout_in_millis=5000,
        interval_in_millis=10000,
        response_body_regex="OK",
        is_force_plain_text=False,
    )
    result = models.map_health_checker(hc_obj)
    assert result.protocol == "HTTP"
    assert result.url_path == "/health"
    assert result.port == 8080
    assert result.return_code == 200
    assert result.retries == 3
    assert result.timeout_in_millis == 5000
    assert result.interval_in_millis == 10000
    assert result.response_body_regex == "OK"
    assert result.is_force_plain_text is False


@pytest.mark.asyncio
async def test_map_certificate():
    cert_obj = make_obj(
        certificate_name="cert1",
        public_certificate="---PUBLIC---",
        ca_certificate="---CA---",
    )
    result = models.map_certificate(cert_obj)
    assert result.certificate_name == "cert1"
    assert result.public_certificate == "---PUBLIC---"
    assert result.ca_certificate == "---CA---"


@pytest.mark.asyncio
async def test_map_listener():
    listener_obj = make_obj(
        name="listener1",
        default_backend_set_name="bs1",
        port=80,
        protocol="HTTP",
        hostname_names=["host1"],
        path_route_set_name=None,
        ssl_configuration=make_obj(protocols=["TLSv1.2"]),
        connection_configuration=make_obj(idle_timeout=30),
        rule_set_names=["rs1"],
        routing_policy_name="rp1",
    )
    result = models.map_listener(listener_obj)
    assert result.name == "listener1"
    assert result.default_backend_set_name == "bs1"
    assert result.port == 80
    assert result.protocol == "HTTP"
    assert result.hostname_names == ["host1"]
    assert result.path_route_set_name is None
    assert result.ssl_configuration.protocols == ["TLSv1.2"]
    assert result.connection_configuration.idle_timeout == 30
    assert result.rule_set_names == ["rs1"]
    assert result.routing_policy_name == "rp1"


@pytest.mark.asyncio
async def test_map_rule_set(monkeypatch):
    # Ensure _oci_to_dict returns a plain dict for simple objects to avoid TypeError
    monkeypatch.setattr(
        models,
        "_oci_to_dict",
        lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", None),
    )
    rule_set_obj = make_obj(
        name="rs1",
        items=[make_obj(action="ADD_HTTP_REQUEST_HEADER", header="X-Test")],
    )
    result = models.map_rule_set(rule_set_obj)
    assert result.name == "rs1"
    assert len(result.items) == 1
    assert result.items[0].action == "ADD_HTTP_REQUEST_HEADER"
    # fields preserves raw, minus the 'action' key if present
    assert result.items[0].fields == {"header": "X-Test"}


@pytest.mark.asyncio
async def test_map_routing_policy():
    rule_obj = make_obj(
        name="rule1",
        condition="true",
        actions=[make_obj(name="FORWARD_TO_BACKENDSET", backend_set_name="bs1")],
    )
    policy_obj = make_obj(
        name="policy1", condition_language_version="V1", rules=[rule_obj]
    )
    result = models.map_routing_policy(policy_obj)
    assert result.name == "policy1"
    assert result.condition_language_version == "V1"
    assert len(result.rules) == 1
    assert result.rules[0].name == "rule1"
    assert result.rules[0].condition == "true"
    assert isinstance(result.rules[0].actions[0], models.ForwardToBackendSet)
    assert result.rules[0].actions[0].backend_set_name == "bs1"


@pytest.mark.asyncio
async def test_map_response_and_pagination_headers():
    # Simulate an OCI response with nested data
    inner_lb = make_obj(id="lb_ocid")
    resp_obj = make_obj(
        status=200,
        headers={"opc-request-id": "req123", "opc-next-page": None},
        data=inner_lb,
        request=make_obj(method="GET", url="http://example.com"),
        next_page=None,
        request_id=None,
    )
    result = models.map_response(resp_obj)
    assert result.status == 200
    assert result.headers["opc-request-id"] == "req123"
    # data may be a mapped Pydantic model or a plain dict depending on type detection
    assert (isinstance(result.data, dict) and result.data.get("id") == "lb_ocid") or (
        getattr(result.data, "id", None) == "lb_ocid"
    )
    assert result.request.method == "GET"
    assert result.request.url == "http://example.com"
    assert result.has_next_page is False


@pytest.mark.asyncio
async def test_map_load_balancer_full_structure():
    lb_obj = make_obj(
        id="lb1",
        compartment_id="comp1",
        display_name="my-lb",
        lifecycle_state="ACTIVE",
        time_created=None,
        ip_addresses=[make_obj(ip_address="1.2.3.4", is_public=True, reserved_ip=None)],
        shape_name="Flexible",
        shape_details=make_obj(
            minimum_bandwidth_in_mbps=10, maximum_bandwidth_in_mbps=100
        ),
        is_private=False,
        is_delete_protection_enabled=False,
        is_request_id_enabled=True,
        request_id_header="X-Req-Id",
        subnet_ids=["sub1"],
        network_security_group_ids=["nsg1"],
        listeners={"lsn": make_obj(name="lsn", port=80, protocol="HTTP")},
        hostnames={"h": make_obj(name="h", hostname="app.example.com")},
        ssl_cipher_suites={"s": make_obj(name="s", ciphers=["C1"])},
        certificates={"c": make_obj(certificate_name="c", public_certificate="P")},
        backend_sets={"bs": make_obj(name="bs", policy="ROUND_ROBIN", backends=[])},
        path_route_sets={"prs": make_obj(name="prs", path_routes=[])},
        rule_sets={"rs": make_obj(name="rs", items=[])},
        routing_policies={"rp": make_obj(name="rp", rules=[])},
        freeform_tags={"env": "dev"},
        defined_tags={"ns": {"k": "v"}},
        security_attributes=None,
        system_tags=None,
        ip_mode="IPV4",
    )
    result = models.map_load_balancer(lb_obj)
    assert result.id == "lb1"
    assert result.display_name == "my-lb"
    assert result.ip_addresses[0].ip_address == "1.2.3.4"
    assert result.shape_details.minimum_bandwidth_in_mbps == 10
    assert result.listeners["lsn"].port == 80
    assert result.backend_sets["bs"].policy == "ROUND_ROBIN"
    assert result.ip_mode == "IPV4"


@pytest.mark.asyncio
async def test_map_health_and_work_request_models():
    # Backend/BackendSet/LoadBalancer health mapping
    hcr = make_obj(
        subnet_id="sub1",
        source_ip_address="10.0.0.2",
        timestamp=None,
        health_check_status="OK",
    )
    bh = make_obj(status="OK", health_check_results=[hcr])
    bsh = make_obj(
        status="WARNING",
        warning_state_backend_names=["b1"],
        critical_state_backend_names=["b2"],
        unknown_state_backend_names=["b3"],
        total_backend_count=3,
    )
    lbh = make_obj(
        status="CRITICAL",
        warning_state_backend_set_names=["bs1"],
        critical_state_backend_set_names=["bs2"],
        unknown_state_backend_set_names=["bs3"],
        total_backend_set_count=3,
    )
    lbs = make_obj(load_balancer_id="lb1", status="UNKNOWN")

    mapped_bh = models.map_backend_health(bh)
    mapped_bsh = models.map_backend_set_health(bsh)
    mapped_lbh = models.map_load_balancer_health(lbh)
    mapped_lbs = models.map_load_balancer_health_summary(lbs)

    assert mapped_bh.status == "OK"
    assert mapped_bh.health_check_results[0].health_check_status == "OK"
    assert mapped_bsh.total_backend_count == 3
    assert mapped_lbh.status == "CRITICAL"
    assert mapped_lbs.load_balancer_id == "lb1"

    # Work request mapping
    wre = make_obj(error_code="BAD_INPUT", message="oops")
    wr = make_obj(
        id="wr1",
        load_balancer_id="lb1",
        type="CREATE",
        compartment_id="comp1",
        lifecycle_state="ACCEPTED",
        message="ok",
        time_accepted=None,
        time_finished=None,
        error_details=[wre],
    )
    mapped_wr = models.map_work_request(wr)
    assert mapped_wr.id == "wr1"
    assert mapped_wr.error_details[0].error_code == "BAD_INPUT"


@pytest.mark.asyncio
async def test_oci_to_dict_variants(monkeypatch):
    # None yields None
    assert models._oci_to_dict(None) is None
    # dict passthrough
    d = {"a": 1}
    assert models._oci_to_dict(d) == d

    # When oci.util.to_dict is available, it may return the object unchanged for
    # unknown types; in that case, ensure we can still access attributes.
    obj = make_obj(x=1, _private=2)
    out = models._oci_to_dict(obj)
    assert (isinstance(out, dict) and out.get("x") == 1) or getattr(out, "x", None) == 1

    # Force fallback branch (oci.util.to_dict raises) to verify underscore filtering
    import oci as _oci_module

    def _raise(_):
        raise RuntimeError("force fallback")

    monkeypatch.setattr(_oci_module.util, "to_dict", _raise)
    out2 = models._oci_to_dict(obj)
    assert out2 == {"x": 1}


@pytest.mark.asyncio
async def test_map_headers_variants(monkeypatch):
    class HeadersObj:
        def items(self):
            return [("k", "v")]

    assert models._map_headers({"a": 1}) == {"a": 1}
    assert models._map_headers(HeadersObj()) == {"k": "v"}

    # Fallback to _oci_to_dict when .items not available; it may return either a dict
    # or the original object depending on the environment. Accept either shape.
    raw = make_obj(a=1)
    out = models._map_headers(raw)
    assert (isinstance(out, dict) and out.get("a") == 1) or getattr(out, "a", None) == 1

    # Force explicit dict via fallback path
    monkeypatch.setattr(models, "_oci_to_dict", lambda obj: {"a": 1})
    assert models._map_headers(raw) == {"a": 1}


@pytest.mark.asyncio
async def test_map_response_next_page_and_request_id_from_attrs():
    resp = make_obj(
        status=200,
        headers=None,
        data=None,
        request=None,
        next_page="np",
        request_id="rid",
    )
    out = models.map_response(resp)
    assert out.next_page == "np"
    assert out.request_id == "rid"
    assert out.has_next_page is True


@pytest.mark.asyncio
async def test_map_response_data_list_and_primitives():
    # list of primitives should be returned as-is
    lst = [1, "a", True]
    # use private helper via map_response
    resp = make_obj(status=200, headers=None, data=lst, request=None)
    out = models.map_response(resp)
    assert out.data == lst


@pytest.mark.asyncio
async def test_map_action_unknown_preserves_details(monkeypatch):
    # Ensure details dict is produced regardless of oci.util behavior
    monkeypatch.setattr(
        models,
        "_oci_to_dict",
        lambda obj: {"header": "X-Test", "value": "1", "name": "ADD_HEADER"},
    )
    act = make_obj(name="ADD_HEADER", header="X-Test", value="1")
    mapped = models.map_action(act)
    assert mapped.name == "ADD_HEADER"
    assert isinstance(mapped.details, dict)
    assert mapped.details["header"] == "X-Test"


@pytest.mark.asyncio
async def test_map_path_route_set_and_routes():
    prs = make_obj(
        name="prs1",
        path_routes=[
            make_obj(
                path="/api",
                path_match_type=make_obj(match_type="PREFIX_MATCH"),
                backend_set_name="bs",
            )
        ],
    )
    mapped = models.map_path_route_set(prs)
    assert mapped.name == "prs1"
    assert mapped.path_routes[0].path == "/api"
    assert mapped.path_routes[0].path_match_type.match_type == "PREFIX_MATCH"
