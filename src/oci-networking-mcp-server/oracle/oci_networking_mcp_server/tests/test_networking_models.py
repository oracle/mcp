"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace
from unittest.mock import create_autospec

import oci
import pytest
from oracle.oci_networking_mcp_server.models import (
    EgressSecurityRule,
    IcmpOptions,
    IngressSecurityRule,
    NetworkSecurityGroup,
    PortRange,
    Request,
    Response,
    SecurityList,
    Subnet,
    TcpOptions,
    UdpOptions,
    Vcn,
    Vnic,
    map_egress_security_rule,
    map_icmp_options,
    map_ingress_security_rule,
    map_network_security_group,
    map_request,
    map_response,
    map_security_list,
    map_subnet,
    map_tcp_options,
    map_udp_options,
    map_vcn,
    map_vnic,
)


class TestModelsMapping:
    def test_map_vcn(self):
        src = oci.core.models.Vcn(
            id="vcn1",
            display_name="VCN 1",
            cidr_block="10.0.0.0/16",
            lifecycle_state="AVAILABLE",
        )
        dst = map_vcn(src)
        assert isinstance(dst, Vcn)
        assert dst.id == "vcn1"
        assert dst.display_name == "VCN 1"
        assert dst.cidr_block == "10.0.0.0/16"
        assert dst.lifecycle_state == "AVAILABLE"

    def test_map_subnet(self):
        src = oci.core.models.Subnet(
            id="subnet1",
            vcn_id="vcn1",
            display_name="Subnet 1",
            cidr_block="10.0.1.0/24",
            lifecycle_state="AVAILABLE",
        )
        dst = map_subnet(src)
        assert isinstance(dst, Subnet)
        assert dst.id == "subnet1"
        assert dst.vcn_id == "vcn1"
        assert dst.display_name == "Subnet 1"
        assert dst.cidr_block == "10.0.1.0/24"

    def test_map_port_range_and_icmp(self):
        pr = PortRange(min=22, max=22)
        assert pr.min == 22 and pr.max == 22

        icmp_src = oci.core.models.IcmpOptions(type=3, code=4)
        icmp = map_icmp_options(icmp_src)
        assert isinstance(icmp, IcmpOptions)
        assert icmp.type == 3 and icmp.code == 4

    def test_map_tcp_udp_options_single_ranges(self):
        tcp_src = oci.core.models.TcpOptions(
            destination_port_range=oci.core.models.PortRange(min=80, max=80),
            source_port_range=oci.core.models.PortRange(min=1000, max=2000),
        )
        tcp = map_tcp_options(tcp_src)
        assert isinstance(tcp, TcpOptions)
        assert tcp.destination_port_range.min == 80
        assert tcp.source_port_range.max == 2000

        udp_src = oci.core.models.UdpOptions(
            destination_port_range=oci.core.models.PortRange(min=53, max=53),
            source_port_range=oci.core.models.PortRange(min=4000, max=5000),
        )
        udp = map_udp_options(udp_src)
        assert isinstance(udp, UdpOptions)
        assert udp.destination_port_range.min == 53
        assert udp.source_port_range.max == 5000

    def test_map_tcp_udp_options_list_ranges_via_dict(self):
        tcp_dict = {
            "destination_port_ranges": [
                {"min": 443, "max": 443},
                {"min": 8443, "max": 8443},
            ],
            "source_port_ranges": [
                {"min": 0, "max": 65535},
            ],
        }
        tcp = map_tcp_options(tcp_dict)
        assert isinstance(tcp, TcpOptions)
        assert tcp.destination_port_ranges and len(tcp.destination_port_ranges) == 2
        assert tcp.destination_port_ranges[0].min == 443
        assert tcp.source_port_ranges[0].max == 65535

        udp_dict = {
            "destination_port_ranges": [
                {"min": 67, "max": 67},
                {"min": 68, "max": 68},
            ],
            "source_port_ranges": [
                {"min": 67, "max": 68},
            ],
        }
        udp = map_udp_options(udp_dict)
        assert isinstance(udp, UdpOptions)
        assert udp.destination_port_ranges[1].min == 68
        assert udp.source_port_ranges[0].min == 67

    def test_map_egress_ingress_rules(self):
        egress_src = oci.core.models.EgressSecurityRule(
            description="allow web",
            destination="0.0.0.0/0",
            protocol="6",  # TCP
            tcp_options=oci.core.models.TcpOptions(
                destination_port_range=oci.core.models.PortRange(min=80, max=80)
            ),
        )
        egress = map_egress_security_rule(egress_src)
        assert isinstance(egress, EgressSecurityRule)
        assert egress.description == "allow web"
        assert egress.tcp_options.destination_port_range.min == 80

        ingress_dict = {
            "description": "allow ssh",
            "source": "0.0.0.0/0",
            "protocol": "6",
            "tcp_options": {"destination_port_range": {"min": 22, "max": 22}},
        }
        ingress = map_ingress_security_rule(ingress_dict)
        assert isinstance(ingress, IngressSecurityRule)
        assert ingress.tcp_options.destination_port_range.max == 22

    def test_map_security_list(self):
        sl_src = oci.core.models.SecurityList(
            id="sl1",
            display_name="SL 1",
            egress_security_rules=[
                oci.core.models.EgressSecurityRule(
                    destination="0.0.0.0/0",
                    protocol="all",
                )
            ],
            ingress_security_rules=[
                oci.core.models.IngressSecurityRule(
                    source="0.0.0.0/0",
                    protocol="6",
                    tcp_options=oci.core.models.TcpOptions(
                        destination_port_range=oci.core.models.PortRange(min=443, max=443)
                    ),
                )
            ],
            lifecycle_state="AVAILABLE",
        )
        sl = map_security_list(sl_src)
        assert isinstance(sl, SecurityList)
        assert sl.id == "sl1"
        assert sl.egress_security_rules and sl.ingress_security_rules
        assert sl.ingress_security_rules[0].tcp_options.destination_port_range.min == 443

    def test_map_network_security_group(self):
        nsg_src = oci.core.models.NetworkSecurityGroup(
            id="nsg1",
            display_name="NSG 1",
            lifecycle_state="AVAILABLE",
            vcn_id="vcn1",
        )
        nsg = map_network_security_group(nsg_src)
        assert isinstance(nsg, NetworkSecurityGroup)
        assert nsg.id == "nsg1" and nsg.vcn_id == "vcn1"

    def test_map_vnic(self):
        vnic_src = oci.core.models.Vnic(
            id="vnic1",
            display_name="VNIC 1",
            lifecycle_state="AVAILABLE",
            private_ip="10.0.0.10",
        )
        vnic = map_vnic(vnic_src)
        assert isinstance(vnic, Vnic)
        assert vnic.id == "vnic1"
        assert vnic.private_ip == "10.0.0.10"

    def test_map_request(self):
        req_src = SimpleNamespace(
            method="GET",
            url="https://example.com",
            query_params={"a": 1},
            header_params={"h": "v"},
            body=None,
            response_type="json",
            enforce_content_headers=True,
        )
        req = map_request(req_src)
        assert isinstance(req, Request)
        assert req.method == "GET" and req.url == "https://example.com"
        assert req.query_params == {"a": 1}

    def test_map_response_with_header_derived_fields(self):
        mock_resp = create_autospec(oci.response.Response)
        mock_resp.status = 200
        mock_resp.headers = {
            "opc-next-page": "token123",
            "opc-request-id": "req-abc",
        }
        mock_resp.data = oci.core.models.Vcn(id="vcn1")
        mock_resp.request = SimpleNamespace(method="GET", url="http://x")
        mock_resp.next_page = None
        mock_resp.request_id = None

        mapped = map_response(mock_resp)
        assert isinstance(mapped, Response)
        assert mapped.status == 200
        # next_page/request_id derived from headers
        assert mapped.next_page == "token123"
        assert mapped.request_id == "req-abc"
        assert mapped.has_next_page is True
        # data should be mapped Vcn object
        assert isinstance(mapped.data, Vcn)
        assert mapped.data.id == "vcn1"

    def test_map_response_with_attrs_and_various_data(self):
        # Build a response without headers but with attrs set
        mock_resp = create_autospec(oci.response.Response)
        mock_resp.status = 201
        mock_resp.headers = None
        mock_resp.data = [
            oci.core.models.Subnet(id="s1"),
            {"k": "v"},
            1,
            "x",
        ]
        mock_resp.request = None
        mock_resp.next_page = "np"
        mock_resp.request_id = "rid"

        mapped = map_response(mock_resp)
        assert mapped.status == 201
        assert mapped.next_page == "np"
        assert mapped.request_id == "rid"
        assert mapped.has_next_page is True
        # list of mixed items mapped recursively
        assert isinstance(mapped.data[0], Subnet)
        assert mapped.data[1] == {"k": "v"}
        assert mapped.data[2] == 1 and mapped.data[3] == "x"

    @pytest.mark.parametrize(
        "func",
        [
            map_vcn,
            map_subnet,
            map_security_list,
            map_network_security_group,
            map_vnic,
            map_icmp_options,
            map_tcp_options,
            map_udp_options,
            map_egress_security_rule,
            map_ingress_security_rule,
            map_request,
            map_response,
        ],
    )
    def test_map_functions_handle_none(self, func):
        assert func(None) is None
