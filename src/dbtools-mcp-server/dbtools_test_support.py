"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
import runpy
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import Mock, patch

from requests import Response

SERVER_PATH = Path(__file__).with_name("dbtools-mcp-server.py")
DBTOOLS_ENDPOINT = "https://dbtools.example.invalid"
SQL_ENDPOINT = "https://sql.dbtools.example.invalid/ords/conn-example/_/sql"


def mock_oci_initialization(stack):
    """Provide isolated settings and replace the SDK/HTTP boundaries before script load."""
    stack.enter_context(
        patch.dict(
            os.environ,
            {
                "PROFILE_NAME": "TEST",
                "TENANCY_ID_OVERRIDE": "tenancy-example",
                "MODEL_NAME": "EXAMPLE_MODEL",
                "MODEL_EMBEDDING_DIMENSION": "384",
                "FASTMCP_SHOW_SERVER_BANNER": "false",
            },
        )
    )
    config = dict.fromkeys(("tenancy", "user", "fingerprint", "key_file", "pass_phrase"), "<redacted>")
    stack.enter_context(patch("oci.config.from_file", return_value=config))
    for target in (
        "oci.identity.IdentityClient",
        "oci.resource_search.ResourceSearchClient",
        "oci.database.DatabaseClient",
        "oci.database_tools.DatabaseToolsClient",
        "oci.vault.VaultsClient",
        "oci.secrets.SecretsClient",
        "oci.object_storage.ObjectStorageClient",
        "oci.signer.Signer",
    ):
        stack.enter_context(patch(target, autospec=True))
    from oci.database_tools import DatabaseToolsClient

    DatabaseToolsClient.return_value.base_client = Mock(_endpoint=DBTOOLS_ENDPOINT)
    stack.enter_context(
        patch("requests.Session.send", side_effect=AssertionError("Unexpected network request"))
    )


def sql_response(text, status=200, **headers):
    response = Response()
    response.status_code = status
    response.encoding = "utf-8"
    response._content = text.encode("utf-8")
    response.headers.update(headers)
    return response


if __name__ == "__main__":
    with ExitStack() as stack:
        mock_oci_initialization(stack)
        runpy.run_path(str(SERVER_PATH), run_name="__main__")
