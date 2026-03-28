"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# load dependencies
from __future__ import annotations

import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import ads
import oci
from ads.catalog.model import ModelCatalog
from ads.catalog.project import ProjectCatalog
from ads.jobs import ContainerRuntime, DataScienceJob, Job, ScriptRuntime
from ads.model import ModelVersionSet
from ads.model.generic_model import GenericModel
from fastmcp import FastMCP
from oci.data_science.models import (
    CreateJobRunDetails,
    CreateModelDeploymentDetails,
    CreateNotebookSessionDetails,
    CreatePipelineRunDetails,
    NotebookSessionConfigDetails,
    NotebookSessionShapeConfigDetails,
    UpdateJobDetails,
)
from pydantic import Field

from . import __project__, __version__

# configure logging
LOG_LEVEL = os.getenv("FASTMCP_LOG_LEVEL", "ERROR").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.ERROR),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stderr,
    force=True,
)
logger = logging.getLogger(__name__)
for noisy in ("fastmcp", "mcp", "uvicorn", "ads", "oci", "urllib3"):
    logging.getLogger(noisy).setLevel(getattr(logging, LOG_LEVEL, logging.ERROR))
    logging.getLogger(noisy).propagate = False

# instantiate MCP server
mcp = FastMCP(name=__project__)

# ADS uses OCI Python SDK config when set to api_key.
ads.set_auth("api_key")

# define helper functions
def _user_agent_name() -> str:
    ''' Returns server name '''
    return __project__.split("oracle.", 1)[1].split("-server", 1)[0]


def get_oci_config() -> dict:
    """Load OCI config from ~/.oci/config."""

    try:

        config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE))
        config["additional_user_agent"] = f"{_user_agent_name()}/{__version__}"
    except Exception:
        logger.exception("Failed to load OCI Config. Ensure your API Key is setup correctly")
    
    return config


def get_identity_client() -> oci.identity.IdentityClient:
    ''' returns an IAM IdentityClient for use with OCI SDK '''
    return oci.identity.IdentityClient(get_oci_config())


def get_data_science_client() -> oci.data_science.DataScienceClient:
    ''' returns a DataScienceClient for use with OCI SDK '''
    return oci.data_science.DataScienceClient(get_oci_config())


def _list_files_recursive(base_dir: str, *, limit: int = 200) -> list[dict[str, Any]]:
    """Return a small, token-efficient recursive file listing for debugging."""

    base = Path(base_dir)
    results: list[dict[str, Any]] = []
    if not base.exists():
        return results

    # Use rglob but keep response size bounded.
    for p in base.rglob("*"):
        if len(results) >= limit:
            break
        if p.is_file():
            try:
                size = p.stat().st_size
            except OSError:
                size = None
            results.append(
                {
                    "path": str(p.relative_to(base)),
                    "bytes": size,
                }
            )
    return results

def _require(value: Any, name: str, *, action: str) -> None:
    ''' Validate required parameter is present and non-empty for a given action of an MCP tool '''
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"Missing required parameter '{name}' for action='{action}'.")


def _at_least_one(*pairs: tuple[str, Any], action: str) -> None:
    ''' Validate that at least one of several candidate parameters is provided '''
    if not any(v is not None and (not isinstance(v, str) or v.strip()) for _, v in pairs):
        keys = ", ".join(k for k, _ in pairs)
        raise ValueError(
            f"At least one of [{keys}] must be provided for action='{action}'."
        )


def _ok(resource: str, action: str, result: Any, **extra: Any) -> Dict[str, Any]:
    ''' 
        Build a standardized success payload for MCP tool responses.

    Returns a dictionary containing the common fields `resource`, `action`, and
    `result`, and merges any additional keyword fields into the payload.

    Args:
        resource: Logical resource name the operation applies to (e.g., "issue").
        action: Logical action performed (e.g., "create", "update").
        result: The primary result object/value to return to the caller.
        **extra: Optional additional fields to include in the payload.

    Returns:
        A dict with keys: `resource`, `action`, `result`, plus any `extra` items.
    '''
    payload: Dict[str, Any] = {"resource": resource, "action": action, "result": result}
    payload.update(extra)
    return payload


