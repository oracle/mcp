"""Offline unit tests for the consolidated OCI Data Science MCP server.

This refactors the legacy per-tool test suite into tests that target the
*consolidated* tool surface in:

  oracle.oci_data_science_mcp_server.server

Consolidated tools (each uses an `action` parameter):

- oci_ds_compartments
- data_science_projects
- data_science_model_catalog
- data_science_jobs
- data_science_job_runs
- data_science_notebook_sessions
- data_science_pipelines
- data_science_pipeline_runs
- data_science_model_deployments

All OCI SDK / ADS SDK interactions are mocked so tests run offline.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client

from oracle.oci_data_science_mcp_server.server import mcp


class TestConsolidatedTools:
    @pytest.mark.asyncio
    async def test_oci_ds_compartments_list(self) -> None:
        fake_compartments = [
            SimpleNamespace(name="Root", id="ocid1.compartment.oc1..root"),
            SimpleNamespace(name="Dev", id="ocid1.compartment.oc1..dev"),
        ]

        with patch(
            "oracle.oci_data_science_mcp_server.server.get_oci_config",
            return_value={"tenancy": "ocid1.tenancy.oc1..abc"},
        ), patch(
            "oracle.oci_data_science_mcp_server.server.get_identity_client"
        ) as mock_identity_client, patch(
            "oracle.oci_data_science_mcp_server.server.oci.pagination.list_call_get_all_results"
        ) as mock_list_all:
            mock_identity_client.return_value = MagicMock()
            mock_list_all.return_value = SimpleNamespace(data=fake_compartments)

            async with Client(mcp) as client:
                res = await client.call_tool("oci_ds_compartments", {"action": "list"})

        out = res.structured_content
        assert out["resource"] == "compartments"
        assert out["action"] == "list"
        assert out["result"]["by_name"]["Root"] == "ocid1.compartment.oc1..root"
        assert out["result"]["by_name"]["Dev"] == "ocid1.compartment.oc1..dev"

    @pytest.mark.asyncio
    async def test_data_science_projects_list_and_count(self) -> None:
        fake_projects = [
            SimpleNamespace(id="p1", display_name="A", description="aa"),
            SimpleNamespace(id="p2", display_name="B", description="bb"),
        ]

        with patch("oracle.oci_data_science_mcp_server.server.ProjectCatalog") as pc:
            inst = pc.return_value
            inst.list_projects.return_value = fake_projects
            inst.__len__.return_value = 2

            async with Client(mcp) as client:
                res_list = await client.call_tool(
                    "data_science_projects",
                    {"action": "list", "compartment_id": "c"},
                )
                res_count = await client.call_tool(
                    "data_science_projects",
                    {"action": "count", "compartment_id": "c"},
                )

        out_list = res_list.structured_content
        assert out_list["resource"] == "projects"
        assert out_list["action"] == "list"
        assert out_list["result"] == [
            {"project_id": "p1", "project_name": "A", "project_description": "aa"},
            {"project_id": "p2", "project_name": "B", "project_description": "bb"},
        ]

        out_count = res_count.structured_content
        assert out_count["resource"] == "projects"
        assert out_count["action"] == "count"
        assert out_count["result"] == 2

    @pytest.mark.asyncio
    async def test_data_science_projects_create_update_delete(self) -> None:
        with patch("oracle.oci_data_science_mcp_server.server.ProjectCatalog") as pc:
            inst = pc.return_value
            inst.create_project.return_value = SimpleNamespace(
                id="p1", display_name="MyProj", description="desc"
            )

            async with Client(mcp) as client:
                res_create = await client.call_tool(
                    "data_science_projects",
                    {
                        "action": "create",
                        "compartment_id": "c",
                        "project_name": "MyProj",
                        "project_description": "desc",
                    },
                )

                res_update = await client.call_tool(
                    "data_science_projects",
                    {
                        "action": "update",
                        "compartment_id": "c",
                        "project_id": "p1",
                        "new_name": "NewName",
                    },
                )

                res_delete = await client.call_tool(
                    "data_science_projects",
                    {"action": "delete", "compartment_id": "c", "project_id": "p1"},
                )

        assert res_create.structured_content["result"]["project_id"] == "p1"
        assert res_update.structured_content["result"]["updated"] is True
        assert res_delete.structured_content["result"]["deleted"] is True

    @pytest.mark.asyncio
    async def test_data_science_model_catalog_list_models_with_project_id(self) -> None:
        # Ensure that passing project_id routes into a project-filtered list_models call.
        with patch("oracle.oci_data_science_mcp_server.server.ModelCatalog") as mc:
            inst = mc.return_value
            inst.list_models.return_value = []

            async with Client(mcp) as client:
                await client.call_tool(
                    "data_science_model_catalog",
                    {
                        "action": "list_models",
                        "compartment_id": "c",
                        "project_id": "p1",
                    },
                )

        inst.list_models.assert_called_with(project_id="p1")

    @pytest.mark.asyncio
    async def test_data_science_model_catalog_download_uses_download_artifact(self) -> None:
        # The consolidated server implementation uses:
        #   model = GenericModel.from_id(model_id)
        #   model.download_artifact(artifact_dir=target_dir, ...)
        # and then returns `_list_files_recursive(target_dir)`.
        with patch("oracle.oci_data_science_mcp_server.server.GenericModel") as gm, patch(
            "oracle.oci_data_science_mcp_server.server._list_files_recursive",
            return_value=[{"path": "score.py", "bytes": 10}],
        ) as list_files:
            model = gm.from_id.return_value

            async with Client(mcp) as client:
                res = await client.call_tool(
                    "data_science_model_catalog",
                    {
                        "action": "download",
                        "compartment_id": "c",
                        "model_id": "m1",
                        "target_dir": "/tmp/out",
                    },
                )

        gm.from_id.assert_called_once_with("m1")
        model.download_artifact.assert_called_once()
        list_files.assert_called_once_with("/tmp/out")

        out = res.structured_content
        assert out["resource"] == "model_catalog"
        assert out["action"] == "download"
        assert out["result"]["artifact_dir"] == "/tmp/out"
        assert out["result"]["downloaded_files_count"] == 1

    @pytest.mark.asyncio
    async def test_data_science_model_catalog_count_and_list_models_limit(self) -> None:
        fake_models = [
            SimpleNamespace(
                id="m1",
                display_name="M1",
                model_version_set_name="vs",
                version_label="1",
                version_id="v1",
                project_id="p1",
                lifecycle_state="ACTIVE",
                time_created=None,
            ),
            SimpleNamespace(
                id="m2",
                display_name="M2",
                model_version_set_name="vs",
                version_label="2",
                version_id="v2",
                project_id="p2",
                lifecycle_state="ACTIVE",
                time_created=None,
            ),
        ]

        with patch("oracle.oci_data_science_mcp_server.server.ModelCatalog") as mc:
            inst = mc.return_value
            inst.list_models.return_value = fake_models

            async with Client(mcp) as client:
                res_count = await client.call_tool(
                    "data_science_model_catalog",
                    {"action": "count", "compartment_id": "c"},
                )
                res_list = await client.call_tool(
                    "data_science_model_catalog",
                    {"action": "list_models", "compartment_id": "c", "limit": 1},
                )

        assert res_count.structured_content["resource"] == "model_catalog"
        assert res_count.structured_content["action"] == "count"
        assert res_count.structured_content["result"] == 2

        out_list = res_list.structured_content
        assert out_list["resource"] == "model_catalog"
        assert out_list["action"] == "list_models"
        assert len(out_list["result"]) == 1
        assert out_list["result"][0]["model_id"] == "m1"

    @pytest.mark.asyncio
    async def test_data_science_model_catalog_list_models_project_id_fallback_filters(self) -> None:
        """If ADS list_models(project_id=...) isn't supported, server falls back to client-side filtering."""

        all_models = [
            SimpleNamespace(id="m1", display_name="M1", project_id="p1"),
            SimpleNamespace(id="m2", display_name="M2", project_id="p2"),
        ]

        with patch("oracle.oci_data_science_mcp_server.server.ModelCatalog") as mc:
            inst = mc.return_value

            def list_models_side_effect(*_args, **kwargs):
                if "project_id" in kwargs:
                    raise TypeError("old ads")
                return all_models

            inst.list_models.side_effect = list_models_side_effect

            async with Client(mcp) as client:
                res = await client.call_tool(
                    "data_science_model_catalog",
                    {"action": "list_models", "compartment_id": "c", "project_id": "p1"},
                )

        out = res.structured_content
        assert out["resource"] == "model_catalog"
        assert [m["model_id"] for m in out["result"]] == ["m1"]

    @pytest.mark.asyncio
    async def test_data_science_model_catalog_list_version_sets_and_attributes(self) -> None:
        with patch(
            "oracle.oci_data_science_mcp_server.server.get_data_science_client"
        ) as get_client, patch(
            "oracle.oci_data_science_mcp_server.server.ModelVersionSet"
        ) as mvs_cls:
            ds_client = MagicMock()
            get_client.return_value = ds_client
            ds_client.list_model_version_sets.return_value = SimpleNamespace(
                data=[SimpleNamespace(id="vs1", name="VS1"), SimpleNamespace(id="vs2", name="VS2")]
            )

            mvs = mvs_cls.from_id.return_value
            mvs.to_dict.return_value = {"id": "vs1", "name": "VS1"}

            async with Client(mcp) as client:
                res_list = await client.call_tool(
                    "data_science_model_catalog",
                    {"action": "list_version_sets", "compartment_id": "c", "limit": 1},
                )
                res_attrs = await client.call_tool(
                    "data_science_model_catalog",
                    {
                        "action": "version_set_attributes",
                        "compartment_id": "c",
                        "model_version_set_id": "vs1",
                    },
                )

        assert res_list.structured_content["resource"] == "model_catalog"
        assert res_list.structured_content["result"] == [{"id": "vs1", "name": "VS1"}]
        assert res_attrs.structured_content["result"]["id"] == "vs1"

    @pytest.mark.asyncio
    async def test_data_science_jobs_list_and_details(self) -> None:
        with patch("oracle.oci_data_science_mcp_server.server.DataScienceJob") as dsj, patch(
            "oracle.oci_data_science_mcp_server.server.Job"
        ) as job_cls:
            dsj.list_jobs.return_value = [
                SimpleNamespace(job_id="j1", name="A"),
                SimpleNamespace(job_id="j2", name="B"),
            ]
            job = job_cls.from_datascience_job.return_value
            job.to_dict.return_value = {"id": "j1"}

            async with Client(mcp) as client:
                res_list = await client.call_tool(
                    "data_science_jobs",
                    {"action": "list", "compartment_id": "c"},
                )
                res_details = await client.call_tool(
                    "data_science_jobs",
                    {"action": "details", "job_id": "j1"},
                )

        assert res_list.structured_content["resource"] == "jobs"
        assert res_list.structured_content["result"] == [
            {"job_id": "j1", "job_name": "A"},
            {"job_id": "j2", "job_name": "B"},
        ]
        assert res_details.structured_content["resource"] == "jobs"
        assert res_details.structured_content["result"]["id"] == "j1"

    @pytest.mark.asyncio
    async def test_data_science_jobs_create_update_and_delete(self) -> None:
        with patch("oracle.oci_data_science_mcp_server.server.DataScienceJob") as infra_cls, patch(
            "oracle.oci_data_science_mcp_server.server.ScriptRuntime"
        ) as script_rt_cls, patch(
            "oracle.oci_data_science_mcp_server.server.ContainerRuntime"
        ) as container_rt_cls, patch(
            "oracle.oci_data_science_mcp_server.server.Job"
        ) as job_cls, patch(
            "oracle.oci_data_science_mcp_server.server.get_data_science_client"
        ) as get_client:
            ds_client = MagicMock()
            get_client.return_value = ds_client

            # Infrastructure builder is a fluent API in ADS.
            infra = infra_cls.return_value
            infra.with_shape_name.return_value = infra
            infra.with_compartment_id.return_value = infra
            infra.with_project_id.return_value = infra
            infra.with_block_storage_size.return_value = infra
            infra.with_shape_config_details.return_value = infra

            # Runtimes are also fluent.
            script_rt = script_rt_cls.return_value
            script_rt.with_service_conda.return_value = script_rt
            script_rt.with_source.return_value = script_rt

            container_rt = container_rt_cls.return_value
            container_rt.with_image.return_value = container_rt
            container_rt.with_replica.return_value = container_rt

            # Job is fluent and returns a dict.
            job = job_cls.return_value
            job.with_infrastructure.return_value = job
            job.with_runtime.return_value = job
            job.create.return_value = None
            job.to_dict.return_value = {"job_id": "j1"}
            job_cls.from_datascience_job.return_value = job

            async with Client(mcp) as client:
                res_create_script = await client.call_tool(
                    "data_science_jobs",
                    {
                        "action": "create_script",
                        "compartment_id": "c",
                        "project_id": "p",
                        "script_path": "./train.py",
                        "display_name": "job-script",
                        "ocpus": 1,
                        "memory_in_gbs": 16.0,
                    },
                )
                res_create_container = await client.call_tool(
                    "data_science_jobs",
                    {
                        "action": "create_container",
                        "compartment_id": "c",
                        "project_id": "p",
                        "image": "iad.ocir.io/tenancy/repo:tag",
                        "display_name": "job-container",
                    },
                )
                res_update = await client.call_tool(
                    "data_science_jobs",
                    {"action": "update", "job_id": "j1", "new_display_name": "job-new"},
                )
                res_delete = await client.call_tool(
                    "data_science_jobs",
                    {"action": "delete", "job_id": "j1"},
                )

        assert res_create_script.structured_content["action"] == "create_script"
        assert res_create_container.structured_content["action"] == "create_container"
        assert res_update.structured_content["result"]["updated"] is True
        assert res_delete.structured_content["result"]["deleted"] is True

        # Ensure update_job was invoked with a details object containing the expected display_name.
        _, kwargs = ds_client.update_job.call_args
        assert kwargs["job_id"] == "j1"
        assert getattr(kwargs["update_job_details"], "display_name", None) == "job-new"

    @pytest.mark.asyncio
    async def test_data_science_jobs_update_requires_new_display_name(self) -> None:
        async with Client(mcp) as client:
            res = await client.call_tool(
                "data_science_jobs",
                {"action": "update", "job_id": "j1"},
                raise_on_error=False,
            )
        assert res.is_error is True

    @pytest.mark.asyncio
    async def test_data_science_job_runs_start_and_list(self) -> None:
        with patch(
            "oracle.oci_data_science_mcp_server.server.get_data_science_client"
        ) as get_client, patch(
            "oracle.oci_data_science_mcp_server.server.oci.util.to_dict",
            side_effect=lambda o: {"id": getattr(o, "id", None)},
        ):
            ds_client = MagicMock()
            get_client.return_value = ds_client

            ds_client.create_job_run.return_value = SimpleNamespace(
                data=SimpleNamespace(id="jr1", lifecycle_state="ACCEPTED")
            )
            ds_client.list_job_runs.return_value = SimpleNamespace(
                data=[SimpleNamespace(id="jr1")]
            )

            async with Client(mcp) as client:
                res_start = await client.call_tool(
                    "data_science_job_runs",
                    {
                        "action": "start",
                        "compartment_id": "c",
                        "project_id": "p",
                        "job_id": "j",
                        "display_name": "run",
                    },
                )
                res_list = await client.call_tool(
                    "data_science_job_runs",
                    {"action": "list", "compartment_id": "c"},
                )

        assert res_start.structured_content["resource"] == "job_runs"
        assert res_start.structured_content["result"]["job_run_id"] == "jr1"
        assert isinstance(res_list.structured_content["result"], list)

    @pytest.mark.asyncio
    async def test_data_science_job_runs_status_and_cancel(self) -> None:
        with patch(
            "oracle.oci_data_science_mcp_server.server.get_data_science_client"
        ) as get_client, patch(
            "oracle.oci_data_science_mcp_server.server.oci.util.to_dict",
            side_effect=lambda o: {"id": getattr(o, "id", None)},
        ):
            ds_client = MagicMock()
            get_client.return_value = ds_client
            ds_client.get_job_run.return_value = SimpleNamespace(data=SimpleNamespace(id="jr-by-id"))
            ds_client.list_job_runs.return_value = SimpleNamespace(data=[SimpleNamespace(id="jr-latest")])

            async with Client(mcp) as client:
                res_status_by_id = await client.call_tool(
                    "data_science_job_runs",
                    {
                        "action": "status",
                        "compartment_id": "c",
                        "job_id": "j",
                        "job_run_id": "jr-by-id",
                    },
                )
                res_status_latest = await client.call_tool(
                    "data_science_job_runs",
                    {"action": "status", "compartment_id": "c", "job_id": "j"},
                )
                res_cancel_by_id = await client.call_tool(
                    "data_science_job_runs",
                    {
                        "action": "cancel",
                        "compartment_id": "c",
                        "job_id": "j",
                        "job_run_id": "jr-by-id",
                    },
                )
                res_cancel_latest = await client.call_tool(
                    "data_science_job_runs",
                    {"action": "cancel", "compartment_id": "c", "job_id": "j"},
                )

        assert res_status_by_id.structured_content["result"]["id"] == "jr-by-id"
        assert res_status_latest.structured_content["result"]["id"] == "jr-latest"
        assert res_cancel_by_id.structured_content["result"]["cancel_requested"] is True
        assert res_cancel_latest.structured_content["result"]["cancel_requested"] is True

    @pytest.mark.asyncio
    async def test_data_science_job_runs_status_and_cancel_when_no_runs(self) -> None:
        with patch(
            "oracle.oci_data_science_mcp_server.server.get_data_science_client"
        ) as get_client:
            ds_client = MagicMock()
            get_client.return_value = ds_client
            ds_client.list_job_runs.return_value = SimpleNamespace(data=[])

            async with Client(mcp) as client:
                res_status = await client.call_tool(
                    "data_science_job_runs",
                    {"action": "status", "compartment_id": "c", "job_id": "j"},
                )
                res_cancel = await client.call_tool(
                    "data_science_job_runs",
                    {"action": "cancel", "compartment_id": "c", "job_id": "j"},
                )

        assert res_status.structured_content["result"] is None
        assert "No job runs found" in res_status.structured_content.get("message", "")
        assert res_cancel.structured_content["result"] is None
        assert "No job runs found" in res_cancel.structured_content.get("message", "")

    @pytest.mark.asyncio
    async def test_data_science_job_runs_list_passes_job_id_and_limit(self) -> None:
        with patch(
            "oracle.oci_data_science_mcp_server.server.get_data_science_client"
        ) as get_client:
            ds_client = MagicMock()
            get_client.return_value = ds_client
            ds_client.list_job_runs.return_value = SimpleNamespace(data=[])

            async with Client(mcp) as client:
                await client.call_tool(
                    "data_science_job_runs",
                    {"action": "list", "compartment_id": "c", "job_id": "j", "limit": 5},
                )

        ds_client.list_job_runs.assert_called_with(compartment_id="c", job_id="j", limit=5)

    @pytest.mark.asyncio
    async def test_data_science_notebook_sessions_create_requires_flex_pair(self) -> None:
        # Flexible shapes require both ocpus and memory_in_gbs.
        async with Client(mcp) as client:
            res = await client.call_tool(
                "data_science_notebook_sessions",
                {
                    "action": "create",
                    "compartment_id": "c",
                    "project_id": "p",
                    "display_name": "nb",
                    "shape": "VM.Standard.E5.Flex",
                    "ocpus": 2,
                    # memory_in_gbs omitted
                },
                raise_on_error=False,
            )

        assert res.is_error is True

    @pytest.mark.asyncio
    async def test_data_science_notebook_sessions_list_create_activate_stop_delete(self) -> None:
        with patch(
            "oracle.oci_data_science_mcp_server.server.get_data_science_client"
        ) as get_client:
            ds_client = MagicMock()
            get_client.return_value = ds_client

            ds_client.list_notebook_sessions.return_value = SimpleNamespace(
                data=[
                    SimpleNamespace(id="nb1", display_name="NB1", lifecycle_state="ACTIVE"),
                    SimpleNamespace(id="nb2", display_name="NB2", lifecycle_state="INACTIVE"),
                ]
            )
            ds_client.create_notebook_session.return_value = SimpleNamespace(
                data=SimpleNamespace(
                    id="nb-created",
                    display_name="NB",
                    time_created="2025-01-01T00:00:00Z",
                    notebook_session_url="https://example/notebook",
                )
            )
            ds_client.get_notebook_session.return_value = SimpleNamespace(
                data=SimpleNamespace(notebook_session_url="https://example/notebook")
            )

            async with Client(mcp) as client:
                res_list = await client.call_tool(
                    "data_science_notebook_sessions",
                    {"action": "list", "compartment_id": "c"},
                )
                res_create = await client.call_tool(
                    "data_science_notebook_sessions",
                    {"action": "create", "compartment_id": "c", "project_id": "p", "display_name": "NB"},
                )
                res_activate = await client.call_tool(
                    "data_science_notebook_sessions",
                    {"action": "activate", "compartment_id": "c", "notebook_session_id": "nb-created"},
                )
                res_stop = await client.call_tool(
                    "data_science_notebook_sessions",
                    {"action": "stop", "notebook_session_id": "nb-created"},
                )
                res_delete = await client.call_tool(
                    "data_science_notebook_sessions",
                    {"action": "delete", "notebook_session_id": "nb-created"},
                )

        assert res_list.structured_content["resource"] == "notebook_sessions"
        assert len(res_list.structured_content["result"]) == 2
        assert res_create.structured_content["result"]["id"] == "nb-created"
        assert res_activate.structured_content["result"]["notebook_session_id"] == "nb-created"
        assert res_stop.structured_content["result"]["stopped"] is True
        assert res_delete.structured_content["result"]["deleted"] is True

    @pytest.mark.asyncio
    async def test_data_science_notebook_sessions_activate_requires_compartment_id(self) -> None:
        async with Client(mcp) as client:
            res = await client.call_tool(
                "data_science_notebook_sessions",
                {"action": "activate", "notebook_session_id": "nb"},
                raise_on_error=False,
            )
        assert res.is_error is True

    @pytest.mark.asyncio
    async def test_data_science_pipelines_list_details_delete(self) -> None:
        with patch(
            "oracle.oci_data_science_mcp_server.server.get_data_science_client"
        ) as get_client, patch(
            "oracle.oci_data_science_mcp_server.server.oci.util.to_dict",
            side_effect=lambda o: {"id": getattr(o, "id", None)},
        ):
            ds_client = MagicMock()
            get_client.return_value = ds_client

            ds_client.list_pipelines.return_value = SimpleNamespace(
                data=[
                    SimpleNamespace(id="pl1", display_name="P1"),
                    SimpleNamespace(id="pl2", display_name="P2"),
                ]
            )
            ds_client.get_pipeline.return_value = SimpleNamespace(data=SimpleNamespace(id="pl1"))

            async with Client(mcp) as client:
                res_list = await client.call_tool(
                    "data_science_pipelines",
                    {"action": "list", "compartment_id": "c", "limit": 1},
                )
                res_details = await client.call_tool(
                    "data_science_pipelines",
                    {"action": "details", "pipeline_id": "pl1"},
                )
                res_delete = await client.call_tool(
                    "data_science_pipelines",
                    {"action": "delete", "pipeline_id": "pl1"},
                )

        assert res_list.structured_content["result"] == [{"id": "pl1", "name": "P1"}]
        assert res_details.structured_content["result"]["id"] == "pl1"
        assert res_delete.structured_content["result"]["delete_requested"] is True

    @pytest.mark.asyncio
    async def test_data_science_pipeline_runs_start_list_and_status(self) -> None:
        with patch(
            "oracle.oci_data_science_mcp_server.server.get_data_science_client"
        ) as get_client, patch(
            "oracle.oci_data_science_mcp_server.server.oci.util.to_dict",
            side_effect=lambda o: {"id": getattr(o, "id", None)},
        ):
            ds_client = MagicMock()
            get_client.return_value = ds_client

            ds_client.create_pipeline_run.return_value = SimpleNamespace(
                data=SimpleNamespace(id="pr1", lifecycle_state="ACCEPTED")
            )
            ds_client.list_pipeline_runs.return_value = SimpleNamespace(data=[SimpleNamespace(id="pr1")])
            ds_client.get_pipeline_run.return_value = SimpleNamespace(data=SimpleNamespace(id="pr-by-id"))

            async with Client(mcp) as client:
                res_start = await client.call_tool(
                    "data_science_pipeline_runs",
                    {"action": "start", "compartment_id": "c", "pipeline_id": "pl1", "display_name": "run"},
                )
                res_list = await client.call_tool(
                    "data_science_pipeline_runs",
                    {"action": "list", "compartment_id": "c", "pipeline_id": "pl1", "limit": 2},
                )
                res_status_by_id = await client.call_tool(
                    "data_science_pipeline_runs",
                    {
                        "action": "status",
                        "compartment_id": "c",
                        "pipeline_id": "pl1",
                        "pipeline_run_id": "pr-by-id",
                    },
                )
                res_status_latest = await client.call_tool(
                    "data_science_pipeline_runs",
                    {"action": "status", "compartment_id": "c", "pipeline_id": "pl1"},
                )

        assert res_start.structured_content["result"]["pipeline_run_id"] == "pr1"
        assert isinstance(res_list.structured_content["result"], list)
        assert res_status_by_id.structured_content["result"]["id"] == "pr-by-id"
        assert res_status_latest.structured_content["result"]["id"] == "pr1"

    @pytest.mark.asyncio
    async def test_data_science_pipeline_runs_status_when_no_runs(self) -> None:
        with patch(
            "oracle.oci_data_science_mcp_server.server.get_data_science_client"
        ) as get_client:
            ds_client = MagicMock()
            get_client.return_value = ds_client
            ds_client.list_pipeline_runs.return_value = SimpleNamespace(data=[])

            async with Client(mcp) as client:
                res = await client.call_tool(
                    "data_science_pipeline_runs",
                    {"action": "status", "compartment_id": "c", "pipeline_id": "pl1"},
                )

        assert res.structured_content["result"] is None
        assert "No pipeline runs found" in res.structured_content.get("message", "")

    @pytest.mark.asyncio
    async def test_data_science_model_deployments_list_deploy_activate_deactivate_delete(self) -> None:
        with patch(
            "oracle.oci_data_science_mcp_server.server.get_data_science_client"
        ) as get_client, patch(
            "oracle.oci_data_science_mcp_server.server.GenericModel"
        ) as gm:
            ds_client = MagicMock()
            get_client.return_value = ds_client

            ds_client.list_model_deployments.return_value = SimpleNamespace(
                data=[
                    SimpleNamespace(id="d1", display_name="D1", lifecycle_state="ACTIVE"),
                    SimpleNamespace(id="d2", display_name="D2", lifecycle_state="INACTIVE"),
                ]
            )

            model = gm.from_id.return_value
            model.deploy.return_value = SimpleNamespace(
                model_deployment=SimpleNamespace(id="dep1", url="https://example/predict")
            )

            async with Client(mcp) as client:
                res_list = await client.call_tool(
                    "data_science_model_deployments",
                    {"action": "list", "compartment_id": "c", "limit": 1},
                )
                res_deploy = await client.call_tool(
                    "data_science_model_deployments",
                    {
                        "action": "deploy",
                        "compartment_id": "c",
                        "project_id": "p",
                        "model_id": "m",
                        "display_name": "DEP",
                        "ocpus": 1,
                        "memory_in_gbs": 8,
                    },
                )
                res_activate = await client.call_tool(
                    "data_science_model_deployments",
                    {"action": "activate", "deployment_id": "dep1"},
                )
                res_deactivate = await client.call_tool(
                    "data_science_model_deployments",
                    {"action": "deactivate", "deployment_id": "dep1"},
                )
                res_delete = await client.call_tool(
                    "data_science_model_deployments",
                    {"action": "delete", "deployment_id": "dep1"},
                )

        assert res_list.structured_content["result"] == [
            {"id": "d1", "name": "D1", "lifecycle_state": "ACTIVE"}
        ]
        assert res_deploy.structured_content["result"]["deployment_id"] == "dep1"
        assert res_activate.structured_content["result"]["activate_requested"] is True
        assert res_deactivate.structured_content["result"]["deactivate_requested"] is True
        assert res_delete.structured_content["result"]["delete_requested"] is True

        ds_client.activate_model_deployment.assert_called_once_with(model_deployment_id="dep1")
        ds_client.deactivate_model_deployment.assert_called_once_with(model_deployment_id="dep1")
        ds_client.delete_model_deployment.assert_called_once_with(model_deployment_id="dep1")

    @pytest.mark.asyncio
    async def test_invalid_action_is_rejected_by_schema_validation(self) -> None:
        async with Client(mcp) as client:
            res = await client.call_tool(
                "data_science_projects",
                {"action": "bogus", "compartment_id": "c"},
                raise_on_error=False,
            )
        assert res.is_error is True


class TestResource:
    @pytest.mark.asyncio
    async def test_resource_config(self) -> None:
        async with Client(mcp) as client:
            contents = await client.read_resource("resource://config")

        assert isinstance(contents, list)
        assert contents and str(contents[0].uri) == "resource://config"
        assert "version" in contents[0].text


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_tool_error_payload_contains_exception_text(self) -> None:
        # Ensure `raise_on_error=False` returns an error payload containing the exception message.
        with patch(
            "oracle.oci_data_science_mcp_server.server.ProjectCatalog",
            side_effect=RuntimeError("boom"),
        ):
            async with Client(mcp) as client:
                res = await client.call_tool(
                    "data_science_projects",
                    {"action": "count", "compartment_id": "c"},
                    raise_on_error=False,
                )

        assert res.is_error is True
        assert any("boom" in getattr(b, "text", "") for b in res.content)
