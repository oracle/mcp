"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import call, patch

from pydantic import ValidationError

# Ensure module-level config in server.py can initialize during import
os.environ.setdefault("OGG_BASE_URL", "https://example.com")
os.environ.setdefault("OGG_USERNAME", "user")
os.environ.setdefault("OGG_PASSWORD", "pass")

from oracle.oracle_goldengate_mcp_server import server  # noqa: E402
from oracle.oracle_goldengate_mcp_server.models import (  # noqa: E402
    CreateExtractBegin,
    CreateExtractOptions,
    CreateExtractSource,
    CreateReplicatBegin,
    CreateReplicatOptions,
    CreateReplicatSource,
    ExtractAdvancedParameters,
    ReplicatAdvancedParameters,
)


class TestGoldenGateTools(unittest.TestCase):
    def _initial_load_responses(self):
        status = {
            "status": "stopped", "processId": 123,
            "lastStarted": "2026-10-23T10:00:00Z",
        }
        return {
            server.api.get_extract_status("E_INIT"): status,
            server.api.get_extract_details("E_INIT"): {"source": "tables", "config": ["EXTFILE I1, PURGE"]},
            server.api.get_replicat_details("R_INIT"): {"source": {"name": "I1"}},
            server.api.get_extract_history("E_INIT"): {"history": [{
                "status": "stopped", "processId": 123, "exitCode": 0,
                "started": "2026-10-23T10:00:00Z", "finished": "2026-10-23T10:01:00Z",
            }]},
            server.api.get_extract_report("E_INIT"): "Process id: 123\nInitial Load Extract processing complete.",
        }

    def _assert_json(self, actual: str, expected: dict):
        self.assertEqual(json.loads(actual), expected)

    def test_ok_redacts_sensitive_tool_output(self):
        output = server._ok(
            {
                "status": "failed",
                "password": "top-secret",
                "report": "USERID app, PASSWORD report-secret",
            }
        )
        self.assertNotIn("top-secret", output)
        self.assertNotIn("report-secret", output)
        self.assertIn("[REDACTED]", output)

    def test_log_startup_writes_file_and_ignores_file_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "startup.log")
            with patch.dict(os.environ, {"GG_MCP_LOG_FILE": log_file}), patch("sys.stderr") as stderr:
                server._log_startup("INFO", "hello PASSWORD secret")
                stderr.write.assert_not_called()
            with open(log_file, encoding="utf-8") as f:
                content = f.read()
                self.assertIn("[INFO] hello", content)
                self.assertNotIn("secret", content)

        with patch.dict(os.environ, {"GG_MCP_LOG_FILE": "/no/such/dir/startup.log"}), patch("sys.stderr") as stderr:
            server._log_startup("INFO", "fallback")
            self.assertTrue(stderr.write.called)

    def test_verify_deployment_connectivity_success(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as get, patch.object(
            server, "_log_startup"
        ) as log:
            server._verify_deployment_connectivity()

        get.assert_called_once_with(server.api.list_domains())
        self.assertEqual(log.call_args_list[-1].args[0], "INFO")
        self.assertIn("Successfully connected", log.call_args_list[-1].args[1])

    def test_verify_deployment_connectivity_logs_401_details(self):
        with (
            patch.object(server.client, "get", side_effect=RuntimeError("401 Unauthorized")),
            patch.object(server, "_log_startup") as log,
            self.assertRaises(RuntimeError),
        ):
            server._verify_deployment_connectivity()

        messages = [call.args[1] for call in log.call_args_list]
        self.assertTrue(any("Authentication to the GoldenGate deployment failed" in msg for msg in messages))

    def test_resolve_begin_value_variants(self):
        self.assertEqual(server._resolve_begin_value(None), "now")
        self.assertEqual(server._resolve_begin_value("  "), "now")
        self.assertEqual(server._resolve_begin_value("2026-04-21T10:33:00Z"), "2026-04-21T10:33:00Z")
        self.assertEqual(server._resolve_begin_value(CreateReplicatBegin(sequence=2, offset=9)), {"sequence": 2, "offset": 9})
        self.assertEqual(server._resolve_begin_value({"sequence": 1}), {"sequence": 1})

    def test_list_domains(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.list_domains()
            m.assert_called_once_with(server.api.list_domains())
            self._assert_json(out, {"ok": True})

    def test_list_connections(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.list_connections("OracleGoldenGate")
            m.assert_called_once_with(server.api.list_connections("OracleGoldenGate"))
            self._assert_json(out, {"ok": True})

    def test_list_checkpoint_tables(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.list_checkpoint_tables("D", "C")
            self.assertIn(server.api.list_checkpoint_tables("D", "C"), m.call_args.args)
            self._assert_json(out, {"ok": True})

    def test_list_extracts(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.list_extracts()
            m.assert_called_once_with(server.api.list_extracts())
            self._assert_json(out, {"ok": True})

    def test_list_replicats(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.list_replicats()
            m.assert_called_once_with(server.api.list_replicats())
            self._assert_json(out, {"ok": True})

    def test_list_distribution_paths(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.list_distribution_paths()
            m.assert_called_once_with(server.api.list_distribution_paths())
            self._assert_json(out, {"ok": True})

    def test_list_data_streams(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.list_data_streams()
            m.assert_called_once_with(server.api.list_data_streams())
            self._assert_json(out, {"ok": True})

    def test_list_trails(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.list_trails()
            m.assert_called_once_with(server.api.list_trails())
            self._assert_json(out, {"ok": True})

    def test_get_extract_status(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.get_extract_status("E1")
            m.assert_called_once_with(server.api.get_extract_status("E1"))
            self._assert_json(out, {"ok": True})

    def test_get_replicat_status(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.get_replicat_status("R1")
            m.assert_called_once_with(server.api.get_replicat_status("R1"))
            self._assert_json(out, {"ok": True})

    def test_create_connection(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_connection("conn", "user", "pwd", "OracleGoldenGate")
            self.assertEqual(m.call_args.args[0], server.api.create_connection("OracleGoldenGate", "conn", "user", "pwd"))
            self._assert_json(out, {"ok": True})

    def test_create_connection_defaults_domain(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_connection("conn", "user", "pwd", " ")
            self.assertEqual(m.call_args.args[0], server.api.create_connection(server.DEFAULT_DOMAIN, "conn", "user", "pwd"))
            self._assert_json(out, {"ok": True})

    def test_add_trandata_schema_and_table_payloads(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.add_trandata_schema("D", "C", "HR")
            m.assert_called_once_with(
                server.api.add_trandata_schema("D", "C"),
                {
                    "schemaName": "HR",
                    "nonvalidatedKeysAllowed": False,
                    "schedulingColumns": True,
                    "allColumns": False,
                    "prepareCsnMode": "nowait",
                    "operation": "add",
                },
            )
            self._assert_json(out, {"ok": True})

        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.add_trandata_table("D", "C", "HR", "EMP")
            m.assert_called_once_with(
                server.api.add_trandata_table("D", "C"),
                {
                    "tableName": "HR.EMP",
                    "primaryKey": True,
                    "schedulingColumns": True,
                    "allColumns": False,
                    "prepareCsnMode": "nowait",
                    "operation": "add",
                },
            )
            self._assert_json(out, {"ok": True})

    def test_add_trandata_schema_supports_custom_logging_options(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.add_trandata_schema(
                "D",
                "C",
                "YAN_POS",
                nonvalidatedKeysAllowed=True,
                schedulingColumns=False,
                allColumns=True,
                prepareCsnMode="wait",
            )
            m.assert_called_once_with(
                server.api.add_trandata_schema("D", "C"),
                {
                    "schemaName": "YAN_POS",
                    "nonvalidatedKeysAllowed": True,
                    "schedulingColumns": False,
                    "allColumns": True,
                    "prepareCsnMode": "wait",
                    "operation": "add",
                },
            )
            self._assert_json(out, {"ok": True})

    def test_add_trandata_table_supports_custom_logging_options(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.add_trandata_table(
                "D",
                "C",
                "HR",
                "EMP",
                primaryKey=False,
                schedulingColumns=False,
                allColumns=True,
                prepareCsnMode="wait",
            )
            m.assert_called_once_with(
                server.api.add_trandata_table("D", "C"),
                {
                    "tableName": "HR.EMP",
                    "primaryKey": False,
                    "schedulingColumns": False,
                    "allColumns": True,
                    "prepareCsnMode": "wait",
                    "operation": "add",
                },
            )
            self._assert_json(out, {"ok": True})

    def test_create_extract(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_extract("E1", "AA", "D", "C", tableStatement="TABLE S.T;", advanced=None)
            self.assertEqual(m.call_args.args[0], server.api.create_extract("E1"))
            self.assertEqual(
                m.call_args.args[1]["managedProcessSettings"],
                server.DEFAULT_MANAGED_PROCESS_SETTINGS,
            )
            self.assertIn(server.DEFAULT_REPORTCOUNT_PARAMETER, m.call_args.args[1]["config"])
            self.assertIn(server.DEFAULT_WARNLONGTRANS_PARAMETER, m.call_args.args[1]["config"])
            self._assert_json(out, {"ok": True})

    def test_create_extract_defaults_begin_to_now(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            server.create_extract("E1", "AA", "D", "C", tableStatement="TABLE S.T;", advanced=None)
            self.assertEqual(m.call_args.args[1]["begin"], "now")

    def test_create_extract_accepts_timestamp_begin(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            server.create_extract(
                "E1",
                "AA",
                "D",
                "C",
                tableStatement="TABLE S.T;",
                begin="2026-04-21T10:33:00+02:00",
                advanced=None,
            )
            self.assertEqual(m.call_args.args[1]["begin"], "2026-04-21T10:33:00+02:00")

    def test_create_extract_accepts_csn_begin(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            server.create_extract(
                "E1",
                "AA",
                "D",
                "C",
                tableStatement="TABLE S.T;",
                begin=CreateExtractBegin(at={"csn": 11}),
                advanced=None,
            )
            self.assertEqual(m.call_args.args[1]["begin"], {"at": {"csn": 11}})

    def test_create_extract_does_not_duplicate_advanced_monitoring_parameters(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            server.create_extract(
                "E1",
                "AA",
                "D",
                "C",
                tableStatement="TABLE S.T;",
                advanced=ExtractAdvancedParameters(
                    reportCount={"every": "10 MINUTES", "rate": True},
                    additionalParameters=["WARNLONGTRANS 2H, CHECKINTERVAL 15M"],
                ),
            )

        config = m.call_args.args[1]["config"]
        self.assertEqual(sum(1 for line in config if line.startswith("REPORTCOUNT")), 1)
        self.assertEqual(sum(1 for line in config if line.startswith("WARNLONGTRANS")), 1)
        self.assertIn("REPORTCOUNT EVERY 10 MINUTES, RATE", config)
        self.assertIn("WARNLONGTRANS 2H, CHECKINTERVAL 15M", config)

    def test_create_initial_load_extract(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_initial_load_extract("E1", "AA", "D", "C", tableStatement="TABLE S.T;")

        self.assertEqual(m.call_args.args[0], server.api.create_extract("E1"))
        payload = m.call_args.args[1]
        self.assertEqual(payload["status"], "stopped")
        self.assertEqual(payload["managedProcessSettings"], server.DEFAULT_MANAGED_PROCESS_SETTINGS)
        self.assertEqual(payload["encryptionProfile"], "LocalWallet")
        self.assertEqual(payload["source"], "tables")
        self.assertEqual(
            payload["config"],
            [
                "--- Auto generated Parameter File, do not edit ---",
                "EXTRACT E1",
                "--- End of auto generated Parameter File ---",
                "USERIDALIAS C DOMAIN D",
                "EXTFILE AA, PURGE",
                "TABLE S.T;",
            ],
        )
        self.assertNotIn("targets", payload)
        self.assertNotIn("begin", payload)
        self.assertNotIn("credentials", payload)
        self._assert_json(out, {"ok": True})

    def test_create_initial_load_extract_builds_structured_source(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_initial_load_extract(
                "E1",
                "AA",
                "D",
                "C",
                source=CreateExtractSource(schema="S", table="T"),
                options=CreateExtractOptions(cols=["ID", "NAME"]),
                encryptionProfile="CustomWallet",
            )

        payload = m.call_args.args[1]
        self.assertEqual(payload["encryptionProfile"], "CustomWallet")
        self.assertIn("TABLE S.T, COLS (ID, NAME);", payload["config"])
        self.assertIn("EXTFILE AA, PURGE", payload["config"])
        self._assert_json(out, {"ok": True})

    def test_create_initial_load_extract_supports_sqlpredicate_as_of_scn(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_initial_load_extract(
                "E1",
                "AA",
                "D",
                "C",
                source=CreateExtractSource(schema="hr", table="*"),
                options=CreateExtractOptions(sqlPredicate="AS OF SCN 168298293"),
            )

        payload = m.call_args.args[1]
        self.assertIn("TABLE hr.*, SQLPREDICATE 'AS OF SCN 168298293';", payload["config"])
        self._assert_json(out, {"ok": True})

    def test_create_initial_load_extract_supports_dedicated_as_of_scn(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_initial_load_extract(
                "E1",
                "AA",
                "D",
                "C",
                source=CreateExtractSource(schema="hr", table="*"),
                asOfScn=168298293,
            )

        payload = m.call_args.args[1]
        self.assertIn("TABLE hr.*, SQLPREDICATE 'AS OF SCN 168298293';", payload["config"])
        self._assert_json(out, {"ok": True})

    def test_create_initial_load_extract_rejects_duplicate_snapshot_predicates(self):
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            server.create_initial_load_extract(
                "E1",
                "AA",
                "D",
                "C",
                source=CreateExtractSource(schema="hr", table="*"),
                options=CreateExtractOptions(sqlPredicate="AS OF SCN 168298293"),
                asOfScn=168298293,
            )

    def test_create_initial_load_extract_adds_as_of_scn_to_raw_statements(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as post:
            out = server.create_initial_load_extract(
                "E1",
                "AA",
                "D",
                "C",
                tableStatement="TABLE hr.employees; TABLE hr.departments;",
                asOfScn=168298293,
            )

        payload = post.call_args.args[1]
        self.assertIn(
            "TABLE hr.employees, SQLPREDICATE 'AS OF SCN 168298293';\n"
            "TABLE hr.departments, SQLPREDICATE 'AS OF SCN 168298293';",
            payload["config"],
        )
        self._assert_json(out, {"ok": True})

    def test_create_initial_load_extract_rejects_duplicate_raw_sqlpredicate(self):
        with self.assertRaisesRegex(ValueError, "already contains SQLPREDICATE"):
            server.create_initial_load_extract(
                "E1",
                "AA",
                "D",
                "C",
                tableStatement="TABLE hr.*, SQLPREDICATE 'WHERE ID > 0';",
                asOfScn=168298293,
            )

    def test_update_extract(self):
        with patch.object(server.client, "patch", return_value={"ok": True}) as m:
            out = server.update_extract("E1", trailName="AA", domainName="D", connectionName="C", tableStatement="TABLE S.T;", advanced=None)
            self.assertEqual(m.call_args.args[0], server.api.update_extract("E1"))
            self.assertEqual(
                m.call_args.args[1]["managedProcessSettings"],
                server.DEFAULT_MANAGED_PROCESS_SETTINGS,
            )
            self._assert_json(out, {"ok": True})

    def test_update_extract_builds_structured_source_and_exttrail_target(self):
        with patch.object(server.client, "patch", return_value={"ok": True}) as m:
            out = server.update_extract(
                "E1",
                trailName="AA",
                domainName="D",
                connectionName="C",
                source=CreateExtractSource(schema="S", table="T"),
                options=CreateExtractOptions(targetDef="target.def"),
                advanced=ExtractAdvancedParameters(extTrail="BB"),
            )

        self._assert_json(out, {"ok": True})
        payload = m.call_args.args[1]
        self.assertIn("TABLE S.T, TARGETDEF target.def;", payload["config"])
        self.assertEqual(payload["targets"], [{"name": "BB"}])
        self.assertEqual(payload["begin"], "now")
        self.assertEqual(payload["credentials"], {"domain": "D", "alias": "C"})

    def test_create_replicat(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_replicat("R1", "AA", "D", "C", mapStatement="MAP S.T, TARGET S2.T2;", advanced=None)
            self.assertEqual(m.call_args.args[0], server.api.create_replicat("R1"))
            self.assertEqual(
                m.call_args.args[1]["managedProcessSettings"],
                server.DEFAULT_MANAGED_PROCESS_SETTINGS,
            )
            self._assert_json(out, {"ok": True})

    def test_create_replicat_requires_map_statement_or_source(self):
        with self.assertRaises(ValueError):
            server.create_replicat("R1", "AA", "D", "C")

    def test_create_replicat_with_structured_source_checkpoint_and_parallel_mode(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_replicat(
                "R1",
                "AA",
                "D",
                "C",
                source=CreateReplicatSource(schema="S", table="T", targetTable="D.T"),
                options=CreateReplicatOptions(targetDef="target.def"),
                advanced=ReplicatAdvancedParameters(
                    credential="USERIDALIAS TARGET DOMAIN D",
                    checkpointTable="D.CHKPT",
                    modeType="parallel",
                    modeParallel=True,
                    additionalParameters=["ASSUMETARGETDEFS"],
                ),
            )

        self._assert_json(out, {"ok": True})
        payload = m.call_args.args[1]
        self.assertIn("USERIDALIAS TARGET DOMAIN D", payload["config"])
        self.assertIn(server.DEFAULT_REPORTCOUNT_PARAMETER, payload["config"])
        self.assertIn("MAP S.T, TARGET D.T, TARGETDEF target.def;", payload["config"])
        self.assertEqual(payload["checkpoint"], {"table": "D.CHKPT"})
        self.assertEqual(payload["mode"], {"type": "parallel", "parallel": True})
        self.assertNotIn("source", payload)
        self.assertNotIn("credentials", payload)

    def test_create_replicat_defaults_begin_to_now(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            server.create_replicat("R1", "AA", "D", "C", mapStatement="MAP S.T, TARGET S2.T2;", advanced=None)
            self.assertEqual(m.call_args.args[1]["begin"], "now")

    def test_create_replicat_does_not_duplicate_advanced_reportcount(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            server.create_replicat(
                "R1",
                "AA",
                "D",
                "C",
                mapStatement="MAP S.T, TARGET S2.T2;",
                advanced=ReplicatAdvancedParameters(additionalParameters=["REPORTCOUNT EVERY 5 MINUTES, RATE"]),
            )

        config = m.call_args.args[1]["config"]
        self.assertEqual(sum(1 for line in config if line.startswith("REPORTCOUNT")), 1)
        self.assertIn("REPORTCOUNT EVERY 5 MINUTES, RATE", config)

    def test_create_replicat_accepts_timestamp_begin(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            server.create_replicat(
                "R1",
                "AA",
                "D",
                "C",
                mapStatement="MAP S.T, TARGET S2.T2;",
                begin="2026-04-21T10:33:00+02:00",
                advanced=None,
            )
            self.assertEqual(m.call_args.args[1]["begin"], "2026-04-21T10:33:00+02:00")

    def test_create_replicat_accepts_trail_position_begin(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            server.create_replicat(
                "R1",
                "AA",
                "D",
                "C",
                mapStatement="MAP S.T, TARGET S2.T2;",
                begin=CreateReplicatBegin(sequence=145, offset=5),
                advanced=None,
            )
            self.assertEqual(m.call_args.args[1]["begin"], {"sequence": 145, "offset": 5})

    def test_create_replicat_accepts_top_level_checkpoint_table(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            server.create_replicat(
                "R1",
                "AA",
                "D",
                "C",
                mapStatement="MAP S.T, TARGET S2.T2;",
                checkpointTable='"SRCMIRROR_OCIGGLL"."CHECKTABLE"',
                advanced=None,
            )
            payload = m.call_args.args[1]
            self.assertEqual(payload["checkpoint"], {"table": '"SRCMIRROR_OCIGGLL"."CHECKTABLE"'})
            self.assertNotIn('CHECKPOINTTABLE "SRCMIRROR_OCIGGLL"."CHECKTABLE"', payload["config"])

    def test_create_replicat_accepts_advanced_checkpoint_table_for_backward_compatibility(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            server.create_replicat(
                "R1",
                "AA",
                "D",
                "C",
                mapStatement="MAP S.T, TARGET S2.T2;",
                advanced=ReplicatAdvancedParameters(checkpointTable="SRCMIRROR_OCIGGLL.CHECKTABLE"),
            )
            payload = m.call_args.args[1]
            self.assertEqual(payload["checkpoint"], {"table": "SRCMIRROR_OCIGGLL.CHECKTABLE"})
            self.assertNotIn("CHECKPOINTTABLE SRCMIRROR_OCIGGLL.CHECKTABLE", payload["config"])

    def test_create_replicat_rejects_conflicting_checkpoint_tables(self):
        with self.assertRaises(ValueError):
            server.create_replicat(
                "R1",
                "AA",
                "D",
                "C",
                mapStatement="MAP S.T, TARGET S2.T2;",
                checkpointTable="A.CHK",
                advanced=ReplicatAdvancedParameters(checkpointTable="B.CHK"),
            )

    def test_update_replicat(self):
        with patch.object(server.client, "patch", return_value={"ok": True}) as m:
            out = server.update_replicat("R1", trailName="AA", domainName="D", connectionName="C", mapStatement="MAP S.T, TARGET S2.T2;", advanced=None)
            self.assertEqual(m.call_args.args[0], server.api.update_replicat("R1"))
            self.assertEqual(
                m.call_args.args[1]["managedProcessSettings"],
                server.DEFAULT_MANAGED_PROCESS_SETTINGS,
            )
            self._assert_json(out, {"ok": True})

    def test_update_replicat_structured_source_requires_target_table(self):
        source_without_target = SimpleNamespace(
            model_dump=lambda **_kwargs: {"schema": "S", "table": "T"}
        )

        with self.assertRaises(ValueError):
            server.update_replicat("R1", source=source_without_target)

    def test_update_replicat_uses_advanced_credentials_and_parallel_mode(self):
        with patch.object(server.client, "patch", return_value={"ok": True}) as m:
            out = server.update_replicat(
                "R1",
                trailName="AA",
                source=CreateReplicatSource(schema="S", table="T", targetTable="D.T"),
                advanced=ReplicatAdvancedParameters(
                    credential="USERIDALIAS TARGET DOMAIN D",
                    modeType="parallel",
                    modeParallel=False,
                ),
            )

        self._assert_json(out, {"ok": True})
        payload = m.call_args.args[1]
        self.assertIn("USERIDALIAS TARGET DOMAIN D", payload["config"])
        self.assertEqual(payload["mode"], {"type": "parallel", "parallel": False})
        self.assertNotIn("source", payload)
        self.assertNotIn("credentials", payload)

    def test_update_replicat_accepts_top_level_checkpoint_table(self):
        with patch.object(server.client, "patch", return_value={"ok": True}) as m:
            server.update_replicat(
                "R1",
                trailName="AA",
                domainName="D",
                connectionName="C",
                mapStatement="MAP S.T, TARGET S2.T2;",
                checkpointTable="SRCMIRROR_OCIGGLL.CHECKTABLE",
                advanced=None,
            )
            payload = m.call_args.args[1]
            self.assertEqual(payload["checkpoint"], {"table": "SRCMIRROR_OCIGGLL.CHECKTABLE"})

    def test_create_distribution_path(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_distribution_path("P1", "src.example.com", "AA", "tgt.example.com", targetAuthenticationMethod=None)
            self.assertEqual(m.call_args.args[0], server.api.create_distribution_path("P1", "src.example.com", "AA", "tgt.example.com", 443, "OAuth", None, None))
            self._assert_json(out, {"ok": True})

    def test_create_distribution_path_with_alias_authentication(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_distribution_path(
                "P1",
                "src.example.com",
                "AA",
                "tgt.example.com",
                targetPort=9443,
                targetAuthenticationMethod="Alias",
                targetDomain="D",
                targetAlias="A",
            )

        self.assertEqual(m.call_args.args[0], server.api.create_distribution_path("P1", "src.example.com", "AA", "tgt.example.com", 9443, "Alias", "D", "A"))
        self.assertEqual(m.call_args.args[1]["target"]["authenticationMethod"], {"domain": "D", "alias": "A"})
        self._assert_json(out, {"ok": True})

    def test_create_distribution_path_rejects_non_hostname_inputs(self):
        with self.assertRaises(ValueError):
            server.create_distribution_path("P1", "https://src.example.com", "AA", "tgt.example.com")

        with self.assertRaises(ValueError):
            server.create_distribution_path("P1", "src.example.com", "AA", "tgt.example.com/services")

    def test_create_data_stream(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_data_stream("DS1", "AA")
            self.assertEqual(m.call_args.args[0], server.api.create_data_stream("DS1", "AA", None, None, None, None, None))
            payload = m.call_args.args[1]
            self.assertFalse(payload["cloudEventsFormat"])
            self.assertEqual(payload["qualityOfService"], "exactlyOnce")
            self.assertEqual(payload["bufferSize"], 1048576)
            self._assert_json(out, {"ok": True})

    def test_create_data_stream_with_custom_options(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_data_stream(
                "DS1",
                "AA",
                qualityOfService="atLeastOnce",
                cloudEventsFormat=True,
                bufferSize=2048,
            )

        payload = m.call_args.args[1]
        self.assertEqual(payload["qualityOfService"], "atLeastOnce")
        self.assertTrue(payload["cloudEventsFormat"])
        self.assertEqual(payload["bufferSize"], 2048)
        self._assert_json(out, {"ok": True})

    def test_create_data_stream_with_included_tables(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_data_stream(
                "DS_CUSTOMER",
                "PC",
                cloudEventsFormat=True,
                includeTables=["YAN_POS.CUSTOMER"],
            )

        m.assert_called_once_with(
            server.api.create_data_stream(
                "DS_CUSTOMER",
                "PC",
                None,
                True,
                None,
                ["YAN_POS.CUSTOMER"],
                None,
            ),
            {
                "source": {"trail": "PC"},
                "qualityOfService": "exactlyOnce",
                "encoding": "json",
                "bufferSize": 1048576,
                "cloudEventsFormat": True,
                "rules": [
                    {
                        "action": "include",
                        "filter": {"objectNames": ["YAN_POS.CUSTOMER"]},
                    }
                ],
            },
        )
        self._assert_json(out, {"ok": True})

    def test_create_data_stream_with_include_and_exclude_rules(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_data_stream(
                "DS_PRODUCTS",
                "PC",
                includeTables=["YAN_POS.CUSTOMER", "YAN_POS.PRODUCT"],
                excludeTables=["YAN_POS.REGIONS"],
            )

        payload = m.call_args.args[1]
        self.assertEqual(
            payload,
            {
                "source": {"trail": "PC"},
                "qualityOfService": "exactlyOnce",
                "encoding": "json",
                "bufferSize": 1048576,
                "cloudEventsFormat": False,
                "rules": [
                    {
                        "action": "include",
                        "filter": {"objectNames": ["YAN_POS.CUSTOMER", "YAN_POS.PRODUCT"]},
                    },
                    {
                        "action": "exclude",
                        "filter": {"objectNames": ["YAN_POS.REGIONS"]},
                    },
                ],
            },
        )
        self._assert_json(out, {"ok": True})

    def test_create_data_stream_rejects_empty_included_table_name(self):
        with patch.object(server.client, "post") as m:
            with self.assertRaisesRegex(ValueError, "non-empty source object name"):
                server.create_data_stream("DS1", "PC", includeTables=[" "])
            m.assert_not_called()

    def test_create_data_stream_rejects_empty_excluded_table_name(self):
        with patch.object(server.client, "post") as m:
            with self.assertRaisesRegex(ValueError, "non-empty source object name"):
                server.create_data_stream("DS1", "PC", excludeTables=[""])
            m.assert_not_called()

    def test_start(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m, patch.object(
            server.client, "get", return_value={"source": "tranlogs"}
        ):
            out = server.start("E1")
            m.assert_called_once_with(server.api.start("E1"), {"name": "start", "processName": "E1"})
            self._assert_json(out, {"ok": True})

    def test_start_at_csn(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m, patch.object(
            server.client, "get", return_value={"source": "tranlogs"}
        ):
            out = server.start("E_Z1", at=50224568010469)
            m.assert_called_once_with(
                server.api.start("E_Z1"),
                {"name": "start", "processName": "E_Z1", "at": 50224568010469},
            )
            self._assert_json(out, {"ok": True})

    def test_start_after_csn(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m, patch.object(
            server.client, "get", return_value={"source": "tranlogs"}
        ):
            out = server.start("E_Z1", after=50224568010469)
            m.assert_called_once_with(
                server.api.start("E_Z1"),
                {"name": "start", "processName": "E_Z1", "after": 50224568010469},
            )
            self._assert_json(out, {"ok": True})

    def test_start_rejects_at_and_after_together(self):
        with patch.object(server.client, "post") as m:
            with self.assertRaisesRegex(ValueError, "mutually exclusive"):
                server.start("E_Z1", at=50224568010469, after=50224568010469)
            m.assert_not_called()

    def test_get_initial_load_cdc_workflow_is_ordered_and_guarded(self):
        workflow = json.loads(server.get_initial_load_cdc_workflow())
        self.assertEqual([step["order"] for step in workflow["steps"]], list(range(1, 8)))
        self.assertIn("start_initial_load_replicat", workflow["steps"][4]["action"])
        self.assertTrue(any("Never start" in rule for rule in workflow["safetyRules"]))

    def test_start_initial_load_replicat_checks_extract_before_starting(self):
        responses = self._initial_load_responses()
        with (
            patch.object(server.client, "get", side_effect=responses.__getitem__) as get,
            patch.object(server.client, "post", return_value={"started": True}) as post,
        ):
            out = server.start_initial_load_replicat("R_INIT", "E_INIT")

        post.assert_called_once_with(
            server.api.start("R_INIT"),
            {"name": "start", "processName": "R_INIT"},
        )
        self.assertEqual(
            get.call_args_list,
            [
                call(server.api.get_extract_status("E_INIT")),
                call(server.api.get_extract_details("E_INIT")),
                call(server.api.get_replicat_details("R_INIT")),
                call(server.api.get_extract_history("E_INIT")),
                call(server.api.get_extract_report("E_INIT")),
                call(server.api.get_extract_status("E_INIT")),
            ],
        )
        result = json.loads(out)
        self.assertEqual(result["prerequisites"]["extractStatus"], "STOPPED")
        self.assertEqual(result["startResult"], {"started": True})

    def test_start_initial_load_replicat_rejects_running_extract(self):
        with (
            patch.object(server.client, "get", return_value={"response": {"status": "running"}}) as get,
            patch.object(server.client, "post") as post,
            self.assertRaisesRegex(ValueError, "not confirmed STOPPED"),
        ):
            server.start_initial_load_replicat("R_INIT", "E_INIT")

        get.assert_called_once_with(server.api.get_extract_status("E_INIT"))
        post.assert_not_called()

    def test_start_initial_load_replicat_rejects_ambiguous_status(self):
        with (
            patch.object(server.client, "get", return_value={"message": "No status available"}) as get,
            patch.object(server.client, "post") as post,
            self.assertRaisesRegex(ValueError, "not confirmed STOPPED"),
        ):
            server.start_initial_load_replicat("R_INIT", "E_INIT")

        get.assert_called_once_with(server.api.get_extract_status("E_INIT"))
        post.assert_not_called()

    def test_start_initial_load_replicat_rejects_failed_or_empty_report(self):
        for report, error in [
            ("Process ABENDED after an error", "failure indicator"),
            ("", "empty report"),
        ]:
            with self.subTest(report=report):
                responses = self._initial_load_responses()
                responses[server.api.get_extract_report("E_INIT")] = report
                with (
                    patch.object(server.client, "get", side_effect=responses.__getitem__) as get,
                    patch.object(server.client, "post") as post,
                    self.assertRaisesRegex(ValueError, error),
                ):
                    server.start_initial_load_replicat("R_INIT", "E_INIT")

                self.assertGreaterEqual(get.call_count, 1)
                post.assert_not_called()

    def test_stop(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.stop("E1")
            m.assert_called_once_with(server.api.stop("E1"), {"name": "stop", "processName": "E1", "force": False})
            self._assert_json(out, {"ok": True})

    def test_start_distribution_path(self):
        with patch.object(server.client, "patch", return_value={"ok": True}) as m:
            out = server.start_distribution_path("P1")
            m.assert_called_once_with(server.api.start_distribution_path("P1"), {"status": "running"})
            self._assert_json(out, {"ok": True})

    def test_stop_distribution_path(self):
        with patch.object(server.client, "patch", return_value={"ok": True}) as m:
            out = server.stop_distribution_path("P1")
            m.assert_called_once_with(server.api.stop_distribution_path("P1"), {"status": "stopped"})
            self._assert_json(out, {"ok": True})

    def test_get_extract_lag(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.get_extract_lag("E1")
            m.assert_called_once_with(server.api.get_extract_lag("E1"), {"command": "GETLAG", "isReported": True})
            self._assert_json(out, {"ok": True})

    def test_get_replicat_lag(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.get_replicat_lag("R1")
            m.assert_called_once_with(server.api.get_replicat_lag("R1"), {"command": "GETLAG", "isReported": True})
            self._assert_json(out, {"ok": True})

    def test_get_extract_report(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.get_extract_report("E1")
            m.assert_called_once_with(server.api.get_extract_report("E1"))
            self._assert_json(out, {"ok": True})

    def test_get_replicat_report(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.get_replicat_report("R1")
            m.assert_called_once_with(server.api.get_replicat_report("R1"))
            self._assert_json(out, {"ok": True})

    def test_get_data_stream_info(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.get_data_stream_info("DS1")
            m.assert_called_once_with(server.api.get_data_stream_info("DS1"))
            self._assert_json(out, {"ok": True})

    def test_get_data_stream_yaml(self):
        with patch.object(server.client, "get", return_value="yaml") as m:
            out = server.get_data_stream_yaml("DS1")
            m.assert_called_once()
            self.assertEqual(out, "yaml")

    def test_get_data_stream_stats(self):
        overall = {"totalMessages": 10}
        network = {"totalBytes": 100}
        tables = {"items": [{"table": "HR.EMP"}]}
        with patch.object(server.client, "get", side_effect=[overall, network, tables]) as m:
            out = server.get_data_stream_stats("DS1")
            self.assertEqual(
                m.call_args_list,
                [
                    ((server.api.get_data_stream_overall_stats("DS1"),), {}),
                    ((server.api.get_data_stream_network_stats("DS1"),), {}),
                    ((server.api.get_data_stream_table_stats("DS1"),), {}),
                ],
            )
            self._assert_json(out, {"overall": overall, "network": network, "tables": tables})
        self.assertEqual(
            server.api.get_data_stream_overall_stats("dsq7x"),
            "/services/pmsrvr/v2/mpoints/DISTSRVR/distsrvrPathStats?WindowRef="
            "%2Fservices%2Fadminsrvr%2Fv2%2Fcontent%2Findex.html%23%2FdataStream%2Fdsq7x%2FdataStreamStats",
        )
        self.assertEqual(
            server.api.get_data_stream_network_stats("dsq7x"),
            "/services/pmsrvr/v2/mpoints/DISTSRVR/distsrvrNetworkStats?WindowRef="
            "%2Fservices%2Fadminsrvr%2Fv2%2Fcontent%2Findex.html%23%2FdataStream%2Fdsq7x%2FdataStreamStats",
        )
        self.assertEqual(
            server.api.get_data_stream_table_stats("dsq7x"),
            "/services/pmsrvr/v2/mpoints/DISTSRVR/distsrvrTableStats?WindowRef="
            "%2Fservices%2Fadminsrvr%2Fv2%2Fcontent%2Findex.html%23%2FdataStream%2Fdsq7x%2FdataStreamStats",
        )

    def test_get_extract_stats(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.get_extract_stats("E1")
            m.assert_called_once_with(server.api.get_extract_stats("E1"), {"command": "STATS", "isReported": True})
            self._assert_json(out, {"ok": True})

    def test_get_replicat_stats(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.get_replicat_stats("R1")
            m.assert_called_once_with(server.api.get_replicat_stats("R1"), {"command": "STATS", "isReported": True})
            self._assert_json(out, {"ok": True})

    def test_get_extract_details(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.get_extract_details("E1")
            m.assert_called_once_with(server.api.get_extract_details("E1"))
            self._assert_json(out, {"ok": True})

    def test_get_replicat_details(self):
        with patch.object(server.client, "get", return_value={"ok": True}) as m:
            out = server.get_replicat_details("R1")
            m.assert_called_once_with(server.api.get_replicat_details("R1"))
            self._assert_json(out, {"ok": True})

    def test_create_extract_requires_table_statement_or_source(self):
        with self.assertRaises(ValueError):
            server.create_extract("E1", "AA", "D", "C")

    def test_create_initial_load_extract_requires_table_statement_or_source(self):
        with self.assertRaises(ValueError):
            server.create_initial_load_extract("E1", "AA", "D", "C")

    def test_update_replicat_requires_map_statement_or_source(self):
        with self.assertRaises(ValueError):
            server.update_replicat("R1")

    def test_create_distribution_path_alias_requires_domain_and_alias(self):
        with self.assertRaises(ValueError):
            server.create_distribution_path(
                "P1",
                "src.example.com",
                "AA",
                "tgt.example.com",
                targetAuthenticationMethod="Alias",
            )

    def test_create_extract_serializes_models_with_aliases(self):
        with patch.object(server, "build_table_statement", return_value="TABLE S.T;") as build_stmt, patch.object(
            server.client, "post", return_value={"ok": True}
        ) as m:
            out = server.create_extract(
                "E1",
                "AA",
                "D",
                "C",
                source=CreateExtractSource(schema="S", table="T"),
                advanced=ExtractAdvancedParameters(ext_trail="AB"),
            )
            self._assert_json(out, {"ok": True})
            build_stmt.assert_called_once()
            arg_payload = build_stmt.call_args.args[0]
            self.assertEqual(arg_payload["source"]["schema"], "S")
            self.assertEqual(arg_payload["source"]["table"], "T")
            sent_payload = m.call_args.args[1]
            self.assertIn("EXTTRAIL AB", sent_payload["config"])

    def test_main_runs_after_successful_connectivity(self):
        with patch.object(server, "_verify_deployment_connectivity") as verify, patch.object(server.mcp, "run") as run:
            server.main()

        verify.assert_called_once_with()
        run.assert_called_once_with(transport="stdio")

    def test_main_exits_after_failed_connectivity_and_debug_trace(self):
        with (
            patch.object(server, "_verify_deployment_connectivity", side_effect=RuntimeError("boom")),
            patch.object(server, "_log_startup") as log,
            patch.object(server.traceback, "print_exc") as print_exc,
            patch.dict(os.environ, {"OGG_MCP_DEBUG": "true"}),
            self.assertRaises(SystemExit) as exc,
        ):
            server.main()

        self.assertEqual(exc.exception.code, 1)
        self.assertTrue(any("Startup aborted" in call.args[1] for call in log.call_args_list))
        print_exc.assert_called_once()


class TestModelValidation(unittest.TestCase):
    def test_extract_source_rejects_extra_fields(self):
        with self.assertRaises(ValidationError):
            CreateExtractSource(schema="S", table="T", unknown="x")

    def test_extract_source_accepts_camel_case_alias(self):
        m = CreateExtractSource(schema="S", table="T", partitionObjIds=[1, 2])
        dumped = m.model_dump(by_alias=True, exclude_none=True)
        self.assertIn("partitionObjIds", dumped)
        self.assertEqual(dumped["partitionObjIds"], [1, 2])


if __name__ == "__main__":
    unittest.main()