# ---------------------------------------------------------------------------
# 1) Compartment Management Tool (optional but helpful if user has not enabled the oci-identity-mcp-server or added compartments to their memory bank)
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "List OCI compartments in the tenancy (including sub-compartments). "
        "Use this tool when the user provides a compartment *name* and you need the compartment OCID."
    )
)
def oci_ds_compartments(
    action: Literal["list"] = Field(
        "list", description="Action to perform. Only supported action is 'list'."
    ),
) -> Dict[str, Any]:
    try:
        config = get_oci_config()
        tenancy_id = config["tenancy"]
        identity_client = get_identity_client()

        response = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            tenancy_id,
            compartment_id_in_subtree=True,
            access_level="ANY",
        )

        compartments = [
            {
                "name": c.name,
                "id": c.id,
                "lifecycle_state": getattr(c, "lifecycle_state", None),
            }
            for c in response.data
        ]
        by_name = {c["name"]: c["id"] for c in compartments}
        return _ok(
            "compartments",
            action,
            {"by_name": by_name, "compartments": compartments},
        )
    except Exception:
        logger.exception("Error listing compartments")
        raise


# ---------------------------------------------------------------------------
# 2) Project Management Tool
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Manage OCI Data Science Projects. Supports create, list, update, delete, and count. "
        "Use 'list' to discover project OCIDs."
    )
)
def data_science_projects(
    action: Literal["create", "list", "update", "delete", "count"] = Field(
        ..., description="The project action to perform."
    ),
    compartment_id: str = Field(
        ..., description="OCID of the compartment containing the projects."
    ),
    project_id: Optional[str] = Field(
        None, description="Project OCID (required for update/delete)."
    ),
    project_name: Optional[str] = Field(
        None, description="Project display name (required for create)."
    ),
    project_description: Optional[str] = Field(
        None, description="Project description (optional for create)."
    ),
    new_name: Optional[str] = Field(
        None, description="New display name (used for update)."
    ),
    new_description: Optional[str] = Field(
        None, description="New description (used for update)."
    ),
    limit: Optional[int] = Field(
        None, description="Optional max number of projects to return for list.", ge=1
    ),
) -> Dict[str, Any]:
    try:
        pc = ProjectCatalog(compartment_id=compartment_id)

        if action == "count":
            pc.list_projects()
            return _ok("projects", action, len(pc), compartment_id=compartment_id)

        if action == "list":
            projects = pc.list_projects()
            rows = [
                {
                    "project_id": p.id,
                    "project_name": getattr(p, "display_name", None),
                    "project_description": getattr(p, "description", None),
                }
                for p in projects
            ]
            if limit is not None:
                rows = rows[:limit]
            return _ok("projects", action, rows, compartment_id=compartment_id)

        if action == "create":
            _require(project_name, "project_name", action=action)
            created = pc.create_project(
                display_name=project_name,
                description=project_description,
                compartment_id=compartment_id,
            )
            return _ok(
                "projects",
                action,
                {
                    "project_id": getattr(created, "id", None),
                    "project_name": getattr(created, "display_name", project_name),
                    "project_description": getattr(
                        created, "description", project_description
                    ),
                },
                next_actions=[
                    "data_science_notebook_sessions(action='create')",
                    "data_science_jobs(action='create_script'|'create_container')",
                ],
            )

        if action == "update":
            _require(project_id, "project_id", action=action)
            _at_least_one(
                ("new_name", new_name), ("new_description", new_description), action=action
            )
            kwargs: Dict[str, Any] = {}
            if new_name:
                kwargs["display_name"] = new_name
            if new_description:
                kwargs["description"] = new_description
            pc.update_project(project_id=project_id, **kwargs)
            return _ok(
                "projects",
                action,
                {"project_id": project_id, "updated": True},
                compartment_id=compartment_id,
            )

        if action == "delete":
            _require(project_id, "project_id", action=action)
            pc.delete_project(project_id)
            return _ok(
                "projects",
                action,
                {"project_id": project_id, "deleted": True},
                compartment_id=compartment_id,
            )

        raise ValueError(f"Unsupported action='{action}'")
    except Exception:
        logger.exception("Error in data_science_projects")
        raise


