"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import importlib.util
import json
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from fastmcp.exceptions import ToolError
from jsonschema import Draft202012Validator
from mcp.types import TextContent

from dbtools_test_support import SERVER_PATH, mock_oci_initialization


class TestNullInputs(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        with ExitStack() as stack:
            mock_oci_initialization(stack)
            spec = importlib.util.spec_from_file_location("dbtools_null_inputs", SERVER_PATH)
            cls.server = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = cls.server
            cls.addClassCleanup(sys.modules.pop, spec.name)
            spec.loader.exec_module(cls.server)

    async def test_null_defaults_are_accepted_by_advertised_schemas(self):
        async with Client(self.server.mcp) as client:
            checked = set()
            for tool in await client.list_tools():
                validator = Draft202012Validator(tool.input_schema)
                for name, schema in tool.input_schema["properties"].items():
                    if "default" in schema and schema["default"] is None:
                        checked.add((tool.name, name))
                        self.assertTrue(validator.evolve(schema=schema).is_valid(None), f"{tool.name}.{name}")
            self.assertEqual(
                checked,
                {
                    ("create_report", "description"),
                    ("create_report", "bind_parameters"),
                    ("execute_report", "bind_values"),
                },
            )

    async def test_optional_report_inputs(self):
        create_args = {"dbtools_connection_display_name": "sample", "name": "sample", "sql_query": "SELECT 1"}
        execute_args = {"dbtools_connection_display_name": "sample", "report_name": "sample"}
        cases = [
            ("create_report", create_args, "description", "Sample report"),
            ("create_report", create_args, "bind_parameters", ["id"]),
            ("execute_report", execute_args, "bind_values", {"id": 1}),
        ]
        search_result = SimpleNamespace(data=SimpleNamespace(items=[]))
        with patch.object(self.server.search_client, "search_resources", return_value=search_result):
            async with Client(self.server.mcp) as client:
                for name, required, parameter, valid in cases:
                    with self.subTest(tool=name, parameter=parameter):
                        omitted = await client.call_tool(name, required)
                        self.assertEqual(
                            json.loads(omitted.content[0].text)["error"],
                            "No connection found with exact name 'sample'",
                        )
                        for value in (None, valid):
                            result = await client.call_tool(name, {**required, parameter: value})
                            self.assertEqual(result.content, omitted.content)
                        with self.assertRaisesRegex(ToolError, "validation error"):
                            await client.call_tool(name, {**required, parameter: 7})


class TestStdio(unittest.IsolatedAsyncioTestCase):
    async def test_script_advertises_tools_and_returns_text_json_over_stdio(self):
        transport = StdioTransport(
            command=sys.executable,
            args=[str(Path(__file__).with_name("dbtools_test_support.py"))],
            keep_alive=False,
        )
        async with Client(transport, timeout=30) as client:
            tools = {tool.name: tool for tool in await client.list_tools()}
            self.assertEqual(
                set(tools),
                {
                    "bootstrap_reports",
                    "create_report",
                    "delete_report",
                    "execute_report",
                    "execute_sql_tool",
                    "find_matching_reports",
                    "get_compartment_by_name_tool",
                    "get_dbtools_connection_by_name_tool",
                    "get_report",
                    "get_table_info",
                    "heatwave_ask_help",
                    "heatwave_ask_ml_rag",
                    "heatwave_ask_nl_sql",
                    "heatwave_load_vector_store",
                    "heatwave_retrieve_relevant_schema_information",
                    "list_all_compartments",
                    "list_all_connections",
                    "list_all_databases",
                    "list_autonomous_databases",
                    "list_dbtools_connection_tool",
                    "list_reports",
                    "list_tables",
                    "object_storage_list_buckets",
                    "object_storage_list_objects",
                    "ragify_column",
                },
            )
            self.assertEqual(
                tools["execute_sql_tool"].input_schema["required"],
                [
                    "dbtools_connection_display_name",
                    "sql_script",
                ],
            )
            result = await client.call_tool("get_dbtools_connection_by_name_tool", {"display_name": ""})
            self.assertEqual(len(result.content), 1)
            self.assertIsInstance(result.content[0], TextContent)
            self.assertEqual(json.loads(result.content[0].text)["error"], "Invalid connection name filter")
