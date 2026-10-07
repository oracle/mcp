"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import importlib.util
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from fastmcp import Client
from fastmcp.exceptions import ToolError
from jsonschema import Draft202012Validator


class TestNullInputs(unittest.IsolatedAsyncioTestCase):
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
                "dbtools_null_inputs", Path(__file__).with_name("dbtools-mcp-server.py")
            )
            cls.server = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = cls.server
            spec.loader.exec_module(cls.server)

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop("dbtools_null_inputs", None)

    async def test_null_defaults_are_accepted_by_advertised_schemas(self):
        async with Client(self.server.mcp) as client:
            for tool in await client.list_tools():
                validator = Draft202012Validator(tool.inputSchema)
                for name, schema in tool.inputSchema["properties"].items():
                    if "default" in schema and schema["default"] is None:
                        self.assertTrue(validator.evolve(schema=schema).is_valid(None), f"{tool.name}.{name}")

    async def test_optional_report_inputs(self):
        cases = [
            ("create_report", {"dbtools_connection_display_name": "sample", "name": "sample",
                               "sql_query": "SELECT 1"}, "description", "Sample report"),
            ("create_report", {"dbtools_connection_display_name": "sample", "name": "sample",
                               "sql_query": "SELECT 1"}, "bind_parameters", ["id"]),
            ("execute_report", {"dbtools_connection_display_name": "sample", "report_name": "sample"},
             "bind_values", {"id": 1}),
        ]
        with patch.object(self.server, "_resolve_connection_or_error", return_value=(None, '{"error": "Offline test"}')):
            async with Client(self.server.mcp) as client:
                for name, required, parameter, valid in cases:
                    with self.subTest(tool=name, parameter=parameter):
                        omitted = await client.call_tool(name, required)
                        for value in (None, valid):
                            result = await client.call_tool(name, {**required, parameter: value})
                            self.assertEqual(result.content, omitted.content)
                        with self.assertRaisesRegex(ToolError, "validation error"):
                            await client.call_tool(name, {**required, parameter: 7})