# ---------------------------------------------------------------------------
# 3) Model Catalog Management Tool
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Manage the OCI Data Science Model Catalog. Supports listing models, counting, downloading model artifacts, "
        "and interacting with Model Version Sets."
    )
)
def data_science_model_catalog(
    action: Literal[
        "list_models",
        "download",
        "count",
        "list_version_sets",
        "version_set_attributes",
    ] = Field(..., description="The model catalog action to perform."),
    compartment_id: str = Field(
        ..., description="OCID of the compartment that contains the model catalog."
    ),
    project_id: Optional[str] = Field(
        None,
        description=(
            "Optional project OCID. When provided with action='list_models', the server "
            "will request/return only models belonging to that project (reduces response size)."
        ),
    ),
    model_id: Optional[str] = Field(None, description="Model OCID (required for download)."),
    target_dir: Optional[str] = Field(
        None,
        description="Local directory to download the artifact into (required for download).",
    ),
    model_version_set_id: Optional[str] = Field(
        None,
        description="Model Version Set OCID (required for version_set_attributes).",
    ),
    limit: Optional[int] = Field(
        None, description="Optional max number of items to return for list actions.", ge=1
    ),
) -> Dict[str, Any]:
    try:
        if action == "count":
            mc = ModelCatalog(compartment_id=compartment_id)
            return _ok(
                "model_catalog",
                action,
                len(mc.list_models()),
                compartment_id=compartment_id,
            )

        if action == "list_models":
            mc = ModelCatalog(compartment_id=compartment_id)
            if project_id:
                # Prefer server-side filtering (OCI API supports project_id). Fall back to
                # client-side filtering for older ADS versions where list_models() may not
                # accept the parameter.
                try:
                    models = mc.list_models(project_id=project_id)
                except TypeError:
                    models = [
                        m
                        for m in mc.list_models()
                        if getattr(m, "project_id", None) == project_id
                    ]
            else:
                models = mc.list_models()
            result = [
                {
                    "model_id": getattr(m, "id", None),
                    "display_name": getattr(m, "display_name", None),
                    "model_version_set": getattr(m, "model_version_set_name", None),
                    "model_version_label": getattr(m, "version_label", None),
                    "model_version_id": getattr(m,"version_id",None),
                    "project_id":getattr(m,"project_id",None),
                    "lifecycle_state":getattr(m,"lifecycle_state",None),
                    "time_created": str(getattr(m, "time_created", ""))
                    if getattr(m, "time_created", None) is not None
                    else None,
                }
                for m in models
            ]
            if limit is not None:
                result = result[:limit]
            return _ok(
                "model_catalog",
                action,
                result,
                compartment_id=compartment_id,
            )

        if action == "download":
            _require(model_id, "model_id", action=action)
            _require(target_dir, "target_dir", action=action)
            # Prefer the explicit, supported ADS API for downloading artifacts:
            # 1) Load the model object
            # 2) Download artifacts directly into `resolved_target_dir`
            try:
                model = GenericModel.from_id(model_id)
                model.download_artifact(
                artifact_dir=target_dir,
                force_overwrite=True,
                remove_existing_artifact=True,
            )


            except Exception:
                    logger.exception(
                        "Download failed but failed"                    )

            downloaded_files = _list_files_recursive(target_dir)
            if not downloaded_files:
                logger.warning(
                    "Model download completed but no files were found in target_dir=%s (model_id=%s). ",
                    target_dir,
                    model_id,
                )

            return _ok(
                "model_catalog",
                action,
                {
                    "artifact_dir": target_dir,
                    "downloaded_files": downloaded_files,
                    "downloaded_files_count": len(downloaded_files)
                },
                compartment_id=compartment_id,
            )

        if action == "list_version_sets":
            ds_client = get_data_science_client()
            mvss = ds_client.list_model_version_sets(compartment_id=compartment_id).data
            result = [{"id": mvs.id, "name": mvs.name} for mvs in mvss]
            if limit is not None:
                result = result[:limit]
            return _ok(
                "model_catalog",
                action,
                result,
                compartment_id=compartment_id,
            )

        if action == "version_set_attributes":
            _require(model_version_set_id, "model_version_set_id", action=action)
            mvs = ModelVersionSet.from_id(model_version_set_id)
            return _ok(
                "model_catalog",
                action,
                mvs.to_dict(),
                compartment_id=compartment_id,
            )

        raise ValueError(f"Unsupported action='{action}'")
    except Exception:
        logger.exception("Error in data_science_model_catalog")
        raise


