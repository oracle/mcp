"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import configparser
import os
import tempfile
from logging import Logger
from pathlib import Path
from typing import Annotated, List

import oci
from fastmcp import FastMCP
from fastmcp.server.auth.providers.oci import OCIProvider
from fastmcp.server.dependencies import get_access_token
from fastmcp.utilities.auth import parse_scopes
from oracle.oci_object_storage_mcp_server.models import (
    Bucket,
    BucketSummary,
    ListObjects,
    ObjectSummary,
    ObjectVersionCollection,
    map_bucket,
    map_bucket_summary,
    map_object_summary,
    map_object_version_summary,
)

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)

_SENSITIVE_UPLOAD_PREFIXES = (
    Path.home() / ".oci",
    Path.home() / ".ssh",
    Path("/etc"),
    Path("/run/secrets"),
    Path("/var/run/secrets"),
)


def _path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _get_upload_root() -> Path:
    root = os.getenv("OCI_MCP_UPLOAD_ROOT")
    if root:
        return Path(root).expanduser().resolve()
    return (Path(tempfile.gettempdir()) / "oci-mcp-uploads").resolve()


def _resolve_upload_path(file_path: str) -> Path:
    upload_root = _get_upload_root()
    resolved_path = Path(file_path).expanduser().resolve(strict=True)
    if not _path_is_relative_to(resolved_path, upload_root):
        raise ValueError(
            f"Rejected upload path '{file_path}': resolved path is outside configured upload root '{upload_root}'."
        )
    for prefix in _SENSITIVE_UPLOAD_PREFIXES:
        resolved_prefix = prefix.expanduser().resolve(strict=False)
        if resolved_path == resolved_prefix or _path_is_relative_to(resolved_path, resolved_prefix):
            raise ValueError(f"Rejected upload path '{file_path}': path is in a sensitive location.")
    if not resolved_path.is_file():
        raise ValueError(f"Rejected upload path '{file_path}': path is not a regular file.")
    return resolved_path


def _get_http_config_and_signer():
    if not (os.getenv("ORACLE_MCP_HOST") and os.getenv("ORACLE_MCP_PORT")):
        return None, None
    token = get_access_token()
    if token is None:
        raise RuntimeError("HTTP requests require an authenticated IDCS access token.")
    domain = os.getenv("IDCS_DOMAIN")
    client_id = os.getenv("IDCS_CLIENT_ID")
    client_secret = os.getenv("IDCS_CLIENT_SECRET")
    if not all((domain, client_id, client_secret)):
        raise RuntimeError(
            "HTTP requests require IDCS authentication. Set IDCS_DOMAIN, IDCS_CLIENT_ID, and IDCS_CLIENT_SECRET."
        )
    region = os.getenv("OCI_REGION")
    if not region:
        raise RuntimeError("HTTP requests require OCI_REGION.")
    config = {"region": region}
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    return config, oci.auth.signers.TokenExchangeSigner(
        token.token,
        f"https://{domain}",
        client_id,
        client_secret,
        region=config.get("region"),
    )

def _get_oci_client_kwargs(signer=None):
    kwargs = {
        "circuit_breaker_strategy": oci.circuit_breaker.CircuitBreakerStrategy(
            failure_threshold=int(os.getenv("OCI_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "10")),
            recovery_timeout=int(os.getenv("OCI_CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30")),
        ),
        "circuit_breaker_callback": lambda exc: logger.warning(
            "Circuit breaker triggered: %s", exc
        ),
    }
    if signer is not None:
        kwargs["signer"] = signer
    return kwargs


_SESSION_TOKEN_DOCS = "https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm"
_API_KEY_FIELDS = ("tenancy", "user", "fingerprint", "key_file")

# configparser reserves "DEFAULT" as the section whose keys are inherited by every
# other section. Naming a section that cannot appear in an OCI config disables that.
_NO_INHERIT = "\x00oci-mcp-no-inherited-defaults"

_api_key_warning_emitted = False


def _selected_profile():
    return os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)


def _profile_declares_session_token():
    """Whether the selected profile declares security_token_file in its own section.

    oci.config.from_file() merges the [DEFAULT] section into every named profile, so
    `"security_token_file" in config` is true for an API-key profile whenever [DEFAULT]
    happens to be a session profile -- which would sign requests with the wrong
    credentials. Re-read the file with that inheritance disabled.
    """
    parser = configparser.ConfigParser(default_section=_NO_INHERIT)
    parser.read(os.path.expanduser(os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION)))
    profile = _selected_profile()
    if not parser.has_section(profile):
        return False
    return parser.has_option(profile, "security_token_file")


