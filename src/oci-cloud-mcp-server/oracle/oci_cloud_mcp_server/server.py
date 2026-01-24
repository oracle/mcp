"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import inspect
import json
import os
from importlib import import_module
from logging import Logger
from typing import Annotated, Any, Callable, Dict, List, Optional, Tuple

import oci
from fastmcp import FastMCP

from . import __project__, __version__
from .utils import initAuditLogger

logger = Logger(__name__, level="INFO")

initAuditLogger(logger)

mcp = FastMCP(
    name=__project__,
    instructions="""
        This server provides tools to interact directly with the OCI Python SDK,
        invoking API clients and operations in-process (no CLI).
        - invoke_oci_api: Call any OCI SDK client operation by FQN and method.
        - list_client_operations: Discover available operations on a client.
    """,
)

_user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
_ADDITIONAL_UA = f"{_user_agent_name}/{__version__}"


def _get_config_and_signer() -> Tuple[Dict[str, Any], Any]:
    """
    Load OCI config and build an appropriate signer.

    Preference order:
    - If a security_token_file exists, use SecurityTokenSigner (session auth).
    - Otherwise, fall back to API key Signer from config.
    """
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    config["additional_user_agent"] = _ADDITIONAL_UA

    # try security token
    token_file = os.path.expanduser(config.get("security_token_file", "") or "")
    try:
        private_key = oci.signer.load_private_key_from_file(config["key_file"])
    except Exception as e:
        logger.error(f"Failed loading private key: {e}")
        raise

    signer = None
    if token_file and os.path.exists(token_file):
        try:
            with open(token_file, "r") as f:
                token = f.read()
            signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
            logger.info("Using SecurityTokenSigner from security_token_file.")
        except Exception as e:
            logger.warning(
                f"Failed to build SecurityTokenSigner from token file, will try API key signer: {e}"
            )

    if signer is None:
        # fall back to API key signer
        try:
            signer = oci.signer.Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config["key_file"],
                pass_phrase=config.get("pass_phrase"),
            )
            logger.info("Using API key Signer.")
        except Exception as e:
            logger.error(f"Failed to build API key Signer: {e}")
            raise

    return config, signer


def _import_client(client_fqn: str) -> Any:
    """
    Import and instantiate an OCI SDK Client given a fully-qualified class name.
    Example: 'oci.core.ComputeClient'
    """
    if "." not in client_fqn:
        raise ValueError(
            "client_fqn must be a fully-qualified class name like 'oci.core.ComputeClient'"
        )
    module_name, class_name = client_fqn.rsplit(".", 1)
    module = import_module(module_name)
    cls = getattr(module, class_name)
    if not inspect.isclass(cls):
        raise ValueError(f"{client_fqn} is not a class")
    config, signer = _get_config_and_signer()
    instance = cls(config, signer=signer)
    return instance


def _serialize_oci_data(data: Any) -> Any:
    """
    Convert OCI SDK model objects or collections into JSON-serializable structures.
    """
    try:
        # oci.util.to_dict handles models and nested data structures
        return oci.util.to_dict(data)
    except Exception:
        # fall back to best-effort for non-OCI types
        if isinstance(data, (list, tuple)):
            return [_serialize_oci_data(x) for x in data]
        if isinstance(data, dict):
            return {k: _serialize_oci_data(v) for k, v in data.items()}
        try:
            json.dumps(data)
            return data
        except Exception:
            return str(data)


def _call_with_pagination_if_applicable(
    method: Callable[..., Any], params: Dict[str, Any], operation_name: str
) -> Tuple[Any, Optional[str]]:
    """
    If the operation appears to be a list operation, use the OCI paginator to get all results.
    Returns (data, opc_request_id).
    """
    # heuristic: use paginator for "list_*" operations
    if operation_name.startswith("list_"):
        logger.info(f"Using paginator for operation {operation_name}")
        response = oci.pagination.list_call_get_all_results(method, **params)
        # response is an oci.response.Response; .data usually list[Model]
        opc_request_id = None
        try:
            opc_request_id = response.headers.get("opc-request-id")
        except Exception:
            opc_request_id = None
        return response.data, opc_request_id

    # non-list operation; invoke directly
    response = method(**params)
    # most OCI SDK methods return oci.response.Response with .data and .headers
    if hasattr(response, "data"):
        data = response.data
    else:
        data = response
    opc_request_id = None
    try:
        opc_request_id = response.headers.get("opc-request-id")
    except Exception:
        opc_request_id = None
    return data, opc_request_id


@mcp.tool(description="Invoke an OCI Python SDK API via client and operation name.")
def invoke_oci_api(
    client_fqn: Annotated[
        str, "Fully-qualified client class, e.g. 'oci.core.ComputeClient'"
    ],
    operation: Annotated[
        str, "Client method/operation name, e.g. 'list_instances' or 'get_instance'"
    ],
    params: Annotated[
        Dict[str, Any],
        "Keyword arguments for the operation (JSON object). Use snake_case keys as in SDK.",
    ] = {},
) -> dict:
    """
    Example:
      client_fqn='oci.core.ComputeClient'
      operation='list_instances'
      params={'compartment_id': '<ocid>', 'availability_domain': '...'}
    """
    try:
        client = _import_client(client_fqn)
        if not hasattr(client, operation):
            raise AttributeError(
                f"Operation '{operation}' not found on client '{client_fqn}'"
            )

        method = getattr(client, operation)
        if not callable(method):
            raise AttributeError(
                f"Attribute '{operation}' on client '{client_fqn}' is not callable"
            )

        params = params or {}
        data, opc_request_id = _call_with_pagination_if_applicable(
            method, params, operation
        )

        result = {
            "client": client_fqn,
            "operation": operation,
            "params": params,
            "opc_request_id": opc_request_id,
            "data": _serialize_oci_data(data),
        }
        logger.info(
            f"invoke_oci_api success: client={client_fqn} op={operation} opc_request_id={opc_request_id}"
        )
        return result

    except Exception as e:
        logger.error(f"Error invoking OCI API {client_fqn}.{operation}: {e}")
        return {
            "client": client_fqn,
            "operation": operation,
            "params": params or {},
            "error": str(e),
        }


@mcp.tool(description="List public callable operations for a given OCI client class.")
def list_client_operations(
    client_fqn: Annotated[
        str, "Fully-qualified client class, e.g. 'oci.core.ComputeClient'"
    ],
) -> List[dict]:
    try:
        module_name, class_name = client_fqn.rsplit(".", 1)
        module = import_module(module_name)
        cls = getattr(module, class_name)
        if not inspect.isclass(cls):
            raise ValueError(f"{client_fqn} is not a class")

        ops: List[dict] = []
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name.startswith("_"):
                continue
            try:
                doc = (inspect.getdoc(member) or "").strip()
                first_line = doc.splitlines()[0] if doc else ""
                params = inspect.signature(member)
            except Exception:
                first_line = ""
            ops.append({"name": name, "summary": first_line, "params": str(params)})

        logger.info(f"Found {len(ops)} operations on {client_fqn}")
        return ops
    except Exception as e:
        logger.error(f"Error listing operations for {client_fqn}: {e}")
        raise


def main():
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