# ---------------------------------------------------------------------------
# 4) Job Management Tool
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Manage OCI Data Science Jobs. Supports creating jobs from scripts or container images, listing jobs, "
        "retrieving details, updating, and deleting jobs."
    )
)
def data_science_jobs(
    action: Literal[
        "create_script",
        "create_container",
        "list",
        "details",
        "update",
        "delete",
    ] = Field(..., description="The job action to perform."),
    compartment_id: Optional[str] = Field(
        None, description="Compartment OCID (required for list/create actions)."
    ),
    project_id: Optional[str] = Field(
        None, description="Project OCID (required for create actions)."
    ),
    job_id: Optional[str] = Field(
        None, description="Job OCID (required for details/update/delete actions)."
    ),
    display_name: Optional[str] = Field(
        None, description="Display name (required for create actions)."
    ),
    script_path: Optional[str] = Field(
        None, description="Local path to the script (required for create_script)."
    ),
    conda_env: str = Field(
        "generalml_p311_cpu_x86_64_v1",
        description="Service-managed conda environment for script jobs.",
    ),
    shape: str = Field(
        "VM.Standard2.2", description="Compute shape for the job infrastructure."
    ),
    ocpus: Optional[int] = Field(None, description="OCPUs (flex shapes).", ge=1),
    memory_in_gbs: Optional[float] = Field(
        None, description="Memory GB (flex shapes).", gt=0
    ),
    block_storage_size: int = Field(
        50, description="Block storage size in GB (must be >= 50).", ge=50
    ),
    image: Optional[str] = Field(
        None, description="Container image URL (required for create_container)."
    ),
    new_display_name: Optional[str] = Field(
        None, description="New display name (used for update)."
    ),
) -> Dict[str, Any]:
    try:
        if action == "list":
            _require(compartment_id, "compartment_id", action=action)
            jobs = DataScienceJob.list_jobs(compartment_id=compartment_id)
            return _ok(
                "jobs",
                action,
                [{"job_id": j.job_id, "job_name": j.name} for j in jobs],
                compartment_id=compartment_id,
            )

        if action == "details":
            _require(job_id, "job_id", action=action)
            job = Job.from_datascience_job(job_id)
            return _ok("jobs", action, job.to_dict())

        if action == "delete":
            _require(job_id, "job_id", action=action)
            Job.from_datascience_job(job_id).delete()
            return _ok("jobs", action, {"job_id": job_id, "deleted": True})

        if action == "create_script":
            _require(compartment_id, "compartment_id", action=action)
            _require(project_id, "project_id", action=action)
            _require(script_path, "script_path", action=action)
            _require(display_name, "display_name", action=action)

            infra = (
                DataScienceJob()
                .with_shape_name(shape)
                .with_compartment_id(compartment_id)
                .with_project_id(project_id)
                .with_block_storage_size(block_storage_size)
            )
            if ocpus is not None and memory_in_gbs is not None:
                infra = infra.with_shape_config_details(
                    memory_in_gbs=memory_in_gbs, ocpus=ocpus
                )

            job = (
                Job(name=display_name)
                .with_infrastructure(infra)
                .with_runtime(
                    ScriptRuntime().with_service_conda(conda_env).with_source(script_path)
                )
            )
            job.create()
            return _ok(
                "jobs",
                action,
                job.to_dict(),
                next_actions=["data_science_job_runs(action='start')"],
            )

        if action == "create_container":
            _require(compartment_id, "compartment_id", action=action)
            _require(project_id, "project_id", action=action)
            _require(image, "image", action=action)
            _require(display_name, "display_name", action=action)

            job = (
                Job(name=display_name)
                .with_infrastructure(
                    DataScienceJob()
                    .with_compartment_id(compartment_id)
                    .with_project_id(project_id)
                    .with_shape_name("VM.Standard2.1")
                )
                .with_runtime(ContainerRuntime().with_image(image).with_replica(1))
            )
            job.create()
            return _ok(
                "jobs",
                action,
                job.to_dict(),
                next_actions=["data_science_job_runs(action='start')"],
            )

        if action == "update":
            _require(job_id, "job_id", action=action)
            _at_least_one(("new_display_name", new_display_name), action=action)
            ds_client = get_data_science_client()
            ds_client.update_job(
                job_id=job_id,
                update_job_details=UpdateJobDetails(display_name=new_display_name),
            )
            return _ok("jobs", action, {"job_id": job_id, "updated": True})

        raise ValueError(f"Unsupported action='{action}'")
    except Exception:
        logger.exception("Error in data_science_jobs")
        raise


