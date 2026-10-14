"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import importlib
import unittest
from unittest.mock import patch

from fastmcp import Client
from fastmcp.exceptions import ToolError
from jsonschema import Draft202012Validator


class TestNullInputs(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        from oracle.mysql_mcp_server import utils

        with patch.object(utils, "load_mysql_config", side_effect=RuntimeError("Offline test")), \
                patch.object(utils, "OciInfo", side_effect=RuntimeError("Offline test")):
            cls.server = importlib.import_module("oracle.mysql_mcp_server.server")

    async def test_null_defaults_are_accepted_by_advertised_schemas(self):
        async with Client(self.server.mcp) as client:
            for tool in await client.list_tools():
                validator = Draft202012Validator(tool.inputSchema)
                for name, schema in tool.inputSchema["properties"].items():
                    if "default" in schema and schema["default"] is None:
                        self.assertTrue(validator.evolve(schema=schema).is_valid(None), f"{tool.name}.{name}")

    async def test_optional_inputs(self):
        cases = [
            ("execute_sql_tool_by_connection_id", {"connection_id": "sample", "sql_script": "SELECT 1"},
             "params", [1]),
            ("object_storage_list_buckets", {}, "compartment_name", "sample"),
            ("object_storage_list_buckets", {}, "compartment_id", "sample"),
        ]
        with patch.object(self.server, "_get_db_connection", side_effect=RuntimeError("Offline test")), \
                patch.object(self.server, "oci_error_msg", '{"error": "Offline test"}'):
            async with Client(self.server.mcp) as client:
                for name, required, parameter, valid in cases:
                    with self.subTest(tool=name, parameter=parameter):
                        omitted = await client.call_tool(name, required)
                        for value in (None, valid):
                            result = await client.call_tool(name, {**required, parameter: value})
                            self.assertEqual(result.content, omitted.content)
                        with self.assertRaisesRegex(ToolError, "validation error"):
                            await client.call_tool(name, {**required, parameter: 7})
