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
from unittest.mock import patch

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
    def _assert_json(self, actual: str, expected: dict):
        self.assertEqual(json.loads(actual), expected)

    def test_log_startup_writes_file_and_ignores_file_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "startup.log")
            with patch.dict(os.environ, {"GG_MCP_LOG_FILE": log_file}):
                server._log_startup("INFO", "hello")
            with open(log_file, encoding="utf-8") as f:
                self.assertIn("[INFO] hello", f.read())

        with patch.dict(os.environ, {"GG_MCP_LOG_FILE": "/no/such/dir/startup.log"}):
            server._log_startup("INFO", "ignored")

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
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.get_extract_status("E1")
            m.assert_called_once_with(server.api.get_extract_status("E1"), {"command": "STATUS"})
            self._assert_json(out, {"ok": True})

    def test_get_replicat_status(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.get_replicat_status("R1")
            m.assert_called_once_with(server.api.get_replicat_status("R1"), {"command": "STATUS"})
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

    def test_create_extract(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_extract("E1", "AA", "D", "C", tableStatement="TABLE S.T;", advanced=None)
            self.assertEqual(m.call_args.args[0], server.api.create_extract("E1"))
            self.assertEqual(
                m.call_args.args[1]["managedProcessSettings"],
                server.DEFAULT_MANAGED_PROCESS_SETTINGS,
            )
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
        self.assertIn("MAP S.T, TARGET D.T, TARGETDEF target.def;", payload["config"])
        self.assertEqual(payload["checkpoint"], {"table": "D.CHKPT"})
        self.assertEqual(payload["mode"], {"type": "parallel", "parallel": True})
        self.assertNotIn("source", payload)

    def test_create_replicat_defaults_begin_to_now(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            server.create_replicat("R1", "AA", "D", "C", mapStatement="MAP S.T, TARGET S2.T2;", advanced=None)
            self.assertEqual(m.call_args.args[1]["begin"], "now")

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

    def test_create_data_stream(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.create_data_stream("DS1", "AA")
            self.assertEqual(m.call_args.args[0], server.api.create_data_stream("DS1", "AA", None, None, None))
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

    def test_start(self):
        with patch.object(server.client, "post", return_value={"ok": True}) as m:
            out = server.start("E1")
            m.assert_called_once_with(server.api.start("E1"), {"name": "start", "processName": "E1"})
            self._assert_json(out, {"ok": True})

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