# ---------------------------------------------------------------------------
# 5) Job Run Management Tool
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Manage OCI Data Science Job Runs. Supports starting runs, listing runs, getting status, and cancelling runs."
    )
)
def data_science_job_runs(
    action: Literal["start", "list", "status", "cancel"] = Field(
        ..., description="The job run action to perform."
    ),
    compartment_id: Optional[str] = Field(
        None,
        description="Compartment OCID (required for start/list/status-by-job).",
    ),
    project_id: Optional[str] = Field(
        None, description="Project OCID (required for start)."
    ),
    job_id: Optional[str] = Field(
        None,
        description="Job OCID (required for start/status-by-job/cancel-by-job).",
    ),
    display_name: Optional[str] = Field(
        None, description="Display name for the job run (required for start)."
    ),
    job_run_id: Optional[str] = Field(
        None,
        description="Job Run OCID (optional for status/cancel; if omitted uses the most recent run for job_id).",
    ),
    limit: Optional[int] = Field(
        None, description="Optional max number of job runs to return for list.", ge=1
    ),
) -> Dict[str, Any]:
    try:
        ds_client = get_data_science_client()

        if action == "start":
            _require(compartment_id, "compartment_id", action=action)
            _require(project_id, "project_id", action=action)
            _require(job_id, "job_id", action=action)
            _require(display_name, "display_name", action=action)

            resp = ds_client.create_job_run(
                create_job_run_details=CreateJobRunDetails(
                    project_id=project_id,
                    compartment_id=compartment_id,
                    job_id=job_id,
                    display_name=display_name,
                )
            )
            data = resp.data
            return _ok(
                "job_runs",
                action,
                {
                    "job_run_id": getattr(data, "id", None),
                    "lifecycle_state": getattr(data, "lifecycle_state", None)
                    or getattr(data, "state", None),
                    "raw": oci.util.to_dict(data),
                },
            )

        if action == "list":
            _require(compartment_id, "compartment_id", action=action)
            kwargs: Dict[str, Any] = {"compartment_id": compartment_id}
            if job_id:
                kwargs["job_id"] = job_id
            if limit is not None:
                kwargs["limit"] = limit
            resp = ds_client.list_job_runs(**kwargs)
            return _ok(
                "job_runs",
                action,
                [oci.util.to_dict(run) for run in resp.data],
            )

        if action == "status":
            if job_run_id:
                data = ds_client.get_job_run(job_run_id=job_run_id).data
                return _ok("job_runs", action, oci.util.to_dict(data))

            _require(compartment_id, "compartment_id", action=action)
            _require(job_id, "job_id", action=action)
            resp = ds_client.list_job_runs(
                compartment_id=compartment_id,
                job_id=job_id,
                sort_by="timeCreated",
                sort_order="DESC",
                limit=1,
            )
            if not resp.data:
                return _ok(
                    "job_runs",
                    action,
                    None,
                    message="No job runs found.",
                )
            return _ok("job_runs", action, oci.util.to_dict(resp.data[0]))

        if action == "cancel":
            # Prefer explicit job_run_id.
            if not job_run_id:
                _require(compartment_id, "compartment_id", action=action)
                _require(job_id, "job_id", action=action)
                resp = ds_client.list_job_runs(
                    compartment_id=compartment_id,
                    job_id=job_id,
                    sort_by="timeCreated",
                    sort_order="DESC",
                    limit=1,
                )
                if not resp.data:
                    return _ok(
                        "job_runs",
                        action,
                        None,
                        message="No job runs found to cancel.",
                    )
                job_run_id = resp.data[0].id

            ds_client.cancel_job_run(job_run_id=job_run_id)
            return _ok(
                "job_runs",
                action,
                {"job_run_id": job_run_id, "cancel_requested": True},
            )

        raise ValueError(f"Unsupported action='{action}'")
    except Exception:
        logger.exception("Error in data_science_job_runs")
        raise


