"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import importlib.util
import io
import json
import os
import sys
import unittest
from contextlib import ExitStack, redirect_stdout
from unittest.mock import patch

import requests
from oci.identity.models import Compartment
from oci.resource_search.models import ResourceSummary, ResourceSummaryCollection
from oci.response import Response

from dbtools_test_support import SERVER_PATH, SQL_ENDPOINT, mock_oci_initialization, sql_response


def oci_response(data, **headers):
    return Response(status=200, headers=headers, data=data, request=None)


def connection(identifier="conn-example", name="Sample", db_type="ORACLE_DATABASE"):
    return ResourceSummary(
        identifier=identifier,
        display_name=name,
        compartment_id="compartment-example",
        lifecycle_state="ACTIVE",
        additional_details={"type": db_type},
    )


def search_response(*connections):
    return oci_response(ResourceSummaryCollection(items=list(connections)))


def ords_rows(*rows):
    return sql_response(json.dumps({"items": [{"resultSet": {"items": rows}}]}))


class TestDbtoolsOffline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ExitStack() as stack:
            mock_oci_initialization(stack)
            spec = importlib.util.spec_from_file_location("dbtools_offline", SERVER_PATH)
            cls.server = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = cls.server
            cls.addClassCleanup(sys.modules.pop, spec.name)
            spec.loader.exec_module(cls.server)

    def setUp(self):
        stack = self.enterContext(ExitStack())
        stack.enter_context(
            patch.dict(
                os.environ,
                {
                    "SQL_CONNECT_TIMEOUT_SEC": "5",
                    "SQL_READ_TIMEOUT_SEC": "60",
                    "SQL_HTTP_RETRIES": "2",
                },
            )
        )
        self.search = stack.enter_context(
            patch.object(
                self.server.search_client, "search_resources", return_value=search_response(connection())
            )
        )
        self.post = stack.enter_context(
            patch("requests.post", side_effect=AssertionError("Unexpected SQL request"))
        )
        self.sleep = stack.enter_context(patch.object(self.server.time, "sleep"))

    def sql_replies(self, *responses):
        self.post.reset_mock()
        self.post.side_effect = responses

    def sql_payload(self, call_index=-1):
        self.assertEqual(self.post.call_args_list[call_index].args, (SQL_ENDPOINT,))
        return self.post.call_args_list[call_index].kwargs["json"]

    def set_database_type(self, db_type):
        self.search.return_value = search_response(connection(db_type=db_type))

    def test_connection_search_selects_exact_name(self):
        self.search.return_value = search_response(connection(name="Sample backup"), connection())
        client = self.server.dbtools_client
        with patch.object(
            client, "get_database_tools_connection", return_value=oci_response("details")
        ) as get:
            self.assertEqual(self.server.get_dbtools_connection_by_name_tool("Sample"), "details")
        get.assert_called_once_with("conn-example")
        self.assertIn("where displayName =~ 'Sample'", self.search.call_args.kwargs["search_details"].query)

    def test_connection_errors_stop_sql_execution(self):
        for results, error in (
            (search_response(connection(name="Different")), "No connection found with exact name 'Sample'"),
            (
                search_response(connection(), connection(identifier="other")),
                "Ambiguous connection name 'Sample'",
            ),
        ):
            with self.subTest(error=error):
                self.search.return_value = results
                for lookup in (
                    self.server.get_dbtools_connection_by_name_tool,
                    lambda name: self.server.execute_sql_tool(name, "SELECT 1 FROM DUAL"),
                ):
                    result = json.loads(lookup("Sample"))
                    self.assertEqual(result["error"], error)
                    if "candidates" in result:
                        self.assertEqual(
                            [item["id"] for item in result["candidates"]], ["conn-example", "other"]
                        )
        self.search.side_effect = RuntimeError("search unavailable")
        self.assertEqual(
            json.loads(self.server.execute_sql_tool("Sample", "SELECT 1"))["error"],
            "Failed to resolve connection",
        )
        self.post.assert_not_called()

    def test_inventory_follows_compartment_pages_and_preserves_service_results(self):
        identity = self.server.identity_client
        first_page = Compartment(name="Development", id="dev")
        second_page = Compartment(name="Testing", id="test")
        root = Compartment(name="Root", id="tenancy-example")
        with (
            patch.object(
                identity,
                "list_compartments",
                side_effect=[
                    oci_response([first_page], **{"opc-next-page": "next"}),
                    oci_response([first_page], **{"opc-next-page": "next"}),
                    oci_response([second_page]),
                ],
            ) as compartments,
            patch.object(identity, "get_compartment", return_value=oci_response(root)),
        ):
            listed = json.loads(self.server.list_all_compartments())
            self.assertEqual([item["id"] for item in listed], ["dev", "tenancy-example"])
            self.assertEqual(json.loads(self.server.get_compartment_by_name_tool("testing"))["id"], "test")
        self.assertEqual(compartments.call_args.kwargs["page"], "next")
        self.assertEqual(compartments.call_args.kwargs["compartment_id"], "tenancy-example")

    def test_inventory_resolves_compartment_before_querying_service(self):
        identity = self.server.identity_client
        storage = self.server.object_storage_client
        with (
            patch.object(
                identity,
                "list_compartments",
                side_effect=lambda **_: oci_response([Compartment(name="Testing", id="test")]),
            ),
            patch.object(identity, "get_compartment", return_value=oci_response(Compartment(name="Root"))),
            patch.object(
                self.server.database_client,
                "list_autonomous_databases",
                return_value=oci_response(["test-db"]),
            ) as databases,
            patch.object(
                self.server.dbtools_client,
                "list_database_tools_connections",
                return_value=oci_response(["test-connection"]),
            ) as connections,
            patch.object(storage, "get_namespace", return_value=oci_response("test-namespace")),
            patch.object(storage, "list_buckets", return_value=oci_response(["sample-bucket"])) as buckets,
        ):
            for tool, service, expected in (
                (self.server.list_autonomous_databases, databases, "['test-db']"),
                (self.server.list_dbtools_connection_tool, connections, "['test-connection']"),
                (self.server.object_storage_list_buckets, buckets, "['sample-bucket']"),
            ):
                with self.subTest(tool=tool.__name__):
                    self.assertIn("not found", json.loads(tool("Missing"))["error"])
                    service.assert_not_called()
                    self.assertEqual(tool("testing"), expected)
                    self.assertEqual(service.call_args.kwargs["compartment_id"], "test")
            self.assertEqual(buckets.call_args.kwargs["namespace_name"], "test-namespace")
            self.assertIn(
                "not found", json.loads(self.server.get_compartment_by_name_tool("Missing"))["error"]
            )
            buckets.side_effect = RuntimeError("bucket access denied")
            self.assertIn(
                "bucket access denied",
                json.loads(self.server.object_storage_list_buckets("Testing"))["error"],
            )

    def test_list_databases_searches_across_database_types(self):
        self.search.return_value = oci_response(
            ResourceSummaryCollection(
                items=[ResourceSummary(identifier="database-example", resource_type="Database")]
            )
        )
        self.assertEqual(
            json.loads(self.server.list_all_databases())["items"][0]["identifier"], "database-example"
        )
        query = self.search.call_args.kwargs["search_details"].query
        self.assertIn("pluggabledatabase", query)
        self.assertIn("mysqldbsystem", query)

    def test_list_connections_reports_partial_lookup_failure(self):
        self.search.return_value = search_response(
            connection(), connection(identifier="denied", name="Restricted")
        )
        with patch.object(
            self.server.dbtools_client,
            "get_database_tools_connection",
            side_effect=[oci_response("Example connection"), RuntimeError("access denied")],
        ):
            result = self.server.list_all_connections()
        self.assertIn("Example connection", result)
        self.assertIn("Error getting details for connection Restricted: access denied", result)
        self.search.return_value = oci_response(None)
        self.assertEqual(json.loads(self.server.list_all_connections()), [])

    def test_list_objects_returns_objects_and_reports_access_failure(self):
        from oci.object_storage.models import ListObjects, ObjectSummary

        with patch.object(
            self.server.object_storage_client,
            "list_objects",
            side_effect=[
                oci_response(ListObjects(objects=[ObjectSummary(name="test.txt")])),
                RuntimeError("object access denied"),
            ],
        ) as list_objects:
            self.assertEqual(
                json.loads(self.server.object_storage_list_objects("namespace", "bucket"))[0]["name"],
                "test.txt",
            )
            list_objects.assert_called_once_with(namespace_name="namespace", bucket_name="bucket")
            self.assertIn(
                "object access denied",
                json.loads(self.server.object_storage_list_objects("namespace", "bucket"))["error"],
            )

    def test_read_only_sql_retries_timeout_and_transient_status(self):
        self.sql_replies(requests.exceptions.Timeout(), sql_response("", 503), ords_rows({"answer": 1}))
        statement = "-- header\n/* label */ SELECT 1 FROM DUAL;"
        result = json.loads(self.server.execute_sql_tool("Sample", statement))
        self.assertEqual(result["items"][0]["resultSet"]["items"], [{"answer": 1}])
        self.assertEqual(self.post.call_count, 3)
        self.assertEqual([call.args for call in self.sleep.call_args_list], [(1,), (2,)])
        for call_index in range(3):
            self.assertEqual(self.sql_payload(call_index), {"statementText": statement})
            kwargs = self.post.call_args_list[call_index].kwargs
            self.assertIs(kwargs["auth"], self.server.auth_signer)
            self.assertEqual(kwargs["timeout"], (5, 60))

    def test_mutating_and_multistatement_sql_return_timeout_without_retry(self):
        for statement in ("DELETE FROM sample_table", "SELECT 1 FROM DUAL; SELECT 2 FROM DUAL"):
            with self.subTest(statement=statement):
                self.sql_replies(requests.exceptions.Timeout())
                result = json.loads(self.server.execute_sql_tool("Sample", statement))
                self.assertEqual(result["error"], "SQL execution request timed out")
                self.assertEqual(
                    result["details"], {"connect_timeout_seconds": 5, "read_timeout_seconds": 60}
                )
                self.post.assert_called_once()
        self.sleep.assert_not_called()

    def test_sql_returns_http_diagnostics_without_server_response_body(self):
        self.sql_replies(sql_response("opaque service body", 403, **{"opc-request-id": "req-example"}))
        result = json.loads(self.server.execute_sql_tool("Sample", "SELECT 1 FROM DUAL"))
        self.assertEqual(
            result, {"error": "SQL execution HTTP error", "status_code": 403, "request_id": "req-example"}
        )
        self.post.assert_called_once()

    def test_sql_preserves_non_json_response_and_reports_transport_error(self):
        self.sql_replies(
            sql_response("plain response"), requests.exceptions.ConnectionError("connection closed")
        )
        self.assertEqual(self.server.execute_sql_tool("Sample", "SELECT 1"), "plain response")
        self.assertEqual(
            json.loads(self.server.execute_sql_tool("Sample", "SELECT 1")),
            {"error": "Error executing SQL: connection closed"},
        )

    def test_table_metadata_uses_binds_and_oracle_uppercase_fallback(self):
        column = {
            "column_name": "ID",
            "data_type": "NUMBER",
            "data_length": "22",
            "nullable": "N",
            "data_default": " 0 ",
            "comments": "Identifier",
            "is_primary_key": 1,
            "num_rows": 5,
        }
        self.sql_replies(ords_rows(), ords_rows(column))
        result = json.loads(self.server.get_table_info("Sample", "widgets"))
        self.assertEqual(
            result,
            {
                "table_name": "WIDGETS",
                "primary_key": ["ID"],
                "row_count": 5,
                "columns": [
                    {
                        "name": "ID",
                        "type": "NUMBER",
                        "length": 22,
                        "nullable": False,
                        "default": "0",
                        "comment": "Identifier",
                    }
                ],
            },
        )
        self.assertEqual(
            self.sql_payload(0)["binds"], [{"name": "table_name", "data_type": "VARCHAR", "value": "widgets"}]
        )
        self.assertEqual(self.sql_payload(1)["binds"][0]["value"], "WIDGETS")
        self.assertIn("FROM SYS.all_tab_columns", self.sql_payload(1)["statementText"])

    def test_mysql_metadata_uses_current_schema_and_nullable_flag(self):
        self.set_database_type("MYSQL")
        self.sql_replies(
            ords_rows(
                {
                    "column_name": "label",
                    "data_type": "text",
                    "data_length": None,
                    "nullable": "YES",
                    "data_default": None,
                    "comments": "",
                    "is_primary_key": 0,
                    "num_rows": None,
                }
            )
        )
        result = json.loads(self.server.get_table_info("Sample", "widgets"))
        self.assertTrue(result["columns"][0]["nullable"])
        self.assertIn("c.table_schema = database()", self.sql_payload()["statementText"])
        self.post.assert_called_once()

    def test_table_metadata_distinguishes_absent_and_malformed_results(self):
        for reply, expected_error in (
            (sql_response('{"items": []}'), "No data returned from query"),
            (ords_rows(), "No columns found for table"),
            (sql_response("non-JSON"), "Failed to parse SQL response"),
            (ords_rows({"column_name": "ID"}), "Error processing results: 'data_type'"),
        ):
            with self.subTest(error=expected_error):
                self.sql_replies(reply)
                self.assertEqual(
                    json.loads(self.server.get_table_info("Sample", "WIDGETS"))["error"], expected_error
                )

    def test_list_tables_queries_correct_catalog_and_extracts_rows(self):
        table = {"table_name": "WIDGETS", "num_rows": 5, "comments": "Examples"}
        for db_type, query in (
            ("ORACLE_DATABASE", "SYS.user_tables"),
            ("MYSQL", "information_schema.tables"),
        ):
            with self.subTest(db_type=db_type):
                self.set_database_type(db_type)
                self.sql_replies(ords_rows(table))
                self.assertEqual(json.loads(self.server.list_tables("Sample")), [table])
                self.assertIn(query, self.sql_payload()["statementText"])
        self.sql_replies(sql_response('{"items": []}'), sql_response("x" * 250))
        self.assertEqual(json.loads(self.server.list_tables("Sample")), [])
        self.assertEqual(json.loads(self.server.list_tables("Sample"))["raw_response"], "x" * 200 + "...")
        self.set_database_type("UNSUPPORTED")
        for tool, args in ((self.server.list_tables, ()), (self.server.get_table_info, ("WIDGETS",))):
            self.assertEqual(
                json.loads(tool("Sample", *args))["supported_types"], ["ORACLE_DATABASE", "MYSQL"]
            )

    def test_report_bootstrap_checks_current_schema_and_database_type(self):
        self.sql_replies(ords_rows({"owner": "EXAMPLE", "table_name": "REPORT_DEFINITIONS"}))
        result = json.loads(self.server.bootstrap_reports("Sample"))
        self.assertEqual(
            result, {"ok": True, "message": "Table 'report_definitions' exists in schema EXAMPLE"}
        )
        statement = self.sql_payload()["statementText"]
        self.assertIn("owner = SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA')", statement)
        self.post.assert_called_once()

        self.set_database_type("MYSQL")
        self.post.reset_mock()
        self.assertEqual(json.loads(self.server.bootstrap_reports("Sample"))["step"], "validate_type")
        self.post.assert_not_called()

    def test_report_bootstrap_reports_create_and_invalid_service_results(self):
        for replies, expected in (
            ((sql_response("opaque"),), {"ok": False, "step": "check_table"}),
            (
                (ords_rows(), sql_response('{"error": "missing privilege"}')),
                {"ok": False, "step": "create_table"},
            ),
            ((ords_rows(), sql_response("opaque")), {"ok": False, "step": "create_table"}),
            (
                (ords_rows(), sql_response('{"items": []}'), ords_rows({"schema": "EXAMPLE"})),
                {
                    "ok": True,
                    "message": "Table 'report_definitions' created in schema EXAMPLE",
                },
            ),
        ):
            with self.subTest(expected=expected):
                self.sql_replies(*replies)
                result = json.loads(self.server.bootstrap_reports("Sample"))
                self.assertEqual({key: result[key] for key in expected}, expected)
                if len(replies) >= 2:
                    self.assertIn("CREATE TABLE report_definitions", self.sql_payload(1)["statementText"])

    def test_create_report_binds_definition_and_embedding_text(self):
        self.sql_replies(ords_rows({"owner": "EXAMPLE"}), sql_response('{"items": []}'))
        result = json.loads(
            self.server.create_report(
                "Sample", "Today's sample", "SELECT :item FROM DUAL", "Example", ["item"]
            )
        )
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["report"]["sql_definition"], {"sql": "SELECT :item FROM DUAL", "binds": [{"name": "item"}]}
        )
        payload = self.sql_payload()
        self.assertIn(
            "VECTOR_EMBEDDING(EXAMPLE_MODEL USING :text_to_embed AS data)", payload["statementText"]
        )
        self.assertNotIn("Today's sample", payload["statementText"])
        binds = {field["name"]: field["value"] for field in payload["binds"]}
        self.assertEqual(binds["text_to_embed"], "Today's sample. Example")
        self.assertEqual(
            json.loads(binds["sql_definition"]),
            {
                "sql": "SELECT :item FROM DUAL",
                "binds": [{"name": "item"}],
            },
        )

    def test_create_report_rejects_invalid_reports_before_insert(self):
        for sql, names, expected_error in (
            ("SELECT 1", ["1bad"], "Invalid bind parameter names"),
            ("SELECT 1", ["item", "item"], "Duplicate bind parameter names are not allowed"),
            ("", None, "Invalid report SQL definition"),
        ):
            with self.subTest(error=expected_error):
                self.sql_replies(ords_rows({"owner": "EXAMPLE"}))
                result = json.loads(
                    self.server.create_report("Sample", "Example", sql, bind_parameters=names)
                )
                self.assertEqual(result["error"], expected_error)
                self.post.assert_called_once()
        self.sql_replies(ords_rows({"owner": "EXAMPLE"}), sql_response('{"error": "duplicate report"}'))
        result = json.loads(self.server.create_report("Sample", "Example", "SELECT 1"))
        self.assertEqual(result, {"error": "Failed to create report", "details": "duplicate report"})

    def test_execute_report_validates_stored_definition(self):
        for definition, detail in (
            ("not JSON", "sql_definition must be valid JSON object"),
            ([], "sql_definition must be an object"),
            ({"sql": "SELECT 1", "extra": True}, "contains unsupported keys"),
            ({"sql": " "}, "must be a non-empty string"),
            ({"sql": "SELECT 1", "binds": "item"}, "binds must be an array"),
            ({"sql": "SELECT 1", "binds": ["item"]}, "must be an object"),
            ({"sql": "SELECT 1", "binds": [{"name": "item", "value": 1}]}, "must only contain"),
            ({"sql": "SELECT 1", "binds": [{"name": "123"}]}, "Invalid bind name"),
            ({"sql": "SELECT 1", "binds": [{"name": "item"}, {"name": "item"}]}, "Duplicate bind name"),
        ):
            with self.subTest(detail=detail):
                self.sql_replies(ords_rows({"sql_definition": definition}))
                result = json.loads(self.server.execute_report("Sample", "Example"))
                self.assertEqual(result["error"], "Stored report definition is invalid")
                self.assertIn(detail, result["details"])
                self.post.assert_called_once()

    def test_execute_report_preserves_declared_bind_order_and_types(self):
        definition = {
            "sql": "SELECT :quantity, :price, :label, :date_filter FROM DUAL",
            "binds": [{"name": name} for name in ("quantity", "price", "label", "date_filter")],
        }
        self.sql_replies(ords_rows({"sql_definition": json.dumps(definition)}), ords_rows({"result": 1}))
        result = json.loads(
            self.server.execute_report(
                "Sample",
                "Example",
                {
                    "date_filter": None,
                    "label": "Today's sample",
                    "price": 2.5,
                    "quantity": 3,
                },
            )
        )
        self.assertEqual(result["items"][0]["resultSet"]["items"], [{"result": 1}])
        self.assertEqual(
            self.sql_payload(0)["binds"], [{"name": "name", "data_type": "VARCHAR", "value": "Example"}]
        )
        self.assertEqual(
            self.sql_payload(),
            {
                "statementText": "SELECT :quantity, :price, :label, :date_filter FROM DUAL",
                "binds": [
                    {"name": "quantity", "data_type": "NUMBER", "value": 3},
                    {"name": "price", "data_type": "NUMBER", "value": 2.5},
                    {"name": "label", "data_type": "VARCHAR", "value": "Today's sample"},
                    {"name": "date_filter", "data_type": "VARCHAR", "value": "None"},
                ],
            },
        )

    def test_execute_report_checks_requested_bind_values_before_running_statement(self):
        definition = {"sql": "SELECT :first, :second", "binds": [{"name": "first"}, {"name": "second"}]}
        for binds, expected in (
            (None, "Missing required bind parameters"),
            ({"extra": 1}, "Unexpected bind parameters provided"),
            ({"first": 1}, "Missing required bind parameter: second"),
            (["not an object"], "bind_values must be an object"),
        ):
            with self.subTest(error=expected):
                self.sql_replies(ords_rows({"sql_definition": definition}))
                result = json.loads(self.server.execute_report("Sample", "Example", binds))
                self.assertEqual(result["error"], expected)
                self.post.assert_called_once()

    def test_get_report_returns_normalized_definition_and_delete_uses_name_bind(self):
        row = {
            "name": "Today's sample",
            "description": "Example",
            "time_created": "2026-01-01T00:00:00Z",
            "time_updated": "2026-01-01T00:00:00Z",
            "sql_definition": json.dumps(
                {
                    "sql": "SELECT :item FROM DUAL",
                    "binds": [{"name": "item"}],
                }
            ),
        }
        self.sql_replies(ords_rows(row), ords_rows({"name": "Today's sample"}), sql_response('{"items": []}'))
        result = json.loads(self.server.get_report("Sample", "Today's sample"))
        self.assertEqual(result["sql_query"], "SELECT :item FROM DUAL")
        self.assertEqual(result["bind_parameters"], ["item"])
        self.assertEqual(result["time_updated"], "2026-01-01T00:00:00Z")
        self.assertTrue(json.loads(self.server.delete_report("Sample", "Today's sample"))["ok"])
        payload = self.sql_payload()
        self.assertIn("DELETE FROM report_definitions", payload["statementText"])
        self.assertEqual(
            payload["binds"], [{"name": "name", "data_type": "VARCHAR", "value": "Today's sample"}]
        )

    def test_report_lookup_and_delete_preserve_service_errors(self):
        for tool, malformed_error in (
            (self.server.get_report, "Failed to parse report definition"),
            (self.server.execute_report, "Failed to parse report definition"),
            (self.server.delete_report, "Failed to check report existence"),
        ):
            with self.subTest(tool=tool.__name__):
                self.sql_replies(sql_response('{"items": []}'), sql_response("opaque"))
                self.assertEqual(json.loads(tool("Sample", "Example"))["error"], "Report 'Example' not found")
                self.assertEqual(json.loads(tool("Sample", "Example"))["error"], malformed_error)
                self.assertEqual(self.post.call_count, 2)
        self.sql_replies(ords_rows({"name": "Example"}), sql_response('{"error": "delete denied"}'))
        self.assertEqual(
            json.loads(self.server.delete_report("Sample", "Example")),
            {"error": "Failed to delete report", "details": "delete denied"},
        )

    def test_list_and_search_reports_keep_query_and_result_contracts(self):
        row = {
            "name": "Example",
            "description": None,
            "time_created": "2026-01-01T00:00:00Z",
            "time_updated": "2026-01-01T00:00:00Z",
            "sql_definition": '{"sql": "SELECT 1"}',
            "similarity_score": "0.75",
        }
        self.sql_replies(
            ords_rows({"owner": "EXAMPLE"}), ords_rows(row), ords_rows({"owner": "EXAMPLE"}), ords_rows(row)
        )
        self.assertEqual(
            json.loads(self.server.list_reports("Sample"))["items"][0]["resultSet"]["items"], [row]
        )
        result = json.loads(self.server.find_matching_reports("Sample", "Today's report", 2))
        self.assertTrue(result["ok"])
        self.assertEqual(
            result["reports"], [{**row, "sql_definition": {"sql": "SELECT 1"}, "similarity_score": 0.75}]
        )
        payload = self.sql_payload()
        self.assertIn('ORDER BY "similarity_score" DESC', payload["statementText"])
        self.assertEqual(
            payload["binds"],
            [
                {"name": "search_text", "data_type": "VARCHAR", "value": "Today's report"},
                {"name": "limit", "data_type": "NUMBER", "value": 2},
            ],
        )

    def test_report_listing_and_creation_stop_when_bootstrap_fails(self):
        self.set_database_type("MYSQL")
        for tool, args in (
            (self.server.create_report, ("Example", "SELECT 1")),
            (self.server.list_reports, ()),
            (self.server.find_matching_reports, ("example search",)),
        ):
            with self.subTest(tool=tool.__name__):
                self.assertEqual(json.loads(tool("Sample", *args))["step"], "validate_type")
        self.post.assert_not_called()

    def test_vector_population_validates_identifiers_before_sql(self):
        for table, columns, vector_column, expected in (
            ("ITEMS", [], "SEARCH_VECTOR", "cannot be empty"),
            ("A.B.C", ["TITLE"], "SEARCH_VECTOR", "Invalid table_name"),
            ("ITEMS", ["TITLE"], "A.B", "Invalid vector_column_name"),
            ("ITEMS", ["TITLE"], "", "Invalid vector_column_name"),
            ("ITEMS", ["x" * 129], "SEARCH_VECTOR", "Invalid column name"),
        ):
            with self.subTest(message=expected):
                result = json.loads(self.server.ragify_column("Sample", table, columns, vector_column))
                self.assertEqual(result["status"], "error")
                self.assertIn(expected, result["message"])
        self.post.assert_not_called()

    def test_invalid_embedding_model_stops_vector_operations(self):
        with patch.object(self.server, "MODEL_NAME", "not an identifier"):
            self.assertIn(
                "Invalid MODEL_NAME",
                json.loads(self.server.ragify_column("Sample", "ITEMS", ["TITLE"], "SEARCH_VECTOR"))[
                    "message"
                ],
            )
            self.post.assert_not_called()
            for tool, args in (
                (self.server.create_report, ("Example", "SELECT 1")),
                (self.server.find_matching_reports, ("example search",)),
            ):
                with self.subTest(tool=tool.__name__):
                    self.sql_replies(ords_rows({"owner": "EXAMPLE"}))
                    self.assertIn("Invalid MODEL_NAME", json.loads(tool("Sample", *args))["error"])
                    self.post.assert_called_once()

    def test_vector_population_reports_outcome_after_existing_column(self):
        existing_column = sql_response(
            '{"items": [{"errorCode": 1430, "errorMessage": "column already exists"}]}'
        )
        failed_update = sql_response(
            '{"items": [{"errorCode": 20000, "errorMessage": "embedding unavailable"}]}'
        )
        for update, status in (
            (sql_response('{"items": []}'), "success"),
            (failed_update, "error"),
            (sql_response("opaque"), "warning"),
        ):
            with self.subTest(status=status):
                self.sql_replies(existing_column, sql_response('{"items": []}'), update)
                with redirect_stdout(io.StringIO()):
                    result = json.loads(
                        self.server.ragify_column(
                            "Sample", " EXAMPLE.ITEMS ", [" TITLE ", "DESCRIPTION"], " SEARCH_VECTOR "
                        )
                    )
                self.assertEqual(result["status"], status)
                self.assertEqual(
                    self.sql_payload(0)["statementText"],
                    "ALTER TABLE EXAMPLE.ITEMS ADD (SEARCH_VECTOR VECTOR(384))",
                )
                self.assertIn(
                    "COMMENT ON COLUMN EXAMPLE.ITEMS.SEARCH_VECTOR", self.sql_payload(1)["statementText"]
                )
                self.assertIn(
                    "WHERE TITLE IS NOT NULL OR DESCRIPTION IS NOT NULL", self.sql_payload(2)["statementText"]
                )

    def test_heatwave_tools_use_mysql_and_parse_statement_result(self):
        cases = (
            (self.server.heatwave_ask_help, "sys.NL2ML", 1, {"text": "ML docs"}, "ML docs"),
            (
                self.server.heatwave_ask_ml_rag,
                "sys.ml_rag",
                2,
                {"context": ["sample"]},
                {"context": ["sample"]},
            ),
            (
                self.server.heatwave_ask_nl_sql,
                "sys.NL_SQL",
                1,
                {"sql_query": "SELECT 1"},
                '{"sql_query": "SELECT 1"}',
            ),
            (
                self.server.heatwave_retrieve_relevant_schema_information,
                "sys.ML_RETRIEVE_SCHEMA_METADATA",
                1,
                {"create_statements": "CREATE TABLE sample (id INT)"},
                '"{\\"create_statements\\": \\"CREATE TABLE sample (id INT)\\"}"',
            ),
        )
        for tool, procedure, index, data, expected in cases:
            with self.subTest(tool=tool.__name__):
                self.set_database_type("ORACLE_DATABASE")
                self.post.reset_mock()
                self.assertIn("only available for MySQL", json.loads(tool("Sample", "Question"))["error"])
                self.post.assert_not_called()
                self.set_database_type("MYSQL")
                items = [{}] * index + [
                    {
                        "resultSet": {
                            "metadata": [{"jsonColumnName": "result"}],
                            "items": [{"result": json.dumps(data)}],
                        }
                    }
                ]
                self.sql_replies(sql_response(json.dumps({"items": items})), sql_response("opaque"))
                self.assertEqual(tool("Sample", "What's the sample?"), expected)
                statement = self.sql_payload()["statementText"]
                self.assertIn(procedure, statement)
                self.assertIn("What''s the sample?", statement)
                self.assertIn("error", json.loads(tool("Sample", "Question")))

    def test_heatwave_vector_load_binds_store_and_schema_in_sql_literals(self):
        args = ("Sample", "namespace", "bucket", "prefix's", "schema", "table")
        self.assertIn(
            "only available for MySQL", json.loads(self.server.heatwave_load_vector_store(*args))["error"]
        )
        self.post.assert_not_called()
        self.set_database_type("MYSQL")
        self.sql_replies(sql_response('{"items": []}'))
        self.assertEqual(json.loads(self.server.heatwave_load_vector_store(*args)), {"items": []})
        statement = self.sql_payload()["statementText"]
        self.assertIn("JSON_OBJECT('schema_name', 'schema', 'table_name', 'table')", statement)
        self.assertIn("CALL sys.VECTOR_STORE_LOAD('oci://bucket@namespace/prefix''s'", statement)
