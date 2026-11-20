"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import contextlib
import importlib.util
import io
import json
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch


class TestStdioOutput(unittest.TestCase):
    """Over stdio, stdout carries JSON-RPC, so tools must not print to it."""

    @classmethod
    def setUpClass(cls):
        # The script creates OCI clients at import; keep those external boundaries offline.
        config = dict.fromkeys(("tenancy", "user", "fingerprint", "key_file", "pass_phrase"), "sample")
        with ExitStack() as stack:
            stack.enter_context(patch("oci.config.from_file", return_value=config))
            for target in (
                "oci.identity.IdentityClient", "oci.resource_search.ResourceSearchClient",
                "oci.database.DatabaseClient", "oci.database_tools.DatabaseToolsClient",
                "oci.vault.VaultsClient", "oci.secrets.SecretsClient",
                "oci.object_storage.ObjectStorageClient", "oci.signer.Signer",
            ):
                stack.enter_context(patch(target))
            spec = importlib.util.spec_from_file_location(
                "dbtools_stdio_output", Path(__file__).with_name("dbtools-mcp-server.py")
            )
            cls.server = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = cls.server
            spec.loader.exec_module(cls.server)

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop("dbtools_stdio_output", None)

    def test_ragify_column_writes_nothing_to_stdout(self):
        responses = [
            json.dumps({"items": [{"errorCode": 0}]}),
            json.dumps({"items": [{"errorCode": 1, "errorMessage": "sample"}]}),
            "not json",
        ]
        for response in responses:
            with self.subTest(response=response):
                stdout = io.StringIO()
                with patch.object(self.server, "execute_sql_tool", return_value=response), \
                        contextlib.redirect_stdout(stdout):
                    self.server.ragify_column("sample", "DOCS", ["BODY"], "BODY_VEC")
                self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