# ---------------------------------------------------------------------------
# 6) Notebook Session Management Tool
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Manage OCI Data Science Notebook Sessions. Supports create, activate, stop, delete, and list. "
        "Notebook session URLs can be used to open the session in the OCI console."
    )
)
def data_science_notebook_sessions(
    action: Literal["create", "activate", "stop", "delete", "list"] = Field(
        ..., description="Notebook session action to perform."
    ),
    compartment_id: Optional[str] = Field(
        None, description="Compartment OCID (required for create/list/activate)."
    ),
    project_id: Optional[str] = Field(
        None, description="Project OCID (required for create)."
    ),
    notebook_session_id: Optional[str] = Field(
        None, description="Notebook session OCID (required for activate/stop/delete)."
    ),
    display_name: Optional[str] = Field(
        None, description="Display name (required for create)."
    ),
    shape: str = Field(
        "VM.Standard2.1",
        description="Compute shape. Flexible shapes require ocpus + memory_in_gbs.",
    ),
    block_storage_size_in_gbs: int = Field(
        50, description="Block storage size in GB (>= 50).", ge=50
    ),
    subnet_id: Optional[str] = Field(None, description="Optional subnet OCID."),
    private_endpoint_id: Optional[str] = Field(
        None, description="Optional private endpoint OCID."
    ),
    ocpus: Optional[int] = Field(None, description="OCPUs (flex shapes).", ge=1),
    memory_in_gbs: Optional[int] = Field(None, description="Memory GB (flex shapes).", ge=1),
) -> Dict[str, Any]:
    try:
        ds_client = get_data_science_client()

        if action == "list":
            _require(compartment_id, "compartment_id", action=action)
            sessions = ds_client.list_notebook_sessions(compartment_id=compartment_id).data
            return _ok(
                "notebook_sessions",
                action,
                [
                    {
                        "id": s.id,
                        "name": s.display_name,
                        "lifecycle_state": s.lifecycle_state,
                    }
                    for s in sessions
                ],
                compartment_id=compartment_id,
            )

        if action == "create":
            _require(compartment_id, "compartment_id", action=action)
            _require(project_id, "project_id", action=action)
            _require(display_name, "display_name", action=action)

            flex_shapes = {"VM.Standard.E5.Flex", "VM.Standard.E4.Flex"}
            if shape in flex_shapes and (ocpus is None or memory_in_gbs is None):
                raise ValueError(
                    "For flexible shapes you must provide both ocpus and memory_in_gbs."
                )

            cfg_kwargs: Dict[str, Any] = {
                "shape": shape,
                "block_storage_size_in_gbs": block_storage_size_in_gbs,
            }
            if subnet_id:
                cfg_kwargs["subnet_id"] = subnet_id
            if private_endpoint_id:
                cfg_kwargs["private_endpoint_id"] = private_endpoint_id
            if ocpus is not None and memory_in_gbs is not None:
                cfg_kwargs["notebook_session_shape_config_details"] = (
                    NotebookSessionShapeConfigDetails(
                        ocpus=ocpus, memory_in_gbs=memory_in_gbs
                    )
                )

            notebook_cfg = NotebookSessionConfigDetails(**cfg_kwargs)
            details = CreateNotebookSessionDetails(
                display_name=display_name,
                project_id=project_id,
                compartment_id=compartment_id,
                notebook_session_config_details=notebook_cfg,
            )
            resp = ds_client.create_notebook_session(details)
            data = resp.data
            return _ok(
                "notebook_sessions",
                action,
                {
                    "id": getattr(data, "id", None),
                    "display_name": getattr(data, "display_name", None),
                    "time_created": str(getattr(data, "time_created", "")),
                    "notebook_session_url": getattr(data, "notebook_session_url", None),
                },
                next_actions=["data_science_notebook_sessions(action='activate')"],
            )

        if action == "activate":
            _require(compartment_id, "compartment_id", action=action)
            _require(notebook_session_id, "notebook_session_id", action=action)
            ds_client.activate_notebook_session(notebook_session_id)
            nb = ds_client.get_notebook_session(notebook_session_id).data
            return _ok(
                "notebook_sessions",
                action,
                {
                    "notebook_session_id": notebook_session_id,
                    "message": "Notebook session activating.",
                    "notebook_session_url": getattr(nb, "notebook_session_url", None),
                },
            )

        if action == "stop":
            _require(notebook_session_id, "notebook_session_id", action=action)
            ds_client.deactivate_notebook_session(notebook_session_id)
            return _ok(
                "notebook_sessions",
                action,
                {"notebook_session_id": notebook_session_id, "stopped": True},
            )

        if action == "delete":
            _require(notebook_session_id, "notebook_session_id", action=action)
            ds_client.delete_notebook_session(notebook_session_id)
            return _ok(
                "notebook_sessions",
                action,
                {"notebook_session_id": notebook_session_id, "deleted": True},
            )

        raise ValueError(f"Unsupported action='{action}'")
    except Exception:
        logger.exception("Error in data_science_notebook_sessions")
        raise


