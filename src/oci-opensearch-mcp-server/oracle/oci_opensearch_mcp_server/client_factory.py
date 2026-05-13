"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
import logging
from typing import Any

import oci

from . import __project__, __version__

logger = logging.getLogger(__name__)


def get_config() -> dict[str, Any]:
    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    return config


def build_signer(config: dict[str, Any]) -> Any:
    token_file = os.path.expanduser(config.get("security_token_file", "") or "")

    if token_file and os.path.exists(token_file):
        try:
            with open(token_file, "r", encoding="utf-8") as token_handle:
                token = token_handle.read().strip()
            if token:
                private_key = oci.signer.load_private_key_from_file(
                    config["key_file"],
                    pass_phrase=config.get("pass_phrase"),
                )
                logger.info("Using SecurityTokenSigner for OpenSearch client")
                return oci.auth.signers.SecurityTokenSigner(token, private_key)
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning(
                "Failed to build SecurityTokenSigner from security_token_file, falling back to API key signer: %s",
                exc,
            )

    logger.info("Using API key Signer for OpenSearch client")
    return oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config["key_file"],
        pass_phrase=config.get("pass_phrase"),
    )


def get_opensearch_cluster_client() -> oci.opensearch.OpensearchClusterClient:
    config = get_config()
    signer = build_signer(config)
    return oci.opensearch.OpensearchClusterClient(config, signer=signer)
