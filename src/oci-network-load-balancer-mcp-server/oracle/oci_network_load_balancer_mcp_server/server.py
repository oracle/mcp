"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Literal, Optional

import oci
from fastmcp import FastMCP
from oracle.oci_network_load_balancer_mcp_server.models import (
    Backend,
    BackendSet,
    Listener,
    NetworkLoadBalancer,
    map_backend,
    map_backend_set,
    map_listener,
    map_network_load_balancer,
)
from pydantic import Field

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
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of network load balancers to return. If None, there is no limit.",
        ge=1,
    ),
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "UPDATING",
            "ACTIVE",
            "DELETING",
            "DELETED",
            "FAILED",
        ]
    ] = Field(
        None,
        description="The lifecycle state of the network load balancer to filter on",
    ),
) -> list[NetworkLoadBalancer]:
    nlbs: list[NetworkLoadBalancer] = []

    try:
        client = get_nlb_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(nlbs) < limit):
            kwargs = {
                "compartment_id": compartment_id,
                "page": next_page,
                "limit": limit,
            }

            if lifecycle_state is not None:
                kwargs["lifecycle_state"] = lifecycle_state

            response = client.list_network_load_balancers(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.network_load_balancer.models.NetworkLoadBalancer] = (
                response.data.items
            )
            for d in data:
                nlbs.append(map_network_load_balancer(d))

        logger.info(f"Found {len(nlbs)} Network Load Balancers")
        return nlbs

    except Exception as e:
        logger.error(f"Error in list_network_load_balancers tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_network_load_balancer", description="Get network load balancer details"
)
def get_network_load_balancer(
    network_load_balancer_id: str = Field(
        ..., description="The OCID of the network load balancer"
    )
):
    try:
        client = get_nlb_client()

        response: oci.response.Response = client.get_network_load_balancer(
            network_load_balancer_id
        )
        data: oci.network_load_balancer.models.NetworkLoadBalancer = response.data
        logger.info("Found Network Load Balancer")
        return map_network_load_balancer(data)

    except Exception as e:
        logger.error(f"Error in get_network_load_balancer tool: {str(e)}")
        raise e


@mcp.tool(
    name="list_network_load_balancer_listeners",
    description="Lists the listeners from the given network load balancer",
)
def list_listeners(
    network_load_balancer_id: str = Field(
        ..., description="The OCID of the network load balancer to list listeners from"
    ),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of listeners to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[Listener]:
    listeners: list[Listener] = []

    try:
        client = get_nlb_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(listeners) < limit):
            kwargs = {
                "network_load_balancer_id": network_load_balancer_id,
                "page": next_page,
                "limit": limit,
            }

            response = client.list_listeners(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.network_load_balancer.models.Listener] = response.data.items
            for d in data:
                listeners.append(map_listener(d))

        logger.info(f"Found {len(listeners)} Listeners")
        return listeners

    except Exception as e:
        logger.error(f"Error in list_network_load_balancer_listeners tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_network_load_balancer_listener",
    description="Gets the listener with the given listener name"
    "from the given network load balancer",
)
def get_listener(
    network_load_balancer_id: str = Field(
        ...,
        description="The OCID of the network load balancer to get the listener from",
    ),
    listener_name: str = Field(..., description="The name of the listener"),
):
    try:
        client = get_nlb_client()

        response: oci.response.Response = client.get_listener(
            network_load_balancer_id, listener_name
        )
        data: oci.network_load_balancer.models.Listener = response.data
        logger.info("Found Listener")
        return map_listener(data)

    except Exception as e:
        logger.error(f"Error in get_network_load_balancer_listener tool: {str(e)}")
        raise e


@mcp.tool(
    name="list_network_load_balancer_backend_sets",
    description="Lists the backend sets from the given network load balancer",
)
def list_backend_sets(
    network_load_balancer_id: str = Field(
        ...,
        description="The OCID of the network load balancer to list backend sets from",
    ),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of backend sets to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[BackendSet]:
    backend_sets: list[BackendSet] = []

    try:
        client = get_nlb_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(backend_sets) < limit):
            kwargs = {
                "network_load_balancer_id": network_load_balancer_id,
                "page": next_page,
                "limit": limit,
            }

            response = client.list_backend_sets(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.network_load_balancer.models.BackendSet] = (
                response.data.items
            )
            for d in data:
                backend_sets.append(map_backend_set(d))

        logger.info(f"Found {len(backend_sets)} Backend Sets")
        return backend_sets

    except Exception as e:
        logger.error(f"Error in list_network_load_balancer_backend_sets tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_network_load_balancer_backend_set",
    description="Gets the backend set with the given backend set name"
    "from the given network load balancer",
)
def get_backend_set(
    network_load_balancer_id: str = Field(
        ...,
        description="The OCID of the network load balancer to get the backend set from",
    ),
    backend_set_name: str = Field(..., description="The name of the backend set"),
):
    try:
        client = get_nlb_client()

        response: oci.response.Response = client.get_backend_set(
            network_load_balancer_id, backend_set_name
        )
        data: oci.network_load_balancer.models.BackendSet = response.data
        logger.info("Found Backend Set")
        return map_backend_set(data)

    except Exception as e:
        logger.error(f"Error in get_network_load_balancer_backend_set tool: {str(e)}")
        raise e


@mcp.tool(
    name="list_network_load_balancer_backends",
    description="Lists the backends from the given backend set and network load balancer",
)
def list_backends(
    network_load_balancer_id: str = Field(
        ...,
        description="The OCID of the network load balancer to list the backends from",
    ),
    backend_set_name: str = Field(
        ..., description="The name of the backend set to list the backends from"
    ),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of backends to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[Backend]:
    backends: list[Backend] = []

    try:
        client = get_nlb_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(backends) < limit):
            kwargs = {
                "network_load_balancer_id": network_load_balancer_id,
                "backend_set_name": backend_set_name,
                "page": next_page,
                "limit": limit,
            }

            response = client.list_backends(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.network_load_balancer.models.Backend] = response.data.items
            for d in data:
                backends.append(map_backend(d))

        logger.info(f"Found {len(backends)} Backends")
        return backends

    except Exception as e:
        logger.error(f"Error in list_network_load_balancer_backends tool: {str(e)}")
        raise e


@mcp.tool(
    name="get_network_load_balancer_backend",
    description="Gets the backend with the given backend name"
    "from the given backend set and network load balancer",
)
def get_backend(
    network_load_balancer_id: str = Field(
        ..., description="The OCID of the network load balancer to get the backend from"
    ),
    backend_set_name: str = Field(
        ..., description="The name of the backend set to get the backend from"
    ),
    backend_name: str = Field(..., description="The name of the backend"),
):
    try:
        client = get_nlb_client()

        response: oci.response.Response = client.get_backend(
            network_load_balancer_id, backend_set_name, backend_name
        )
        data: oci.network_load_balancer.models.Backend = response.data
        logger.info("Found Backend")
        return map_backend(data)

    except Exception as e:
        logger.error(f"Error in get_network_load_balancer_backend tool: {str(e)}")
        raise e


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