# ---------------------------------------------------------------------------
# 7) Pipeline Management Tool
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Manage OCI Data Science Pipelines. Supports list, details, and delete."
    )
)
def data_science_pipelines(
    action: Literal["list", "details", "delete"] = Field(
        ..., description="Pipeline action to perform."
    ),
    compartment_id: Optional[str] = Field(
        None, description="Compartment OCID (required for list)."
    ),
    pipeline_id: Optional[str] = Field(
        None, description="Pipeline OCID (required for details/delete)."
    ),
    limit: Optional[int] = Field(
        None, description="Optional max number of pipelines to return for list.", ge=1
    ),
) -> Dict[str, Any]:
    try:
        ds_client = get_data_science_client()

        if action == "list":
            _require(compartment_id, "compartment_id", action=action)
            pipes = ds_client.list_pipelines(compartment_id=compartment_id).data
            result = [{"id": p.id, "name": p.display_name} for p in pipes]
            if limit is not None:
                result = result[:limit]
            return _ok(
                "pipelines",
                action,
                result,
                compartment_id=compartment_id,
            )

        if action == "details":
            _require(pipeline_id, "pipeline_id", action=action)
            data = ds_client.get_pipeline(pipeline_id=pipeline_id).data
            return _ok("pipelines", action, oci.util.to_dict(data))

        if action == "delete":
            _require(pipeline_id, "pipeline_id", action=action)
            ds_client.delete_pipeline(pipeline_id=pipeline_id)
            return _ok(
                "pipelines",
                action,
                {"pipeline_id": pipeline_id, "delete_requested": True},
            )

        raise ValueError(f"Unsupported action='{action}'")
    except Exception:
        logger.exception("Error in data_science_pipelines")
        raise


# ---------------------------------------------------------------------------
# 8) Pipeline Run Management Tool
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Manage OCI Data Science Pipeline Runs. Supports starting runs, listing runs, and retrieving status."
    )
)
def data_science_pipeline_runs(
    action: Literal["start", "status", "list"] = Field(
        ..., description="Pipeline run action to perform."
    ),
    compartment_id: Optional[str] = Field(
        None, description="Compartment OCID (required for all actions)."
    ),
    pipeline_id: Optional[str] = Field(
        None, description="Pipeline OCID (required for all actions)."
    ),
    display_name: Optional[str] = Field(
        None, description="Optional run display name (used for start)."
    ),
    pipeline_run_id: Optional[str] = Field(
        None,
        description="Pipeline run OCID (optional for status; if omitted uses the most recent run for pipeline_id).",
    ),
    limit: Optional[int] = Field(
        None, description="Optional max number of runs to return for list.", ge=1
    ),
) -> Dict[str, Any]:
    try:
        _require(compartment_id, "compartment_id", action=action)
        _require(pipeline_id, "pipeline_id", action=action)
        ds_client = get_data_science_client()

        if action == "start":
            resp = ds_client.create_pipeline_run(
                CreatePipelineRunDetails(
                    compartment_id=compartment_id,
                    pipeline_id=pipeline_id,
                    display_name=display_name,
                )
            )
            data = resp.data
            return _ok(
                "pipeline_runs",
                action,
                {
                    "pipeline_run_id": getattr(data, "id", None),
                    "lifecycle_state": getattr(data, "lifecycle_state", None),
                    "raw": oci.util.to_dict(data),
                },
            )

        if action == "list":
            kwargs: Dict[str, Any] = {
                "compartment_id": compartment_id,
                "pipeline_id": pipeline_id,
            }
            if limit is not None:
                kwargs["limit"] = limit
            resp = ds_client.list_pipeline_runs(**kwargs)
            return _ok(
                "pipeline_runs",
                action,
                [oci.util.to_dict(run) for run in resp.data],
            )

        if action == "status":
            if pipeline_run_id:
                data = ds_client.get_pipeline_run(pipeline_run_id=pipeline_run_id).data
                return _ok("pipeline_runs", action, oci.util.to_dict(data))

            resp = ds_client.list_pipeline_runs(
                compartment_id=compartment_id,
                pipeline_id=pipeline_id,
                sort_by="timeAccepted",
                sort_order="DESC",
                limit=1,
            )
            if not resp.data:
                return _ok(
                    "pipeline_runs",
                    action,
                    None,
                    message="No pipeline runs found.",
                )
            return _ok("pipeline_runs", action, oci.util.to_dict(resp.data[0]))

        raise ValueError(f"Unsupported action='{action}'")
    except Exception:
        logger.exception("Error in data_science_pipeline_runs")
        raise


# ---------------------------------------------------------------------------
# 9) Model Deployment Management Tool
# ---------------------------------------------------------------------------


