import contextlib
import importlib.util
import json
import os
import sys
import types
import unittest
import uuid
from unittest import mock

import mysql_mcp_server as m
from utils import get_ssh_command, fill_config_defaults

SKIP_ESTABLISHED = False


def get_server_module():
    # Dynamically load the server module but shim fastmcp so @mcp.tool() returns the original function
    # This avoids FunctionTool non-callable wrappers when importing FastMCP from 'fastmcp'.

    server_path = os.path.join(os.path.dirname(__file__), "mysql_mcp_server.py")
    if not os.path.exists(server_path):
        raise FileNotFoundError(f"Server file not found at {server_path}")

    class _ShimFastMCP:
        def __init__(self, name):
            self.name = name

        def tool(self, *args, **kwargs):
            def _decorator(fn):
                return fn  # keep functions directly callable in tests

            return _decorator

        def run(self, transport="stdio"):
            # no-op for tests
            pass

    prev_fastmcp = sys.modules.get("fastmcp")
    fastmcp_mod = types.ModuleType("fastmcp")
    fastmcp_mod.FastMCP = _ShimFastMCP
    sys.modules["fastmcp"] = fastmcp_mod

    try:
        spec = importlib.util.spec_from_file_location(
            "mysql_mcp_server_under_test", server_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if prev_fastmcp is not None:
            sys.modules["fastmcp"] = prev_fastmcp
        else:
            del sys.modules["fastmcp"]

    return module


src_module = get_server_module()


def get_first_valid_connection_id(desired_mode=None):
    payload = json.loads(src_module.list_all_connections())
    valid = payload.get("valid keys", [])
    if not isinstance(valid, list) or len(valid) == 0:
        raise Exception("No valid connections")

    def _is_valid_entry(e):
        return (
            isinstance(e, dict)
            and "key" in e
            and "mode" in e
            and isinstance(e["mode"], str)
        )

    if desired_mode is None:
        first = valid[0]
        if not _is_valid_entry(first):
            raise Exception("Unexpected format for valid keys")
        return first["key"]

    for entry in valid:
        desired_value = getattr(desired_mode, "value", str(desired_mode))
        if _is_valid_entry(entry) and entry["mode"] == desired_value:
            return entry["key"]

    raise Exception(f"No valid connections for mode {desired_mode}")


try:
    get_first_valid_connection_id(m.Mode.MYSQL_AI)
    SKIP_MYSQL_AI = False
except:
    SKIP_MYSQL_AI = True

try:
    get_first_valid_connection_id(m.Mode.OCI)
    SKIP_OCI = False
except:
    SKIP_OCI = True

MYSQL_AI_SKIP_MSG = "Skip MySQL AI Dependent Test"
OCI_SKIP_MSG = "Skip OCI Dependent Test"


class TestMysqlMcpUtilities(unittest.TestCase):
    # ---- Mode ----
    def test_mode_from_string_valid(self):
        self.assertEqual(m.Mode.from_string("LCL"), m.Mode.MYSQL_AI)
        self.assertEqual(m.Mode.from_string("OCI"), m.Mode.OCI)
        # Case-insensitivity
        self.assertEqual(m.Mode.from_string("lcl"), m.Mode.MYSQL_AI)
        self.assertEqual(m.Mode.from_string("oci"), m.Mode.OCI)

    def test_mode_from_string_invalid(self):
        with self.assertRaises(ValueError):
            m.Mode.from_string("XYZ")

    # ---- _validate_name ----
    def test_validate_name_valid(self):
        self.assertEqual(m._validate_name("Valid_Name_123"), "Valid_Name_123")
        self.assertEqual(m._validate_name("A"), "A")
        self.assertEqual(m._validate_name("a_b_c"), "a_b_c")
        self.assertEqual(m._validate_name("Z9_"), "Z9_")

    def test_validate_name_invalid(self):
        for bad in [
            "invalid-name!",
            "space name",
            "semi;colon",
            "quote'name",
            "star*",
            "dash-",
            "dot.",
            "slash/",
        ]:
            with self.assertRaises(ValueError, msg=f"Expected failure for {bad}"):
                m._validate_name(bad)

    # ---- get_error / check_error ----
    def test_get_error_and_check_error(self):
        # None / non-JSON
        self.assertIsNone(m.get_error(None))
        self.assertFalse(m.check_error(None))
        self.assertIsNone(m.get_error("not-json"))
        self.assertFalse(m.check_error("not-json"))

        # JSON but not dict
        self.assertIsNone(m.get_error(json.dumps([1, 2, 3])))
        self.assertFalse(m.check_error(json.dumps([1, 2, 3])))

        # JSON dict without error
        ok = json.dumps({"ok": True})
        self.assertIsNone(m.get_error(ok))
        self.assertFalse(m.check_error(ok))

        # JSON dict with error
        err = json.dumps({"error": "boom"})
        self.assertEqual(m.get_error(err), "boom")
        self.assertTrue(m.check_error(err))

    # ---- fetch_one ----
    def test_fetch_one_success(self):
        self.assertEqual(m.fetch_one(json.dumps([["value"]])), "value")
        self.assertEqual(m.fetch_one(json.dumps([[123]])), 123)

    def test_fetch_one_wrong_rowcount(self):
        with self.assertRaises(Exception) as ctx:
            m.fetch_one(json.dumps([["a"], ["b"]]))
        self.assertIn("Unexpected response invalid number of rows", str(ctx.exception))

        with self.assertRaises(Exception):
            m.fetch_one(json.dumps([]))

    # ---- _get_mode (all DB calls mocked) ----
    def test_get_mode_success_mysql_ai(self):
        # Simulate SELECT @@rapid_cloud_provider; returning a single row 'LCL'
        provider_result = json.dumps([["LCL"]])
        with mock.patch.object(
            m, "_execute_sql_tool", return_value=provider_result
        ):
            mode = m._get_mode("any_conn")
            self.assertEqual(mode, m.Mode.MYSQL_AI)

    def test_get_mode_success_oci(self):
        provider_result = json.dumps([["OCI"]])
        with mock.patch.object(
            m, "_execute_sql_tool", return_value=provider_result
        ):
            mode = m._get_mode("any_conn")
            self.assertEqual(mode, m.Mode.OCI)

    def test_get_mode_error_from_check_error(self):
        # If the tool returns an error JSON dict, check_error returns True -> raises Exception
        provider_result = json.dumps({"error": "driver failure"})
        with mock.patch.object(
            m, "_execute_sql_tool", return_value=provider_result
        ):
            with self.assertRaises(Exception) as ctx:
                m._get_mode("any_conn")
            self.assertIn(
                "Exception occurred while fetching cloud provider", str(ctx.exception)
            )

    def test_get_mode_invalid_provider_value(self):
        # Single row but invalid provider value -> Mode.from_string raises ValueError
        provider_result = json.dumps([["XYZ"]])
        with mock.patch.object(
            m, "_execute_sql_tool", return_value=provider_result
        ):
            with self.assertRaises(ValueError):
                m._get_mode("any_conn")


class TestLoadMySQLConfig(unittest.TestCase):
    def _valid_config(self):
        return {
            "server_infos": {
                "myconn": {
                    "host": "h",
                    "user": "u",
                    "password": "p",
                    "database": "db",
                    "port": 3306,
                }
            }
        }

    def test_load_uses_env_path_when_set(self):
        cfg_path = "/tmp/conf.json"
        data = self._valid_config()
        with mock.patch.dict(os.environ, {"MYSQL_MCP_CONFIG": cfg_path}, clear=False), \
             mock.patch("os.path.isfile", return_value=True), \
             mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(data))):
            cfg = m.load_mysql_config()
        self.assertEqual(cfg, data)

    def test_load_uses_module_local_config_when_env_unset(self):
        # Determine the utils module directory the function belongs to
        utils_dir = os.path.dirname(os.path.abspath(m.load_mysql_config.__code__.co_filename))
        local_path = os.path.join(utils_dir, "local_config.json")

        def isfile_side_effect(path):
            return path == local_path

        data = self._valid_config()
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch("os.path.isfile", side_effect=isfile_side_effect), \
             mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(data))):
            cfg = m.load_mysql_config()
        self.assertEqual(cfg, data)

    def test_load_raises_when_file_missing(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch("os.path.isfile", return_value=False):
            with self.assertRaises(Exception) as ctx:
                m.load_mysql_config()
        self.assertIn("Config file not found", str(ctx.exception))

    def test_invalid_config_raises_via_fill_config_defaults(self):
        # Missing 'server_infos'
        bad = {"conn": {"host": "h"}}
        cfg_path = "/x/y/z.json"
        with mock.patch.dict(os.environ, {"MYSQL_MCP_CONFIG": cfg_path}, clear=False), \
             mock.patch("os.path.isfile", return_value=True), \
             mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(bad))):
            with self.assertRaises(Exception) as ctx:
                m.load_mysql_config()
        self.assertIn("server_infos", str(ctx.exception))


