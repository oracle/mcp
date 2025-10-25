"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Annotated

import oci
from fastmcp import FastMCP

from . import __project__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_nlb_client():
    logger.info("entering get_nlb_client")
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )

    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    token = None
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.network_load_balancer.NetworkLoadBalancerClient(config, signer=signer)


@mcp.tool(
    name="list_network_load_balancers",
    description="Lists the network load balancers from the given compartment",
)
def list_network_load_balancers(
    compartment_id: Annotated[str, "compartment ocid"],
) -> list[dict]:
    nlb_client = get_nlb_client()
    nlbs = nlb_client.list_network_load_balancers(compartment_id).data.items
    return [
        {
            "nlb_id": nlb.id,
            "display_name": nlb.display_name,
            "lifecycle_state": nlb.lifecycle_state,
            "public_ips": [ip.ip_address for ip in nlb.ip_addresses if ip.is_public],
            "private_ips": [
                ip.ip_address for ip in nlb.ip_addresses if not ip.is_public
            ],
        }
        for nlb in nlbs
    ]


@mcp.tool(
    name="get_network_load_balancer", description="Get network load balancer details"
)
def get_network_load_balancer(network_load_balancer_id: Annotated[str, "nlb id"]):
    nlb_client = get_nlb_client()
    return nlb_client.get_network_load_balancer(network_load_balancer_id).data


@mcp.tool(name="list_network_load_balancer_listeners")
def list_listeners(network_load_balancer_id: str) -> list[dict]:
    """Lists the listeners from the given network load balancer"""
    nlb_client = get_nlb_client()
    listeners = nlb_client.list_listeners(network_load_balancer_id).data.items
    return [
        {
            "name": listener.name,
            "ip_version": listener.ip_version,
            "protocol": listener.protocol,
            "port": listener.port,
            "is_ppv2_enabled": listener.is_ppv2_enabled,
        }
        for listener in listeners
    ]


@mcp.tool(name="get_network_load_balancer_listener")
def get_listener(
    network_load_balancer_id: str,
    listener_name: str,
):
    """Gets the listener with the given listener name
    from the given network load balancer"""
    nlb_client = get_nlb_client()
    return nlb_client.get_listener(network_load_balancer_id, listener_name).data


@mcp.tool(name="list_network_load_balancer_backend_sets")
def list_backend_sets(network_load_balancer_id: str) -> list[dict]:
    """Lists the backend sets from the given network load balancer"""
    nlb_client = get_nlb_client()
    backend_sets = nlb_client.list_backend_sets(network_load_balancer_id).data.items
    return [
        {
            "name": backend_set.name,
            "ip_version": backend_set.ip_version,
            "is_preemptive": backend_set.are_operationally_active_backends_preferred,
            "load_balancing_policy": backend_set.policy,
            "number_of_backends": len(backend_set.backends),
        }
        for backend_set in backend_sets
    ]


@mcp.tool(name="get_network_load_balancer_backend_set")
def get_backend_set(
    network_load_balancer_id: str,
    backend_set_name: str,
):
    """Gets the backend set with the given backend set name
    from the given network load balancer"""
    nlb_client = get_nlb_client()
    return nlb_client.get_backend_set(network_load_balancer_id, backend_set_name).data


@mcp.tool(name="list_network_load_balancer_backends")
def list_backends(
    network_load_balancer_id: str,
    backend_set_name: str,
) -> list[dict]:
    """Lists the backends from the given backend set and network load balancer"""
    nlb_client = get_nlb_client()
    backends = nlb_client.list_backends(
        network_load_balancer_id, backend_set_name
    ).data.items
    return [
        {
            "name": backend.name,
            "ip_address": backend.ip_address,
            "port": backend.port,
            "weight": backend.weight,
            "is_drain": backend.is_drain,
            "is_backup": backend.is_backup,
            "is_offline": backend.is_offline,
        }
        for backend in backends
    ]


@mcp.tool(name="get_network_load_balancer_backend")
def get_backend(
    network_load_balancer_id: str,
    backend_set_name: str,
    backend_name: str,
):
    """Gets the backend with the given backend name
    from the given backend set and network load balancer"""
    nlb_client = get_nlb_client()
    return nlb_client.get_backend(
        network_load_balancer_id, backend_set_name, backend_name
    ).data


def main():
    mcp.run()


if __name__ == "__main__":
    main()