@mcp.tool(
    description=(
        "Manage OCI Data Science Model Deployments. Supports deploy, list, activate, deactivate, and delete. "
        "Deploy uses ADS GenericModel.deploy for conda-based deployments."
    )
)
def data_science_model_deployments(
    action: Literal["deploy", "activate", "deactivate", "delete", "list"] = Field(
        ..., description="Model deployment action to perform."
    ),
    compartment_id: Optional[str] = Field(
        None, description="Compartment OCID (required for deploy/list)."
    ),
    project_id: Optional[str] = Field(
        None, description="Project OCID (required for deploy)."
    ),
    model_id: Optional[str] = Field(
        None, description="Model OCID (required for deploy)."
    ),
    display_name: Optional[str] = Field(
        None, description="Deployment name (required for deploy)."
    ),
    deployment_id: Optional[str] = Field(
        None,
        description="Model deployment OCID (required for activate/deactivate/delete).",
    ),
    subnet_id: Optional[str] = Field(None, description="Optional subnet OCID."),
    log_group: Optional[str] = Field(None, description="Optional log group OCID."),
    access_log: Optional[str] = Field(None, description="Optional access log OCID."),
    predict_log: Optional[str] = Field(None, description="Optional predict log OCID."),
    shape: str = Field("VM.Standard.E2.1", description="Compute shape."),
    ocpus: Optional[int] = Field(None, description="OCPUs (flex shapes).", ge=1),
    memory_in_gbs: Optional[int] = Field(None, description="Memory GB (flex shapes).", ge=1),
    limit: Optional[int] = Field(
        None, description="Optional max number of deployments to return for list.", ge=1
    ),
) -> Dict[str, Any]:
    try:
        ds_client = get_data_science_client()

        if action == "list":
            _require(compartment_id, "compartment_id", action=action)
            deps = ds_client.list_model_deployments(compartment_id=compartment_id).data
            result = [
                {
                    "id": d.id,
                    "name": d.display_name,
                    "lifecycle_state": d.lifecycle_state,
                }
                for d in deps
            ]
            if limit is not None:
                result = result[:limit]
            return _ok(
                "model_deployments",
                action,
                result,
                compartment_id=compartment_id,
            )

        if action == "deploy":
            _require(compartment_id, "compartment_id", action=action)
            _require(project_id, "project_id", action=action)
            _require(model_id, "model_id", action=action)
            _require(display_name, "display_name", action=action)

            model = GenericModel.from_id(model_id)
            kwargs: Dict[str, Any] = {"deployment_instance_shape": shape}
            if subnet_id:
                kwargs["subnet_id"] = subnet_id
            if log_group:
                kwargs["deployment_log_group_id"] = log_group
            if access_log:
                kwargs["deployment_access_log_id"] = access_log
            if predict_log:
                kwargs["deployment_predict_log_id"] = predict_log
            if ocpus is not None:
                kwargs["deployment_ocpus"] = ocpus
            if memory_in_gbs is not None:
                kwargs["deployment_memory_in_gbs"] = memory_in_gbs

            deployment = model.deploy(
                display_name=display_name,
                project_id=project_id,
                compartment_id=compartment_id,
                **kwargs,
            )
            md = deployment.model_deployment
            return _ok(
                "model_deployments",
                action,
                {
                    "deployment_id": getattr(md, "id", None),
                    "url": getattr(md, "url", None),
                },
                next_actions=["data_science_model_deployments(action='activate')"],
            )

        if action == "activate":
            _require(deployment_id, "deployment_id", action=action)
            ds_client.activate_model_deployment(model_deployment_id=deployment_id)
            return _ok(
                "model_deployments",
                action,
                {"deployment_id": deployment_id, "activate_requested": True},
            )

        if action == "deactivate":
            _require(deployment_id, "deployment_id", action=action)
            ds_client.deactivate_model_deployment(model_deployment_id=deployment_id)
            return _ok(
                "model_deployments",
                action,
                {"deployment_id": deployment_id, "deactivate_requested": True},
            )

        if action == "delete":
            _require(deployment_id, "deployment_id", action=action)
            ds_client.delete_model_deployment(model_deployment_id=deployment_id)
            return _ok(
                "model_deployments",
                action,
                {"deployment_id": deployment_id, "delete_requested": True},
            )

        raise ValueError(f"Unsupported action='{action}'")
    except Exception:
        logger.exception("Error in data_science_model_deployments")
        raise


@mcp.resource("resource://config")
def get_config() -> dict:
    return {"version": "2.0", "author": "FastMCP", "server": __project__}


def main() -> None:
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")
    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