class TestDbConnectionUtilities(unittest.TestCase):
    def test_get_db_connection_success_calls_connector(self):
        cfg = {
            "server_infos": {
                "good": {
                    "database": "testdb",
                    "user": "u",
                    "password": "p",
                    "host": "h",
                    "port": 3306,
                }
            }
        }
        mock_conn = mock.Mock(name="MySQLConnection")

        with mock.patch.object(m, "config", cfg), mock.patch.object(
            m.connector, "connect", return_value=mock_conn
        ) as connect_mock:
            conn = m._get_db_connection("good")

        self.assertIs(conn, mock_conn)
        connect_mock.assert_called_once_with(**cfg["server_infos"]["good"])

    def test_get_db_connection_invalid_id_raises(self):
        with mock.patch.object(m, "config", {"server_infos": {}}):
            with self.assertRaises(m.DatabaseConnectionError) as ctx:
                m._get_db_connection("nope")
        self.assertIn("is not a valid connection", str(ctx.exception))

    def test_get_db_connection_missing_database_key_raises(self):
        with mock.patch.object(m, "config", {"server_infos": {"bad": {"host": "h", "user": "u"}}}):
            with self.assertRaises(m.DatabaseConnectionError) as ctx:
                m._get_db_connection("bad")
        self.assertIn("Database must be specified in config", str(ctx.exception))

    def test_get_db_connection_connect_failure_wrapped(self):
        cfg = {"server_infos": {"good": {"database": "testdb", "user": "u"}}}
        with mock.patch.object(m, "config", cfg), mock.patch.object(
            m.connector, "connect", side_effect=RuntimeError("driver down")
        ):
            with self.assertRaises(m.DatabaseConnectionError) as ctx:
                m._get_db_connection("good")
        self.assertIn("Connection failed with error: driver down", str(ctx.exception))

    def test_get_db_connection_config_error_msg_not_none_raises(self):
        error_msg = json.dumps({"error": "Config failed"})
        with mock.patch.object(m, "config_error_msg", error_msg):
            with self.assertRaises(m.DatabaseConnectionError) as ctx:
                m._get_db_connection("any")
        self.assertIn("Configuration file is not loaded", str(ctx.exception))

    def test_get_database_connection_cm_closes_on_success(self):
        mock_conn = mock.Mock(name="MySQLConnection")
        with mock.patch.object(m, "_get_db_connection", return_value=mock_conn):
            with m._get_database_connection_cm("any") as conn:
                self.assertIs(conn, mock_conn)
            mock_conn.close.assert_called_once()

    def test_get_database_connection_cm_closes_on_exception(self):
        mock_conn = mock.Mock(name="MySQLConnection")
        with mock.patch.object(m, "_get_db_connection", return_value=mock_conn):
            with self.assertRaises(ValueError):
                with m._get_database_connection_cm("any") as conn:
                    self.assertIs(conn, mock_conn)
                    raise ValueError("boom")
            mock_conn.close.assert_called_once()


class TestListAllConnections(unittest.TestCase):
    def test_list_all_connections_config_error_msg_not_none(self):
        error_msg = json.dumps({"error": "Config failed"})
        with mock.patch.object(src_module, "config_error_msg", error_msg):
            out = src_module.list_all_connections()
        self.assertEqual(out, error_msg)

    def test_list_all_connections_all_valid_mocked(self):
        cfg = {"server_infos": {"conn1": {"database": "db1"}, "conn2": {"database": "db2"}}}

        @contextlib.contextmanager
        def ok_cm(_cid):
            yield None

        with mock.patch.object(
            src_module, "config", cfg, create=True
        ), mock.patch.object(
            src_module, "_get_database_connection_cm", new=ok_cm
        ), mock.patch.object(
            src_module, "_get_mode", return_value=src_module.Mode.MYSQL_AI
        ):
            out = src_module.list_all_connections()

        self.assertIsInstance(out, str)
        payload = json.loads(out)
        self.assertIn("valid keys", payload)
        self.assertIn("invalid keys", payload)
        self.assertEqual(len(payload["valid keys"]), len(cfg["server_infos"]))
        self.assertEqual(payload["invalid keys"], [])
        keys = [k["key"] for k in payload["valid keys"]]
        modes = [k["mode"] for k in payload["valid keys"]]
        self.assertCountEqual(keys, list(cfg["server_infos"].keys()))
        self.assertTrue(all(mode in ("MYSQL_AI", "OCI") for mode in modes))

    def test_list_all_connections_mixed_mocked(self):
        cfg = {"server_infos": {"good": {"database": "db"}, "bad": {"database": "db"}}}

        @contextlib.contextmanager
        def mixed_cm(cid):
            if cid == "bad":
                raise RuntimeError("boom")
            yield None

        with mock.patch.object(
            src_module, "config", cfg, create=True
        ), mock.patch.object(
            src_module, "_get_database_connection_cm", new=mixed_cm
        ), mock.patch.object(
            src_module, "_get_mode", return_value=src_module.Mode.OCI
        ):
            out = src_module.list_all_connections()

        payload = json.loads(out)
        self.assertIn("valid keys", payload)
        self.assertIn("invalid keys", payload)
        self.assertTrue(
            any(
                v["key"] == "good" and v["mode"] in ("MYSQL_AI", "OCI")
                for v in payload["valid keys"]
            )
        )
        self.assertTrue(
            any(
                x["key"] == "bad" and "boom" in x["error"]
                for x in payload["invalid keys"]
            )
        )

    def test_list_all_connections_all_invalid_mocked(self):
        cfg = {"server_infos": {"k1": {"database": "db"}, "k2": {"database": "db"}}}

        def failing_cm(_cid):
            raise m.DatabaseConnectionError("cannot connect")

        with mock.patch.object(
            src_module, "config", cfg, create=True
        ), mock.patch.object(
            src_module, "_get_database_connection_cm", side_effect=failing_cm
        ):
            out = src_module.list_all_connections()

        payload = json.loads(out)
        self.assertEqual(payload["valid keys"], [])
        self.assertCountEqual(
            [e["key"] for e in payload["invalid keys"]], list(cfg["server_infos"].keys())
        )
        for e in payload["invalid keys"]:
            self.assertIn("cannot connect", e["error"])

    def test_list_all_connections_empty_config_mocked(self):
        with mock.patch.object(src_module, "config", {"server_infos": {}}, create=True):
            out = src_module.list_all_connections()
        payload = json.loads(out)
        self.assertEqual(payload["valid keys"], [])
        self.assertEqual(payload["invalid keys"], [])

    def test_list_all_connections_real_json_and_at_least_one_valid(self):
        out = src_module.list_all_connections()
        self.assertIsInstance(out, str)
        payload = json.loads(out)
        self.assertIn("valid keys", payload)
        self.assertIn("invalid keys", payload)
        self.assertIsInstance(payload["valid keys"], list)
        self.assertIsInstance(payload["invalid keys"], list)
        if payload["valid keys"]:
            self.assertIsInstance(payload["valid keys"][0], dict)
            self.assertIn("key", payload["valid keys"][0])
            self.assertIn("mode", payload["valid keys"][0])
        self.assertGreaterEqual(len(payload["valid keys"]), 1)


