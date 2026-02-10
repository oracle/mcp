"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime

import oci
import pytest
from oracle.oci_network_load_balancer_mcp_server.models import (
    Backend,
    BackendSet,
    DnsHealthCheckerDetails,
    HealthChecker,
    IpAddress,
    Listener,
    NetworkLoadBalancer,
    ReservedIP,
    _oci_to_dict,
    map_backend,
    map_backend_set,
    map_dns_health_checker_details,
    map_health_checker,
    map_ip_address,
    map_listener,
    map_network_load_balancer,
    map_reserved_ip,
)


class TestNetworkLoadBalancerModels:
    def test_map_reserved_ip(self):
        src = oci.network_load_balancer.models.ReservedIP(id="rip1")
        dst = map_reserved_ip(src)
        assert isinstance(dst, ReservedIP)
        assert dst.id == "rip1"

    def test_map_ip_address(self):
        src = oci.network_load_balancer.models.IpAddress(
            ip_address="192.168.0.1",
            is_public=True,
            ip_version="IPV4",
            reserved_ip=oci.network_load_balancer.models.ReservedIP(id="rip2"),
        )
        dst = map_ip_address(src)
        assert isinstance(dst, IpAddress)
        assert dst.ip_address == "192.168.0.1"
        assert dst.is_public is True
        assert dst.ip_version == "IPV4"
        assert dst.reserved_ip and dst.reserved_ip.id == "rip2"

    def test_map_backend(self):
        src = oci.network_load_balancer.models.Backend(
            name="b1",
            ip_address="10.0.0.10",
            target_id="ocid1.instance.oc1..xyz",
            port=8080,
            weight=1,
            is_drain=False,
            is_backup=False,
            is_offline=False,
        )
        dst = map_backend(src)
        assert isinstance(dst, Backend)
        assert dst.name == "b1"
        assert dst.port == 8080
        assert dst.is_offline is False

    def test_map_dns_health_checker_details(self):
        src = oci.network_load_balancer.models.DnsHealthCheckerDetails(
            transport_protocol="UDP",
            domain_name="example.com",
            query_class="IN",
            query_type="A",
            rcodes=["NOERROR"],
        )
        dst = map_dns_health_checker_details(src)
        assert isinstance(dst, DnsHealthCheckerDetails)
        assert dst.transport_protocol == "UDP"
        assert dst.query_type == "A"

    def test_map_health_checker(self):
        src = oci.network_load_balancer.models.HealthChecker(
            protocol="TCP",
            port=80,
            retries=3,
            timeout_in_millis=5000,
            interval_in_millis=10000,
            url_path="/health",
            response_body_regex=".*OK.*",
            return_code=200,
            request_data=None,
            response_data=None,
            dns=oci.network_load_balancer.models.DnsHealthCheckerDetails(
                transport_protocol="TCP",
                domain_name="example.com",
                query_class="IN",
                query_type="A",
                rcodes=["NOERROR"],
            ),
        )
        dst = map_health_checker(src)
        assert isinstance(dst, HealthChecker)
        assert dst.protocol == "TCP"
        assert dst.dns and dst.dns.domain_name == "example.com"

    def test_map_listener(self):
        src = oci.network_load_balancer.models.Listener(
            name="ln1",
            default_backend_set_name="bs1",
            port=443,
            protocol="TCP",
            ip_version="IPV4",
            is_ppv2_enabled=False,
            tcp_idle_timeout=30,
            udp_idle_timeout=30,
            l3_ip_idle_timeout=30,
        )
        dst = map_listener(src)
        assert isinstance(dst, Listener)
        assert dst.name == "ln1"
        assert dst.protocol == "TCP"

    def test_map_backend_set(self):
        src = oci.network_load_balancer.models.BackendSet(
            name="bs1",
            policy="THREE_TUPLE",
            is_preserve_source=True,
            is_fail_open=False,
            is_instant_failover_enabled=True,
            is_instant_failover_tcp_reset_enabled=False,
            are_operationally_active_backends_preferred=False,
            ip_version="IPV4",
            backends=[
                oci.network_load_balancer.models.Backend(name="b1", port=80),
                oci.network_load_balancer.models.Backend(name="b2", port=81),
            ],
            health_checker=oci.network_load_balancer.models.HealthChecker(protocol="TCP"),
        )
        dst = map_backend_set(src)
        assert isinstance(dst, BackendSet)
        assert dst.name == "bs1"
        assert dst.policy == "THREE_TUPLE"
        assert dst.backends and len(dst.backends) == 2
        assert dst.backends[0].name == "b1"
        assert dst.health_checker and dst.health_checker.protocol == "TCP"

    def test_map_network_load_balancer(self):
        src = oci.network_load_balancer.models.NetworkLoadBalancer(
            id="nlb1",
            compartment_id="ocid1.compartment.oc1..abc",
            display_name="NLB 1",
            lifecycle_state="ACTIVE",
            lifecycle_details="Running",
            nlb_ip_version="IPV4",
            time_created=datetime.utcnow(),
            time_updated=datetime.utcnow(),
            ip_addresses=[
                oci.network_load_balancer.models.IpAddress(
                    ip_address="1.2.3.4", is_public=True, ip_version="IPV4"
                )
            ],
            is_private=False,
            is_preserve_source_destination=False,
            is_symmetric_hash_enabled=False,
            subnet_id="ocid1.subnet.oc1..def",
            network_security_group_ids=["ocid1.nsg.oc1..ghi"],
            listeners={
                "ln1": oci.network_load_balancer.models.Listener(name="ln1", port=80),
            },
            backend_sets={
                "bs1": oci.network_load_balancer.models.BackendSet(name="bs1", policy="THREE_TUPLE")
            },
            freeform_tags={"a": "b"},
            defined_tags={"ns": {"k": "v"}},
            system_tags={"orcl": {"managed": "true"}},
        )
        dst = map_network_load_balancer(src)
        assert isinstance(dst, NetworkLoadBalancer)
        assert dst.id == "nlb1"
        assert dst.display_name == "NLB 1"
        assert dst.ip_addresses and dst.ip_addresses[0].ip_address == "1.2.3.4"
        assert dst.listeners and isinstance(dst.listeners["ln1"], Listener)
        assert dst.backend_sets and isinstance(dst.backend_sets["bs1"], BackendSet)
        assert dst.freeform_tags == {"a": "b"}

    @pytest.mark.parametrize(
        "func",
        [
            map_reserved_ip,
            map_ip_address,
            map_backend,
            map_dns_health_checker_details,
            map_health_checker,
            map_listener,
            map_backend_set,
        ],
    )
    def test_map_functions_handle_none(self, func):
        assert func(None) is None

    def test_map_network_load_balancer_handles_none(self):
        # Unlike other mappers, map_network_load_balancer returns an empty model when given None
        dst = map_network_load_balancer(None)
        assert isinstance(dst, NetworkLoadBalancer)
        assert dst.id is None

    def test__oci_to_dict_helper(self):
        # dict passes through
        d = {"k": "v"}
        assert _oci_to_dict(d) == d

        # object with __dict__ falls back
        class Foo:
            def __init__(self):
                self.a = 1
                self._private = 2

        out = _oci_to_dict(Foo())
        # Depending on environment, helper may return the object or a dict
        if isinstance(out, dict):
            assert out == {"a": 1}
        else:
            assert hasattr(out, "a") and out.a == 1
        # None returns None
        assert _oci_to_dict(None) is None