def _build_signer(config):
    """Build a request signer matching the selected profile's authentication type."""
    global _api_key_warning_emitted

    if _profile_declares_session_token():
        private_key = oci.signer.load_private_key_from_file(config["key_file"])
        with open(os.path.expanduser(config["security_token_file"]), "r") as f:
            token = f.read()
        return oci.auth.signers.SecurityTokenSigner(token, private_key)

    profile = _selected_profile()
    missing = [field for field in _API_KEY_FIELDS if not config.get(field)]
    if missing:
        raise RuntimeError(
            f"OCI profile [{profile}] cannot authenticate: it declares no "
            f"security_token_file, and these API key fields are missing: "
            f"{', '.join(missing)}. Either run 'oci session authenticate' to create a "
            f"session-token profile, or add the missing fields. See {_SESSION_TOKEN_DOCS}"
        )

    if not _api_key_warning_emitted:
        _api_key_warning_emitted = True
        logger.warning(
            f"OCI profile [{profile}] authenticates with a long-lived API key. Session "
            f"tokens expire automatically and limit the damage from a leaked credential; "
            f"prefer 'oci session authenticate' where your tenancy supports it. "
            f"See {_SESSION_TOKEN_DOCS}"
        )

    return oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config["key_file"],
        pass_phrase=config.get("pass_phrase"),
    )


def get_object_storage_client():
    config, signer = _get_http_config_and_signer()
    if signer is not None:
        return oci.object_storage.ObjectStorageClient(config, **_get_oci_client_kwargs(signer))
    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    signer = _build_signer(config)
    return oci.object_storage.ObjectStorageClient(config, **_get_oci_client_kwargs(signer))


# Object storage namespace
def get_object_storage_namespace(compartment_id: str):
    object_storage_client = get_object_storage_client()
    namespace = object_storage_client.get_namespace(compartment_id=compartment_id)
    return namespace.data


@mcp.tool(description="Get the object storage namespace for the tenancy")
def get_namespace(
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
):
    return get_object_storage_namespace(compartment_id)


# Buckets
@mcp.tool(description="List object storage buckets")
def list_buckets(
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
) -> List[BucketSummary]:
    object_storage_client = get_object_storage_client()
    namespace_name = get_object_storage_namespace(compartment_id)
    buckets = object_storage_client.list_buckets(namespace_name, compartment_id).data
    return [map_bucket_summary(bucket) for bucket in buckets]


@mcp.tool(description="Get details for a specific object storage bucket")
def get_bucket_details(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
) -> Bucket:
    object_storage_client = get_object_storage_client()
    namespace_name = get_object_storage_namespace(compartment_id)
    bucket_details = object_storage_client.get_bucket(
        namespace_name,
        bucket_name,
        fields=[
            "approximateSize",
            "approximateCount",
            "autoTiering",
        ],
    ).data

    return map_bucket(bucket_details)


# Objects
@mcp.tool(description="List objects in a given object storage bucket")
def list_objects(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    prefix: Annotated[str, "Optional prefix to filter objects"] = "",
) -> ListObjects:
    object_storage_client = get_object_storage_client()
    namespace_name = get_object_storage_namespace(compartment_id)
    list_objects = object_storage_client.list_objects(
        namespace_name,
        bucket_name,
        prefix=prefix,
        fields="name,size,timeModified,archivalState,storageTier",
    ).data

    objects = [map_object_summary(obj) for obj in list_objects.objects]
    prefixes = list_objects.prefixes if list_objects.prefixes else []
    return ListObjects(objects=objects, prefixes=prefixes)