class TestExecuteSqlTool(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.conn_id = get_first_valid_connection_id()

    # ---- Minimal mocking for exception/error branches ----
    def test_execute_sql_tool_connection_id_connect_failure_returns_error_json(self):
        with mock.patch.object(
            src_module, "_get_db_connection", side_effect=Exception("no connect")
        ):
            out = src_module._execute_sql_tool("any_conn", "SELECT 1")
        self.assertTrue(src_module.check_error(out))
        payload = json.loads(out)
        self.assertIn("unable to establish a database connection", payload["error"])

    def test_execute_sql_tool_execute_exception_returns_error_json_and_includes_context(
        self,
    ):
        # Mock connection and cursor to raise on execute
        mock_cursor_cm = mock.MagicMock()
        mock_cursor = mock_cursor_cm.__enter__.return_value
        mock_cursor.execute.side_effect = RuntimeError("bad sql")
        mock_conn = mock.MagicMock()
        mock_conn.cursor.return_value = mock_cursor_cm

        out = src_module._execute_sql_tool(mock_conn, "SELECT oops", params=[1, 2, 3])
        self.assertTrue(src_module.check_error(out))
        payload = json.loads(out)
        self.assertIn("Error executing SQL", payload["error"])
        self.assertEqual(payload["sql_script"], "SELECT oops")
        self.assertEqual(payload["params"], [1, 2, 3])
        # When passing a connection object, it should NOT close in finally
        mock_conn.close.assert_not_called()

    def test_execute_sql_tool_no_result_set_returns_json_null(self):
        # Mock a statement with no result set (description is None)
        mock_cursor_cm = mock.MagicMock()
        mock_cursor = mock_cursor_cm.__enter__.return_value
        mock_cursor.description = None  # no rows
        mock_cursor.nextset.return_value = None
        mock_conn = mock.MagicMock()
        mock_conn.cursor.return_value = mock_cursor_cm

        out = src_module._execute_sql_tool(mock_conn, "DO 1")
        self.assertFalse(src_module.check_error(out))
        self.assertIsNone(json.loads(out))
        mock_conn.commit.assert_called_once()

    def test_execute_sql_tool_closes_when_connection_id_used_no_result_set(self):
        mock_conn = mock.MagicMock()
        mock_cursor_cm = mock.MagicMock()
        mock_cursor = mock_cursor_cm.__enter__.return_value
        mock_cursor.description = None  # No result set -> JSON null
        mock_cursor.nextset.return_value = None
        mock_conn.cursor.return_value = mock_cursor_cm

        with mock.patch.object(
            src_module, "_get_db_connection", return_value=mock_conn
        ):
            out = src_module._execute_sql_tool("good_conn", "SELECT 1")

        self.assertFalse(m.check_error(out))
        self.assertIsNone(json.loads(out))
        mock_conn.close.assert_called_once()

    def test_execute_sql_tool_closes_when_connection_id_used_with_result_set(self):
        mock_conn = mock.MagicMock()
        mock_cursor_cm = mock.MagicMock()
        mock_cursor = mock_cursor_cm.__enter__.return_value
        mock_cursor.description = None  # No result set -> JSON null
        mock_cursor.nextset.return_value = None
        mock_conn = mock.MagicMock()
        mock_conn.cursor.return_value = mock_cursor_cm
        mock_cursor = mock_cursor_cm.__enter__.return_value
        mock_cursor.description = [("col",)]  # Indicate a result set
        mock_cursor.fetchall.return_value = [[1]]  # JSON-serializable rows
        mock_cursor.nextset.return_value = None
        mock_conn.cursor.return_value = mock_cursor_cm

        with mock.patch.object(
            src_module, "_get_db_connection", return_value=mock_conn
        ):
            out = src_module._execute_sql_tool("good_conn", "SELECT 1")

        self.assertFalse(m.check_error(out))
        self.assertEqual(json.loads(out), [[1]])
        mock_conn.close.assert_called_once()

    def test_execute_sql_tool_by_connection_id_wrapper_delegates(self):
        with mock.patch.object(
            src_module, "_execute_sql_tool", return_value="[]"
        ) as inner:
            out = src_module.execute_sql_tool_by_connection_id(
                "cid", "SELECT 1", params=[42]
            )
        self.assertEqual(out, "[]")
        inner.assert_called_once_with("cid", "SELECT 1", params=[42])

    def test_real_valid_select_no_error(self):
        out = src_module.execute_sql_tool_by_connection_id(self.conn_id, "SELECT 1")
        self.assertFalse(src_module.check_error(out))
        data = json.loads(out)
        self.assertIsInstance(data, list)

    def test_real_semantically_invalid_no_error(self):
        # MySQL typically returns NULL (with warning) for division by zero rather than an error
        out = src_module.execute_sql_tool_by_connection_id(self.conn_id, "SELECT 1/0")
        self.assertFalse(src_module.check_error(out))
        data = json.loads(out)
        self.assertIsInstance(data, list)

    def test_real_valid_multi_select_error(self):
        # Multiple selects are not supported currently
        out = src_module.execute_sql_tool_by_connection_id(self.conn_id, "SELECT 1; SELECT 2;")
        self.assertFalse(src_module.check_error(out))
        data = json.loads(out)
        self.assertEqual(data, [[1], [2]])


class TestMlGenerate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.conn_id = get_first_valid_connection_id()

    def test_ml_generate_returns_plain_text_on_success(self):
        # Simulate SELECT sys.ML_GENERATE returning a single-row JSON string with {"text": "..."}
        row = json.dumps({"text": "hello world"})
        with mock.patch.object(
            src_module,
            "_execute_sql_tool",
            return_value=json.dumps([[row]]),
        ):
            out = src_module.ml_generate("any", "Q")
        self.assertFalse(src_module.check_error(out))
        self.assertIsInstance(out, str)
        self.assertEqual(out, "hello world")

    def test_ml_generate_propagates_error_when_check_error_true(self):
        with mock.patch.object(
            src_module,
            "_execute_sql_tool",
            return_value=json.dumps({"error": "forced"}),
        ):
            out = src_module.ml_generate("any", "Q")
        self.assertTrue(src_module.check_error(out))
        payload = json.loads(out)
        self.assertIn("Error with ML_GENERATE", payload["error"])

    def test_ml_generate_unexpected_format_when_non_json_string_in_row(self):
        # fetch_one will succeed but json.loads(response_data) will fail
        with mock.patch.object(
            src_module,
            "_execute_sql_tool",
            return_value=json.dumps([["not-json"]]),
        ):
            out = src_module.ml_generate("any", "Q")
        self.assertTrue(src_module.check_error(out))
        self.assertIn("Unexpected response format", json.loads(out)["error"])

    def test_ml_generate_unexpected_format_when_missing_text_key(self):
        # JSON string but missing "text" key -> KeyError -> caught -> error JSON
        row = json.dumps({"not_text": "value"})
        with mock.patch.object(
            src_module,
            "_execute_sql_tool",
            return_value=json.dumps([[row]]),
        ):
            out = src_module.ml_generate("any", "Q")
        self.assertTrue(src_module.check_error(out))
        self.assertIn("Unexpected response format", json.loads(out)["error"])

    def test_ml_generate_unexpected_format_when_wrong_rowcount(self):
        # fetch_one raises due to wrong row count -> caught -> error JSON
        row = json.dumps({"text": "ignored"})
        with mock.patch.object(
            src_module,
            "_execute_sql_tool",
            return_value=json.dumps([[row], [row]]),
        ):
            out = src_module.ml_generate("any", "Q")
        self.assertTrue(src_module.check_error(out))
        self.assertIn("Unexpected response format", json.loads(out)["error"])

    def test_ml_generate_real(self):
        out = src_module.ml_generate(self.conn_id, "Hello from test")
        self.assertFalse(src_module.check_error(out))
        self.assertIsInstance(out, str)


class TestRagifyColumn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.conn_id = get_first_valid_connection_id()

    def test_ragify_column_success_mocked(self):
        class FakeConn:
            database = "test_schema"

        fake_conn = FakeConn()

        @contextlib.contextmanager
        def cm(_cid):
            yield fake_conn

        with mock.patch.object(
            src_module, "_get_database_connection_cm", new=cm
        ), mock.patch.object(
            src_module, "_execute_sql_tool", return_value=json.dumps(None)
        ) as exec_mock:
            out = src_module.ragify_column("any", "docs", "body", "embedding")

        self.assertFalse(src_module.check_error(out))
        self.assertIsInstance(out, str)
        self.assertTrue(out.startswith("Successfully added embedding column"))

        expected_qualified_text = "test_schema.docs.body"
        expected_qualified_embedding = "test_schema.docs.embedding"
        exec_mock.assert_called_once()
        called_args, called_kwargs = exec_mock.call_args
        self.assertIn("CALL sys.ML_EMBED_TABLE", called_args[1])
        self.assertEqual(called_kwargs["params"][0], expected_qualified_text)
        self.assertEqual(called_kwargs["params"][1], expected_qualified_embedding)

    def test_ragify_column_error_branch_mocked(self):
        class FakeConn:
            database = "sch"

        @contextlib.contextmanager
        def cm(_cid):
            yield FakeConn()

        with mock.patch.object(
            src_module, "_get_database_connection_cm", new=cm
        ), mock.patch.object(
            src_module,
            "_execute_sql_tool",
            return_value=json.dumps({"error": "forced"}),
        ):
            out = src_module.ragify_column("any", "docs", "body", "embedding")

        self.assertTrue(src_module.check_error(out))
        payload = json.loads(out)
        self.assertIn("Error with ML_EMBED_TABLE", payload["error"])

    def test_ragify_column_passes_connection_context_mocked(self):
        class FakeConn:
            database = "sch"

        captured_conn = {}

        @contextlib.contextmanager
        def cm(_cid):
            fc = FakeConn()
            captured_conn["obj"] = fc
            yield fc

        def exec_side_effect(conn, sql, params=None):
            self.assertIs(conn, captured_conn["obj"])
            return json.dumps(None)

        with mock.patch.object(
            src_module, "_get_database_connection_cm", new=cm
        ), mock.patch.object(
            src_module, "_execute_sql_tool", side_effect=exec_side_effect
        ):
            out = src_module.ragify_column("any", "t", "c", "e")
        self.assertFalse(src_module.check_error(out))

    def test_ragify_column_real(self):
        table = f"gc_docs_{uuid.uuid4().hex[:8]}"
        text_col = "body"
        embed_col = "embedding"

        try:
            # Create table with a primary key
            create_sql = f"CREATE TABLE {table} (id INT PRIMARY KEY AUTO_INCREMENT, {text_col} TEXT)"
            out = src_module.execute_sql_tool_by_connection_id(self.conn_id, create_sql)
            self.assertFalse(src_module.check_error(out), f"create table failed: {out}")

            # Insert at least two rows
            ins1 = src_module.execute_sql_tool_by_connection_id(
                self.conn_id,
                f"INSERT INTO {table} ({text_col}) VALUES (%s)",
                params=["row one"],
            )
            ins2 = src_module.execute_sql_tool_by_connection_id(
                self.conn_id,
                f"INSERT INTO {table} ({text_col}) VALUES (%s)",
                params=["row two"],
            )
            self.assertFalse(src_module.check_error(ins1), f"insert 1 failed: {ins1}")
            self.assertFalse(src_module.check_error(ins2), f"insert 2 failed: {ins2}")

            # Run ragify and require success
            result = src_module.ragify_column(self.conn_id, table, text_col, embed_col)
            self.assertFalse(
                src_module.check_error(result), f"ragify_column failed: {result}"
            )
            self.assertIsInstance(result, str)
            self.assertTrue(result.startswith("Successfully added embedding column"))
        finally:
            src_module.execute_sql_tool_by_connection_id(
                self.conn_id, f"DROP TABLE IF EXISTS {table}"
            )


class TestListVectorStoreFilesLocal(unittest.TestCase):

    def test_list_vector_store_files_local_success_mocked(self):
        files_payload = [
            {"name": "file:///secure/path/doc1.pdf"},
            {"name": "file:///secure/path/sub/doc2.txt"},
        ]
        execute_result = json.dumps([[json.dumps(files_payload)]])

        with mock.patch.object(
            src_module, "_get_mode", return_value=src_module.Mode.MYSQL_AI
        ), mock.patch.object(
            src_module, "_execute_sql_tool", return_value=execute_result
        ):
            out = src_module.list_vector_store_files_local("cid")

        self.assertFalse(src_module.check_error(out))
        files = json.loads(out)
        self.assertIsInstance(files, list)
        self.assertListEqual(
            files, ["/secure/path/doc1.pdf", "/secure/path/sub/doc2.txt"]
        )

    def test_list_vector_store_files_local_wrong_mode_mocked(self):
        with mock.patch.object(
            src_module, "_get_mode", return_value=src_module.Mode.OCI
        ):
            out = src_module.list_vector_store_files_local("cid")
        self.assertTrue(src_module.check_error(out))
        self.assertIn("not MySQL AI", json.loads(out)["error"])

    def test_list_vector_store_files_local_malformed_result_mocked(self):
        # Cause fetch_one to raise (e.g., unexpected rowcount)
        with mock.patch.object(
            src_module, "_get_mode", return_value=src_module.Mode.MYSQL_AI
        ), mock.patch.object(
            src_module,
            "_execute_sql_tool",
            return_value=json.dumps([["x"], ["y"]]),
        ):
            out = src_module.list_vector_store_files_local("cid")
        self.assertTrue(src_module.check_error(out))
        self.assertIn("Error with LIST_FILES", json.loads(out)["error"])

    def test_list_vector_store_files_local_bad_json_payload_mocked(self):
        # fetch_one returns a string that isn't JSON -> json.loads fails -> caught -> error JSON
        with mock.patch.object(
            src_module, "_get_mode", return_value=src_module.Mode.MYSQL_AI
        ), mock.patch.object(
            src_module,
            "_execute_sql_tool",
            return_value=json.dumps([["not-json"]]),
        ):
            out = src_module.list_vector_store_files_local("cid")
        self.assertTrue(src_module.check_error(out))
        self.assertIn("Error with LIST_FILES", json.loads(out)["error"])

    @unittest.skipIf(SKIP_MYSQL_AI, MYSQL_AI_SKIP_MSG)
    def test_list_vector_store_files_local_real(self):
        conn_id = get_first_valid_connection_id(m.Mode.MYSQL_AI)
        out = src_module.list_vector_store_files_local(conn_id)
        self.assertFalse(m.check_error(out))
        files = json.loads(out)
        self.assertIsInstance(files, list)
        self.assertGreaterEqual(len(files), 1)


class TestAskMlRagHelper(unittest.TestCase):
    def test_success_path_returns_scalar_string(self):
        # Capture the connection object to ensure it is passed to _execute_sql_tool
        captured = {}

        @contextlib.contextmanager
        def cm(_cid):
            conn = object()
            captured["conn"] = conn
            yield conn

        calls = []

        def exec_side_effect(conn, sql, params=None):
            # Validate the same connection object is used for all calls
            self.assertIs(conn, captured["conn"])
            calls.append((sql, params))
            if sql.startswith("SET @options"):
                return json.dumps(None)
            if sql.startswith("CALL sys.ML_RAG"):
                # Ensure question param is passed
                self.assertEqual(params, ["What is up?"])
                return json.dumps(None)
            if sql.startswith("SELECT @response"):
                # Single-row scalar string that fetch_one should return directly
                return json.dumps([["final-answer"]])
            self.fail(f"Unexpected SQL: {sql}")

        with mock.patch.object(
            m, "_get_database_connection_cm", new=cm
        ), mock.patch.object(m, "_execute_sql_tool", side_effect=exec_side_effect):
            out = m._ask_ml_rag_helper(
                "cid", "What is up?", "JSON_OBJECT('skip_generate', true)"
            )

        self.assertFalse(m.check_error(out))
        self.assertEqual(out, "final-answer")
        # Ensure expected sequence of calls
        self.assertEqual(len(calls), 3)
        self.assertTrue(calls[0][0].startswith("SET @options"))
        self.assertTrue(calls[1][0].startswith("CALL sys.ML_RAG"))
        self.assertTrue(calls[2][0].startswith("SELECT @response"))

    def test_set_options_error_short_circuit(self):
        @contextlib.contextmanager
        def cm(_cid):
            yield object()

        def exec_side_effect(conn, sql, params=None):
            if sql.startswith("SET @options"):
                return json.dumps({"error": "failed to set options"})
            self.fail("Subsequent calls should not execute when set fails")

        with mock.patch.object(
            m, "_get_database_connection_cm", new=cm
        ), mock.patch.object(m, "_execute_sql_tool", side_effect=exec_side_effect):
            out = m._ask_ml_rag_helper("cid", "Q", "JSON_OBJECT('skip_generate', true)")

        self.assertTrue(m.check_error(out))
        self.assertIn("Error with ML_RAG", json.loads(out)["error"])

    def test_ml_rag_call_error_short_circuit(self):
        @contextlib.contextmanager
        def cm(_cid):
            yield object()

        def exec_side_effect(conn, sql, params=None):
            if sql.startswith("SET @options"):
                return json.dumps(None)
            if sql.startswith("CALL sys.ML_RAG"):
                return json.dumps({"error": "ml_rag failed"})
            self.fail("SELECT @response should not be called")

        with mock.patch.object(
            m, "_get_database_connection_cm", new=cm
        ), mock.patch.object(m, "_execute_sql_tool", side_effect=exec_side_effect):
            out = m._ask_ml_rag_helper("cid", "Q", "JSON_OBJECT('skip_generate', true)")

        self.assertTrue(m.check_error(out))
        self.assertIn("Error with ML_RAG", json.loads(out)["error"])

    def test_fetch_response_error_short_circuit(self):
        @contextlib.contextmanager
        def cm(_cid):
            yield object()

        def exec_side_effect(conn, sql, params=None):
            if sql.startswith("SET @options"):
                return json.dumps(None)
            if sql.startswith("CALL sys.ML_RAG"):
                return json.dumps(None)
            if sql.startswith("SELECT @response"):
                return json.dumps({"error": "fetch failed"})
            self.fail("Unexpected SQL")

        with mock.patch.object(
            m, "_get_database_connection_cm", new=cm
        ), mock.patch.object(m, "_execute_sql_tool", side_effect=exec_side_effect):
            out = m._ask_ml_rag_helper("cid", "Q", "JSON_OBJECT('skip_generate', true)")

        self.assertTrue(m.check_error(out))
        self.assertIn("Error with ML_RAG", json.loads(out)["error"])

    def test_unexpected_response_format_from_fetch_one(self):
        @contextlib.contextmanager
        def cm(_cid):
            yield object()

        def exec_side_effect(conn, sql, params=None):
            if sql.startswith("SET @options"):
                return json.dumps(None)
            if sql.startswith("CALL sys.ML_RAG"):
                return json.dumps(None)
            if sql.startswith("SELECT @response"):
                # Multiple rows -> fetch_one should raise and be caught
                return json.dumps([["x"], ["y"]])
            self.fail("Unexpected SQL")

        with mock.patch.object(
            m, "_get_database_connection_cm", new=cm
        ), mock.patch.object(m, "_execute_sql_tool", side_effect=exec_side_effect):
            out = m._ask_ml_rag_helper("cid", "Q", "JSON_OBJECT('skip_generate', true)")

        self.assertTrue(m.check_error(out))
        self.assertIn("Unexpected response format", json.loads(out)["error"])

    def test_passes_correct_options_and_params(self):
        # Verifies that options_json_str is embedded in the CALL statement and question is passed as param
        @contextlib.contextmanager
        def cm(_cid):
            yield object()

        observed = {"rag_sql": None, "rag_params": None}

        def exec_side_effect(conn, sql, params=None):
            if sql.startswith("SET @options"):
                return json.dumps(None)
            if sql.startswith("CALL sys.ML_RAG"):
                observed["rag_sql"] = sql
                observed["rag_params"] = params
                return json.dumps(None)
            if sql.startswith("SELECT @response"):
                return json.dumps([["ok"]])
            self.fail("Unexpected SQL")

        options = "JSON_OBJECT('skip_generate', true, 'extra', 1)"
        with mock.patch.object(
            m, "_get_database_connection_cm", new=cm
        ), mock.patch.object(m, "_execute_sql_tool", side_effect=exec_side_effect):
            out = m._ask_ml_rag_helper("cid", "my-question", options)

        self.assertEqual(out, "ok")
        self.assertIsNotNone(observed["rag_sql"])
        self.assertIn(options, observed["rag_sql"])
        self.assertEqual(observed["rag_params"], ["my-question"])


class TestAskMlRagVectorStore(unittest.TestCase):

    @unittest.skipIf(SKIP_MYSQL_AI, MYSQL_AI_SKIP_MSG)
    def test_ask_ml_rag_vector_store_mysql_ai(self):
        conn_id = get_first_valid_connection_id(m.Mode.MYSQL_AI)

        files_json = src_module.list_vector_store_files_local(conn_id)
        self.assertFalse(
            src_module.check_error(files_json),
            f"list_vector_store_files_local error: {files_json}",
        )
        files = json.loads(files_json)
        self.assertIsInstance(files, list)
        self.assertGreaterEqual(
            len(files), 1, "Expected at least one file in secure_file_priv"
        )

        for fp in files:
            out = src_module.load_vector_store_local(conn_id, fp)
            self.assertFalse(
                src_module.check_error(out),
                f"load_vector_store_local failed for {fp}: {out}",
            )

        result = src_module.ask_ml_rag_vector_store(
            conn_id, "What documents are available?"
        )
        self.assertFalse(
            src_module.check_error(result), f"ask_ml_rag_vector_store failed: {result}"
        )
        self.assertIsInstance(result, str)


    def test_load_vector_store_oci_mode_not_oci(self):
        # _get_mode returns something that is not Mode.OCI
        with mock.patch.object(src_module, "_get_mode") as mock_get_mode:
            mock_get_mode.return_value = "MYSQL_AI"
            result = src_module.load_vector_store_oci(
                connection_id="myconn",
                namespace="ns",
                bucket_name="bucket",
                document_prefix="prefix/",
            )
        self.assertIn("Error with VECTOR_STORE_LOAD", result)
        self.assertIn("not OCI", result)
        self.assertIn("load_vector_store_local", result)

    def test_load_vector_store_oci_exception(self):
        # _get_mode raises an unexpected exception
        with mock.patch.object(src_module, "_get_mode") as mock_get_mode:
            mock_get_mode.side_effect = Exception("something bad happened")
            result = src_module.load_vector_store_oci(
                connection_id="myconn",
                namespace="ns",
                bucket_name="bucket",
                document_prefix="prefix/",
            )
        self.assertIn("Error with VECTOR_STORE_LOAD", result)
        self.assertIn("something bad happened", result)


class TestAskMlRagInnoDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.conn_id = get_first_valid_connection_id()

    def test_validation_error_for_bad_names(self):
        with mock.patch.object(
            src_module, "_validate_name", side_effect=ValueError("bad name")
        ):
            out = src_module.ask_ml_rag_innodb("cid", "Q", "seg", "emb")
        self.assertTrue(src_module.check_error(out))
        self.assertIn("Error validating names", json.loads(out)["error"])

    def test_delegates_to_helper_with_expected_options(self):
        observed = {"options": None, "question": None, "conn": None}

        def helper_spy(connection_id, question, options_json_str):
            observed["conn"] = connection_id
            observed["question"] = question
            observed["options"] = options_json_str
            return "ok"

        with mock.patch.object(
            src_module, "_validate_name", side_effect=lambda n: n
        ), mock.patch.object(src_module, "_ask_ml_rag_helper", side_effect=helper_spy):
            out = src_module.ask_ml_rag_innodb("cid", "Find docs", "body", "embedding")

        self.assertEqual(out, "ok")
        self.assertEqual(observed["conn"], "cid")
        self.assertEqual(observed["question"], "Find docs")
        self.assertIn("JSON_OBJECT('skip_generate', true", observed["options"])
        self.assertIn("'vector_store_columns'", observed["options"])
        self.assertIn("'segment', 'body'", observed["options"])
        self.assertIn("'segment_embedding', 'embedding'", observed["options"])

    def test_helper_error_bubbles_as_error_json(self):
        with mock.patch.object(
            src_module, "_validate_name", side_effect=lambda n: n
        ), mock.patch.object(
            src_module,
            "_ask_ml_rag_helper",
            return_value=json.dumps({"error": "ml_rag err"}),
        ):
            out = src_module.ask_ml_rag_innodb("cid", "Q", "body", "embedding")
        self.assertTrue(src_module.check_error(out))
        self.assertIn("ml_rag err", json.loads(out)["error"])

    def test_real_nonexistent_columns_error(self):
        # Choose a table name that likely doesn't exist or columns that don't exist
        # We call ask_ml_rag_innodb; it should return an error JSON via helper path when server rejects it.
        out = src_module.ask_ml_rag_innodb(
            self.conn_id,
            "What content is available?",
            "no_such_segment",
            "no_such_embedding",
        )
        self.assertTrue(
            src_module.check_error(out),
            f"Expected error when referencing nonexistent columns, got: {out}",
        )

    def test_real_success_on_populated_table(self):
        # Create a temp table, insert rows, ragify to create embeddings, then run ask_ml_rag_innodb.
        table = f"gc_innodb_{uuid.uuid4().hex[:8]}"
        segment_col = "body"
        embedding_col = "embedding"

        try:
            # Create table with primary key
            create_sql = f"CREATE TABLE {table} (id INT PRIMARY KEY AUTO_INCREMENT, {segment_col} TEXT)"
            out = src_module.execute_sql_tool_by_connection_id(self.conn_id, create_sql)
            self.assertFalse(src_module.check_error(out), f"create table failed: {out}")

            rows = [f"row {i}" for i in range(1, 6)]
            for r in rows:
                ins = src_module.execute_sql_tool_by_connection_id(
                    self.conn_id,
                    f"INSERT INTO {table} ({segment_col}) VALUES (%s)",
                    params=[r],
                )
                self.assertFalse(src_module.check_error(ins), f"insert failed: {ins}")

            # Ragify to create/populate embedding column
            res = src_module.ragify_column(
                self.conn_id, table, segment_col, embedding_col
            )
            self.assertFalse(
                src_module.check_error(res), f"ragify_column failed: {res}"
            )

            # Now query via ask_ml_rag_innodb
            out = src_module.ask_ml_rag_innodb(
                self.conn_id, "Find information across rows", segment_col, embedding_col
            )
            self.assertFalse(
                src_module.check_error(out), f"ask_ml_rag_innodb failed: {out}"
            )
            self.assertIsInstance(out, str)

            self.assertGreater(len(json.loads(out)['citations']), 0)
        finally:
            src_module.execute_sql_tool_by_connection_id(
                self.conn_id, f"DROP TABLE IF EXISTS {table}"
            )


class TestLoadVectorStoreLocalMocked(unittest.TestCase):
    def test_success_sets_autocommit_and_calls_execute(self):
        file_path = "/secure/dir/doc.pdf"
        prefixed = f"file://{file_path}"

        class FakeConn:
            def __init__(self):
                self.autocommit = False

        fake_conn = FakeConn()

        @contextlib.contextmanager
        def cm(_cid):
            yield fake_conn

        with mock.patch.object(
            src_module, "_get_mode", return_value=src_module.Mode.MYSQL_AI
        ), mock.patch.object(
            src_module, "_get_database_connection_cm", new=cm
        ), mock.patch.object(
            src_module, "_execute_sql_tool", return_value=json.dumps(None)
        ) as exec_mock:
            out = src_module.load_vector_store_local("cid", file_path)

        # Function now returns the JSON string from _execute_sql_tool
        self.assertIsInstance(out, str)
        self.assertFalse(m.check_error(out))
        self.assertIsNone(json.loads(out))
        # autocommit should be turned on before calling the procedure
        self.assertTrue(fake_conn.autocommit)
        # Ensure correct call with prefixed file path
        exec_mock.assert_called_once()
        args, kwargs = exec_mock.call_args
        self.assertIn("CALL sys.vector_store_load", args[1])
        self.assertEqual(kwargs["params"], [prefixed])

    def test_wrong_mode_returns_error_json(self):
        with mock.patch.object(
            src_module, "_get_mode", return_value=src_module.Mode.OCI
        ):
            out = src_module.load_vector_store_local("cid", "/a/b.txt")
        self.assertTrue(m.check_error(out))
        self.assertIn("not MySQL AI", json.loads(out)["error"])

    def test_execute_raises_returns_error_json(self):
        class FakeConn:
            def __init__(self):
                self.autocommit = False

        @contextlib.contextmanager
        def cm(_cid):
            yield FakeConn()

        with mock.patch.object(
            src_module, "_get_mode", return_value=src_module.Mode.MYSQL_AI
        ), mock.patch.object(
            src_module, "_get_database_connection_cm", new=cm
        ), mock.patch.object(
            src_module, "_execute_sql_tool", side_effect=RuntimeError("boom")
        ):
            out = src_module.load_vector_store_local("cid", "/secure/dir/file.txt")

        self.assertTrue(m.check_error(out))
        self.assertIn("boom", json.loads(out)["error"])

    def test_context_manager_exit_called(self):
        events = {"entered": False, "exited": False}

        class FakeConn:
            def __init__(self):
                self.autocommit = False

        @contextlib.contextmanager
        def cm(_cid):
            events["entered"] = True
            try:
                yield FakeConn()
            finally:
                events["exited"] = True

        with mock.patch.object(
            src_module, "_get_mode", return_value=src_module.Mode.MYSQL_AI
        ), mock.patch.object(
            src_module, "_get_database_connection_cm", new=cm
        ), mock.patch.object(
            src_module, "_execute_sql_tool", return_value=json.dumps(None)
        ):
            out = src_module.load_vector_store_local("cid", "/secure/dir/x")

        self.assertIsInstance(out, str)
        self.assertFalse(m.check_error(out))
        self.assertIsNone(json.loads(out))
        self.assertTrue(events["entered"])
        self.assertTrue(events["exited"])


class TestOciTools(unittest.TestCase):

    def test_list_all_compartments_unavailable(self):
        with mock.patch.object(src_module, "oci_error_msg", "error message"):
            result = src_module.list_all_compartments()
        self.assertEqual(result, "error message")

    def test_object_storage_list_buckets_unavailable(self):
        with mock.patch.object(src_module, "oci_error_msg", "error message"):
            result = src_module.object_storage_list_buckets("any-compartment")
        self.assertEqual(result, "error message")

    def test_object_storage_list_objects_unavailable(self):
        with mock.patch.object(src_module, "oci_error_msg", "error message"):
            result = src_module.object_storage_list_objects("ns", "bucket")
        self.assertEqual(result, "error message")

    def test_get_compartment_by_name_oci_info_none(self):
        with mock.patch.object(src_module, "oci_error_msg", "error message"):
            result = src_module._get_compartment_by_name("any-compartment")
        self.assertEqual(result, None)

    # ---- list_all_compartments error (identity error) ----
    def test_list_all_compartments_identity_error(self):
        mock_oci_info = mock.MagicMock()
        mock_identity_client = mock.MagicMock()
        mock_identity_client.list_compartments.side_effect = Exception(
            "OCI identity error: {'target_service': 'identity', 'status': 404, 'code': 'NotAuthorizedOrNotFound', 'message': 'Authorization failed or requested resource not found'}"
        )
        mock_oci_info.identity_client = mock_identity_client
        mock_oci_info.tenancy_id = "ocid1.tenancy.oc1..example"
        with mock.patch.object(src_module, "oci_info", mock_oci_info), \
            mock.patch.object(src_module, "oci_error_msg", None):
            result = src_module.list_all_compartments()
        self.assertIn("Error with list_compartments", result)
        self.assertIn("NotAuthorizedOrNotFound", result)
        self.assertIn("Authorization failed", result)

    def test_list_all_compartments_success(self):
        mock_oci_info = mock.MagicMock()
        # The result for list_compartments
        fake_compartment1 = mock.MagicMock()
        fake_compartment1.__repr__ = (
            lambda self=fake_compartment1: '{"id": "ocid1.compartment.oc1..abc", "name": "A"}'
        )
        # Updated list_all_compartments uses .id and .name attributes
        fake_compartment1.id = "ocid1.compartment.oc1..abc"
        fake_compartment1.name = "A"

        mock_identity_client = mock.MagicMock()
        mock_identity_client.list_compartments.return_value.data = [fake_compartment1]
        mock_oci_info.identity_client = mock_identity_client
        mock_oci_info.tenancy_id = "ocid1.tenancy.oc1..xyz"

        with mock.patch.object(src_module, "oci_info", mock_oci_info), \
            mock.patch.object(src_module, "oci_error_msg", None):
            result = src_module.list_all_compartments()
        # Only the list_compartments result should be present; get_compartment is not called
        self.assertIn("ocid1.compartment.oc1..abc", result)
        self.assertIn("A", result)
        mock_identity_client.get_compartment.assert_not_called()

    def test_list_all_compartments_does_not_call_get_compartment(self):
        mock_oci_info = mock.MagicMock()
        # list_compartments succeeds
        fake_compartment = mock.MagicMock()
        fake_compartment.__repr__ = (
            lambda self=fake_compartment: '{"id": "ocid1.compartment.oc1..abc", "name": "A"}'
        )
        # Updated list_all_compartments uses .id and .name attributes
        fake_compartment.id = "ocid1.compartment.oc1..abc"
        fake_compartment.name = "A"
        mock_identity_client = mock.MagicMock()
        mock_identity_client.list_compartments.return_value.data = [fake_compartment]
        # get_compartment should not be called; make it raise if it is
        mock_identity_client.get_compartment.side_effect = Exception("should not be called")
        mock_oci_info.identity_client = mock_identity_client
        mock_oci_info.tenancy_id = "ocid1.tenancy.oc1..xyz"

        with mock.patch.object(src_module, "oci_info", mock_oci_info), \
            mock.patch.object(src_module, "oci_error_msg", None):
            result = src_module.list_all_compartments()
        self.assertIn("ocid1.compartment.oc1..abc", result)
        self.assertNotIn("Error with get_compartment", result)
        mock_identity_client.get_compartment.assert_not_called()

    def test_list_all_compartments_access_report_includes_object_storage_success(self):
        mock_oci_info = mock.MagicMock()
        # One accessible compartment
        fake_compartment = mock.MagicMock()
        fake_compartment.name = "CompA"
        fake_compartment.id = "ocid1.compartment.oc1..compa"

        mock_identity_client = mock.MagicMock()
        mock_identity_client.list_compartments.return_value.data = [fake_compartment]

        mock_oci_info.identity_client = mock_identity_client
        mock_oci_info.tenancy_id = "ocid1.tenancy.oc1..xyz"

        # Object storage access succeeds
        mock_oci_info.object_storage_client.get_namespace.return_value.data = "ns"
        mock_oci_info.object_storage_client.list_buckets.return_value = mock.MagicMock()

        with mock.patch.object(src_module, "oci_info", mock_oci_info), \
            mock.patch.object(src_module, "oci_error_msg", None):
            result = src_module.list_all_compartments()

        # Result is a stringified dict; assert expected substrings
        self.assertIn("CompA", result)
        self.assertIn("ocid1.compartment.oc1..compa", result)
        self.assertIn("'object_storage': True", result)
        self.assertIn("'databases': False", result)
        # No error strings expected when object storage succeeds
        self.assertNotIn("Object Storage:", result)

    def test_list_all_compartments_access_report_records_errors_on_object_storage_failure(self):
        mock_oci_info = mock.MagicMock()
        # One accessible compartment
        fake_compartment = mock.MagicMock()
        fake_compartment.name = "CompB"
        fake_compartment.id = "ocid1.compartment.oc1..compb"

        mock_identity_client = mock.MagicMock()
        mock_identity_client.list_compartments.return_value.data = [fake_compartment]

        mock_oci_info.identity_client = mock_identity_client
        mock_oci_info.tenancy_id = "ocid1.tenancy.oc1..xyz"

        # Force get_namespace to fail -> should record error and leave object_storage False
        mock_oci_info.object_storage_client.get_namespace.side_effect = Exception("boom ns")

        with mock.patch.object(src_module, "oci_info", mock_oci_info), \
            mock.patch.object(src_module, "oci_error_msg", None):
            result = src_module.list_all_compartments()

        self.assertIn("CompB", result)
        self.assertIn("ocid1.compartment.oc1..compb", result)
        self.assertIn("'object_storage': False", result)
        self.assertIn("Object Storage: boom ns", result)

    # ---- object_storage_list_buckets error: missing compartment id ----
    def test_object_storage_list_buckets_missing_compartmentid(self):
        mock_oci_info = mock.MagicMock()
        err_msg = "{\"error\": \"Error listing buckets: {'target_service': 'object_storage', 'status': 400, 'code': 'MissingCompartmentId', 'message': \"The 'compartmentId' query parameter was missing\"}\"}"
        # Simulate failure on get_namespace (or list_buckets)
        mock_oci_info.object_storage_client.get_namespace.return_value.data = "ns"
        mock_oci_info.object_storage_client.list_buckets.side_effect = Exception(
            "{'target_service': 'object_storage', 'status': 400, 'code': 'MissingCompartmentId', 'message': \"The 'compartmentId' query parameter was missing\"}"
        )
        with mock.patch.object(src_module, "oci_info", mock_oci_info), \
            mock.patch.object(src_module, "oci_error_msg", None):
            result = src_module.object_storage_list_buckets("any-compartment")
        self.assertIn("Error listing buckets", result)
        self.assertIn("MissingCompartmentId", result)

    # ---- object_storage_list_buckets error: NotAuthorizedOrNotFound on get_compartment ----
    def test_object_storage_list_buckets_authorization_error_on_get_compartment(self):
        mock_oci_info = mock.MagicMock()
        fake_compartment = mock.MagicMock()
        fake_compartment.name = "mysql-genai"
        # Simulate _get_compartment_by_name triggers an exception (via side effect in our setup)
        with mock.patch.object(
            src_module,
            "_get_compartment_by_name",
            side_effect=Exception(
                "{'target_service': 'identity', 'status': 404, 'code': 'NotAuthorizedOrNotFound', 'message': 'Authorization failed or requested resource not found'}"
            ),
        ):
            with mock.patch.object(src_module, "oci_info", mock_oci_info), \
                mock.patch.object(src_module, "oci_error_msg", None):
                result = src_module.object_storage_list_buckets(
                    compartment_name="mysql-genai"
                )
            self.assertIn("Error listing buckets", result)
            self.assertIn("NotAuthorizedOrNotFound", result)

    # ---- object_storage_list_buckets NamespaceNotFound ----
    def test_object_storage_list_buckets_namespace_not_found(self):
        mock_oci_info = mock.MagicMock()
        mock_oci_info.object_storage_client.get_namespace.return_value.data = "mysqlpm"
        mock_oci_info.object_storage_client.list_buckets.side_effect = Exception(
            "{'target_service': 'object_storage', 'status': 404, 'code': 'NamespaceNotFound', 'message': 'You do not have authorization to perform this request, or the requested resource could not be found.'}"
        )
        with mock.patch.object(src_module, "oci_info", mock_oci_info), \
            mock.patch.object(src_module, "oci_error_msg", None):
            result = src_module.object_storage_list_buckets(
                compartment_id="ocid1.compartment.oc1..unauth"
            )
        self.assertIn("Error listing buckets", result)
        self.assertIn("NamespaceNotFound", result)
        self.assertIn("authorization to perform this request", result)

    # ---- object_storage_list_buckets success/exact list ----
    def test_object_storage_list_buckets_success(self):
        mock_oci_info = mock.MagicMock()
        bucket1 = mock.MagicMock()
        bucket1.name = "bucket-chicago-sp1"
        bucket1.__repr__ = lambda self=bucket1: '{"name": "bucket-chicago-sp1"}'
        bucket2 = mock.MagicMock()
        bucket2.name = "nl2ml-bucket-chicago"
        bucket2.__repr__ = lambda self=bucket2: '{"name": "nl2ml-bucket-chicago"}'
        mock_oci_info.object_storage_client.get_namespace.return_value.data = "mysqlpm"
        mock_oci_info.object_storage_client.list_buckets.return_value.data = [
            bucket1,
            bucket2,
        ]
        with mock.patch.object(src_module, "oci_info", mock_oci_info), \
            mock.patch.object(src_module, "oci_error_msg", None):
            result = src_module.object_storage_list_buckets(
                compartment_id="ocid1.compartment.oc1..success"
            )
        self.assertIn("bucket-chicago-sp1", result)
        self.assertIn("nl2ml-bucket-chicago", result)

    def test_object_storage_list_buckets_resolve_name_success(self):
        # Set up a compartment that matches the name
        compartment_name = "MySQL-GenAI"
        fake_compartment = mock.MagicMock()
        fake_compartment.id = "ocid1.compartment.oc1..mysqlgenai"
        fake_compartment.name = "MYSQL-GENAI"

        mock_oci_info = mock.MagicMock()
        mock_identity_client = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_result.data = [fake_compartment]
        mock_identity_client.list_compartments.return_value = mock_result
        mock_identity_client.get_compartment.return_value.data = fake_compartment
        mock_oci_info.identity_client = mock_identity_client

        fake_bucket = mock.MagicMock()
        fake_bucket.__repr__ = lambda self=fake_bucket: "bucket1"
        mock_oci_info.object_storage_client.list_buckets.return_value.data = [
            fake_bucket
        ]
        mock_oci_info.tenancy_id = "ocid1.tenancy.oc1..foo"

        with mock.patch.object(src_module, "oci_info", mock_oci_info), \
            mock.patch.object(src_module, "oci_error_msg", None):
            result = src_module.object_storage_list_buckets(
                compartment_name=compartment_name
            )

        self.assertIn("bucket1", result)

    # ---- object_storage_list_objects success/minimal set ----
    def test_object_storage_list_objects_success(self):
        mock_oci_info = mock.MagicMock()
        obj1 = mock.MagicMock()
        obj1.name = "mysql-en-ml-9.2.0.pdf"
        obj1.__repr__ = lambda self=obj1: '{"name": "mysql-en-ml-9.2.0.pdf"}'
        obj2 = mock.MagicMock()
        obj2.name = "history_docs/24 Hours of Le Mans - Wikipedia.pdf"
        obj2.__repr__ = (
            lambda self=obj2: '{"name": "history_docs/24 Hours of Le Mans - Wikipedia.pdf"}'
        )
        list_object_response = mock.MagicMock()
        list_object_response.data.objects = [obj1, obj2]
        mock_oci_info.object_storage_client.list_objects.return_value = (
            list_object_response
        )
        with mock.patch.object(src_module, "oci_info", mock_oci_info), \
            mock.patch.object(src_module, "oci_error_msg", None):
            result = src_module.object_storage_list_objects(
                "mysqlpm", "nl2ml-bucket-chicago"
            )
        self.assertIn("mysql-en-ml-9.2.0.pdf", result)
        self.assertIn("Le Mans", result)

    # ---- object_storage_list_objects error ----
    def test_object_storage_list_objects_error(self):
        mock_oci_info = mock.MagicMock()
        mock_oci_info.object_storage_client.list_objects.side_effect = Exception(
            "Error with listing objects in a specified bucket: fake failure"
        )
        with mock.patch.object(src_module, "oci_info", mock_oci_info), \
            mock.patch.object(src_module, "oci_error_msg", None):
            result = src_module.object_storage_list_objects("mysqlpm", "bad-bucket")
        self.assertIn("Error with listing objects", result)
        self.assertIn("fake failure", result)


class TestFillConfigDefaults(unittest.TestCase):
    def _base_server(self):
        return {
            "host": "h",
            "user": "u",
            "password": "p",
            "database": "d",
            "port": 3306,
        }

    def test_empty_server_infos_raises(self):
        cfg = {"server_infos": {}}
        with self.assertRaises(Exception) as ctx:
            fill_config_defaults(cfg)
        self.assertIn("at least one server", str(ctx.exception))

    def test_server_info_missing_required_keys_raises(self):
        cfg = {"server_infos": {"c1": {"host": "h", "user": "u", "password": "p", "database": "d"}}}  # missing port
        with self.assertRaises(Exception) as ctx:
            fill_config_defaults(cfg)
        self.assertIn("must specify all of the following keys", str(ctx.exception))

    def test_bastion_defaults_applied(self):
        cfg = {
            "server_infos": {"c1": self._base_server()},
            "bastion": {
                "bastion_host": "bhost",
                "bastion_username": "buser",
                "private_key_path": "/path/key",
                "db_host": "db.remote",
            },
        }
        out = fill_config_defaults(cfg)
        b = out["bastion"]
        # Ensure defaults are present
        self.assertEqual(b["bastion_port"], 22)
        self.assertEqual(b["db_port"], 3306)
        self.assertEqual(b["local_bind_host"], "127.0.0.1")
        self.assertEqual(b["local_bind_port"], 3306)
        # Ensure the full allowed key set is present (no extras, no missing)
        expected_keys = {
            "bastion_host",
            "bastion_username",
            "private_key_path",
            "db_host",
            "db_port",
            "bastion_port",
            "local_bind_host",
            "local_bind_port",
        }
        self.assertEqual(set(b.keys()), expected_keys)

    def test_bastion_missing_required_key_raises(self):
        cfg = {
            "server_infos": {"c1": self._base_server()},
            "bastion": {
                "bastion_host": "bhost",
                "bastion_username": "buser",
                "private_key_path": "/path/key",
                # missing db_host
            },
        }
        with self.assertRaises(Exception) as ctx:
            fill_config_defaults(cfg)
        self.assertIn("Config bastion", str(ctx.exception))


class TestGetSshCommand(unittest.TestCase):
    def _base_server(self):
        return {
            "host": "h",
            "user": "u",
            "password": "p",
            "database": "d",
            "port": 3306,
        }

    def test_get_ssh_command_returns_none_when_missing(self):
        cfg = {"server_infos": {"c1": self._base_server()}}
        result = get_ssh_command(cfg)
        self.assertIsNone(result)

    def test_get_ssh_command_returns_expected_command(self):
        bastion = {
            "bastion_host": "bhost",
            "bastion_username": "buser",
            "private_key_path": "/path/key",
            "db_host": "db.remote",
            "bastion_port": 2222,
            "db_port": 3307,
            "local_bind_host": "127.0.0.2",
            "local_bind_port": 4400,
        }

        cfg = {"server_infos": {"c1": self._base_server()}, "bastion": bastion}
        result = get_ssh_command(cfg)

        expected_ssh_command = (
            f'`ssh -i {bastion["private_key_path"]} '
            f'-p {bastion["bastion_port"]} '
            f'-L {bastion["local_bind_host"]}:{bastion["local_bind_port"]}:{bastion["db_host"]}:{bastion["db_port"]} '
            '-o ServerAliveInterval=60 '
            '-o ServerAliveCountMax=3 '
            '-N '
            f'{bastion["bastion_username"]}@{bastion["bastion_host"]}`'
        )

        self.assertEqual(result, expected_ssh_command)


class TestHeatwaveAskHelp(unittest.TestCase):
    def test_heatwave_ask_help_success_mocked(self):
        # Mode must be OCI and NL2ML returns a single-row scalar JSON string
        with mock.patch.object(src_module, "_get_mode", return_value=src_module.Mode.OCI), \
             mock.patch.object(src_module, "_execute_sql_tool", return_value=json.dumps([[json.dumps({"text": "ok"})]])):
            out = src_module.heatwave_ask_help("cid", "Q")
        self.assertFalse(src_module.check_error(out))
        self.assertIsInstance(out, str)
        self.assertIn('"text"', out)

    def test_heatwave_ask_help_mode_not_oci_mocked(self):
        # Non-OCI connections should return an error JSON
        with mock.patch.object(src_module, "_get_mode", return_value=src_module.Mode.MYSQL_AI):
            out = src_module.heatwave_ask_help("cid", "Q")
        self.assertTrue(src_module.check_error(out))
        self.assertIn("does not support NL2ML", json.loads(out)["error"])

    def test_heatwave_ask_help_execute_returns_error_mocked(self):
        # If the NL2ML call returns an error JSON, it should be surfaced
        with mock.patch.object(src_module, "_get_mode", return_value=src_module.Mode.OCI), \
             mock.patch.object(src_module, "_execute_sql_tool", return_value=json.dumps({"error": "forced"})):
            out = src_module.heatwave_ask_help("cid", "Q")
        self.assertTrue(src_module.check_error(out))
        self.assertIn("forced", json.loads(out)["error"])

    def test_heatwave_ask_help_unexpected_rowcount_error_mocked(self):
        # Multiple rows cause fetch_one to raise; tool should return an NL2ML error JSON
        with mock.patch.object(src_module, "_get_mode", return_value=src_module.Mode.OCI), \
             mock.patch.object(src_module, "_execute_sql_tool", return_value=json.dumps([["x"], ["y"]])):
            out = src_module.heatwave_ask_help("cid", "Q")
        self.assertTrue(src_module.check_error(out))
        self.assertIn("Error with NL2ML", json.loads(out)["error"])

    @unittest.skipIf(SKIP_OCI, OCI_SKIP_MSG)
    def test_heatwave_ask_help_real_query(self):
        # Issues a real NL2ML query against an OCI-mode connection
        conn_id = get_first_valid_connection_id(m.Mode.OCI)
        out = src_module.heatwave_ask_help(conn_id, "Give me a training query for email spam detection.")
        self.assertFalse(src_module.check_error(out), f"heatwave_ask_help failed: {out}")
        self.assertIsInstance(out, str)


if __name__ == "__main__":
    unittest.main()