@mcp.tool(description="List object versions in a given object storage bucket")
def list_object_versions(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    prefix: Annotated[str, "Optional prefix to filter object versions"] = "",
) -> ObjectVersionCollection:
    object_storage_client = get_object_storage_client()
    namespace_name = get_object_storage_namespace(compartment_id)
    list_object_versions = object_storage_client.list_object_versions(
        namespace_name,
        bucket_name,
        prefix=prefix,
        limit=25,
        fields="timeModified",
    ).data

    versioned_objects = [map_object_version_summary(obj) for obj in list_object_versions.items]
    prefixes = list_object_versions.prefixes if list_object_versions.prefixes else []
    return ObjectVersionCollection(items=versioned_objects, prefixes=prefixes)


@mcp.tool(description="Get a specific object from an object storage bucket")
def get_object(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    object_name: Annotated[str, "The name of the object"],
    version_id: Annotated[str, "Optional version ID of the object"] = "",
) -> ObjectSummary:
    object_storage_client = get_object_storage_client()
    namespace_name = get_object_storage_namespace(compartment_id)
    obj = object_storage_client.get_object(
        namespace_name,
        bucket_name,
        object_name,
        version_id=version_id,
    ).data

    return map_object_summary(obj)


@mcp.tool(description="Upload an object to an object storage bucket")
def upload_object(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    file_path: Annotated[str, "The path to the file to upload"],
    object_name: Annotated[
        str,
        "Optional name of the object to upload"
        "If the object name is not provided, use the file name as the object name",
    ] = "",
):
    try:
        resolved_file_path = _resolve_upload_path(file_path)
    except Exception as e:
        logger.warning("Rejected upload path %s: %s", file_path, e)
        return {"error": str(e)}

    object_storage_client = get_object_storage_client()
    namespace_name = get_object_storage_namespace(compartment_id)
    logger.info("Got Namespace: %s", namespace_name)
    logger.info("Checking file at path: %s", resolved_file_path)
    object_name = object_name or resolved_file_path.name
    try:
        with open(resolved_file_path, "rb") as file:
            object_storage_client.put_object(namespace_name, bucket_name, object_name, file)
        return {"message": "Object uploaded successfully"}
    except Exception as e:
        return {"error": str(e)}


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if not (host and port):
        mcp.run()
        return
    domain = os.getenv("IDCS_DOMAIN")
    client_id = os.getenv("IDCS_CLIENT_ID")
    client_secret = os.getenv("IDCS_CLIENT_SECRET")
    base_url = os.getenv("ORACLE_MCP_BASE_URL", "")
    audience = os.getenv("IDCS_AUDIENCE")
    if not all((domain, client_id, client_secret, audience, base_url)):
        raise RuntimeError(
            "HTTP transport requires IDCS authentication. "
            "Set IDCS_DOMAIN, IDCS_CLIENT_ID, IDCS_CLIENT_SECRET, IDCS_AUDIENCE, "
            "ORACLE_MCP_BASE_URL, ORACLE_MCP_HOST, and ORACLE_MCP_PORT."
        )
    mcp.auth = OCIProvider(
        config_url=f"https://{domain}/.well-known/openid-configuration",
        client_id=client_id,
        client_secret=client_secret,
        audience=audience,
        required_scopes=parse_scopes(os.getenv("IDCS_REQUIRED_SCOPES")) or f"openid profile email oci_mcp.{__project__.removeprefix('oracle.oci-').removesuffix('-mcp-server').replace('-', '_')}.invoke".split(),
        base_url=base_url,
    )
    mcp.run(transport="http", host=host, port=int(port))


if __name__ == "__main__":
    main()
