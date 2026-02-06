"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from fastmcp import FastMCP
import ads
from ads.catalog.project import ProjectCatalog
from ads.catalog.model import ModelCatalog
import logging
import sys
from starlette.responses import JSONResponse
from typing import Any, Dict, List
import pandas as pd
import oci
from . import __project__, __version__
from ads.model import ModelVersionSet#, Model
from ads.jobs import Job, DataScienceJobRun, DataScienceJob
from ads.pipeline import Pipeline, PipelineStep
from ads.model.generic_model import GenericModel
from ads.model.framework.sklearn_model import SklearnModel
import pickle
from joblib import load
from oci.data_science.models import (
    NotebookSessionSummary,
    UpdateNotebookSessionDetails,
    CreateNotebookSessionDetails,
    NotebookSession,
    NotebookSessionConfigurationDetails,
    NotebookSessionConfigDetails,
    NotebookSessionShapeConfigDetails,
)
from ads.model.deployment import ModelDeployment, ModelDeploymentInfrastructure, ModelDeploymentRuntime
import yaml
import requests
from ads.jobs import Job, DataScienceJob, ScriptRuntime,ContainerRuntime
from ads.catalog import notebook

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

mcp = FastMCP(name=__project__)

ads.set_auth("api_key") # this assumes users have setup API key via OCI SDK.

def log_request(tool_name: str, **kwargs):
    logger.debug(f"[REQUEST RECEIVED] Tool: {tool_name}, Args: {kwargs}")

def log_response(tool_name: str, result):
    logger.debug(f"[RESPONSE SENT] Tool: {tool_name}, Result: {result}")


@mcp.tool()
def get_datascience_compartment_id() -> Any:
    """ Get a list of Compartment OCID by Compartment name for use with other tools. Important - use this tool to initialise the compartment_id variable. 
    
    Returns:
        compartment_dict: OCI compartment ID and OCI Compartment name as key-value pairs
    """

    try:
        config = oci.config.from_file()
        identity_client = oci.identity.IdentityClient(config)
        tenancy_id = config['tenancy']

        # List compartments in tenancy, including sub-compartments
        compartment_list = []
        response = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            tenancy_id,
            compartment_id_in_subtree=True,
            access_level='ANY'
        )

        # Build dict {compartment_name: compartment_ocid}
        compartment_dict = {}
        for compartment in response.data:
            compartment_dict[compartment.name] = compartment.id
        
        return compartment_dict


    except Exception as e:
        logger.exception("Error getting project count")
        raise


@mcp.tool()
def project_count(compartment_id) -> int:
    """Get count of OCI Data Science Projects
    
    Args:
        compartment_id: OCI compartment ID
    
    Returns:
        Number of projects in the compartment
    """
    
    logger.debug("calling project_count tool successfully")
    
    try:
        project_catalog = ProjectCatalog(compartment_id=compartment_id)
        projects = project_catalog.list_projects()
        num_projects = len(project_catalog)
        return num_projects
    except Exception as e:
        logger.exception("Error getting project count")
        raise


@mcp.tool()
def create_project(project_name,project_description,compartment_id) -> Dict:
    """ Create new OCI Data Science Project with project name and description.
    
    Args:
        compartment_id: OCI compartment ID. 
        project_name: a name for the new project, for example 'Customer Churn Project'
        project_description: a description of the new project, for example 'Customer Churn modelling using binary classification'
    
    Returns:
        Dictionary of new project details
    """
    try:
        project_catalog = ProjectCatalog(compartment_id)
        res = project_catalog.create_project(display_name=project_name,description=project_description,compartment_id=compartment_id)
        return res.to_dataframe().to_dict()

    except Exception as e:
        logger.exception("Error getting project count")
        raise

@mcp.tool()
def model_count(compartment_id) -> int:
    """Returns number of models saved to model catalog in OCI Data Science for a given compartment
    
    Args:
        compartment_id: OCI compartment ID. If not provided, will use environment variable COMPARTMENT_ID
    
    Returns:
        Number of models in the model catalog
    """

    try:
        model_catalog = ModelCatalog(compartment_id=compartment_id)
        models = model_catalog.list_models()
        num_models = len(models)
        return num_models
    except Exception as e:
        logger.exception("Error getting model count")
        raise

@mcp.tool()
def list_projects(compartment_id) -> Dict:
    ''' returns a list of OCI Data Science Projects by Project Name, Project ID and Project Description as a dictionary 
    
        Args:
        compartment_id: OCI compartment ID. If not provided, will use environment variable COMPARTMENT_ID
    
    Returns:
        List of OCI Data Science Projects in a compartment
    
    '''
    try:
        project_catalog = ProjectCatalog(compartment_id)
        projects = project_catalog.list_projects()
        project_id = []
        project_name = []
        project_desc = []
        for i in range(len(projects)):
            project_id.append(projects[i].id)
            project_name.append(projects[i].display_name)
            project_desc.append(projects[i].description)

        projects_df = pd.DataFrame({'project_id':project_id,'project_name':project_name,'project_description':project_desc}).to_dict('records')
        return projects_df
    except Exception as e:
        logger.exception("Error getting project list")
        raise

@mcp.tool()
def create_notebook_session(project_id=None,compartment_id=None,display_name=None,shape='VM.Standard2.1',block_storage_size_in_gbs=50,subnet_id=None,private_endpoint_id=None,ocpus=None,memory_in_gbs=None,) -> Dict:
    ''' Creates a managed Notebook Session on OCI Data Science in a given Project and Compartment.
    
        Args:
        compartment_id: OCI compartment ID.
        project_id: OCI Data Science Project OCID. 
        display_name: A meaningful name for the notebook session
        shape: compute shape. Valid options for non-flexible shapes are: [“VM.Standard2.2”, “VM.Standard2.1”, “VM.Standard2.4”, “VM.Standard2.8”, “VM.Standard2.16”, “VM.Standard2.24”]
        valid options for flexible shapes are: ["VM.Standard.E5.Flex","VM.Standard.E4.Flex"]
        if you select a flexible shape you MUST also provide ocpus and memory_in_gbs parameters as well. For example:
        
            VM.Standard.E5.Flex with 2 OCPUs and 16 GB memory would have ocpus=2 and memory_in_gbs = 16

        if the user does not give a shape explicitly, default the shape to “VM.Standard2.1”

        if the user does not give a block storage size explicitly, set block_storage_size_in_gbs to 50 which is the minimum storage accepted.

    Returns:
        Details of Notebook Session. It is important to share the Notebook URL correctly as it will be used to access the session.
    
    '''
    try:
        config = oci.config.from_file()
        ds_client = oci.data_science.DataScienceClient(config)
        config_kwargs = dict(shape=shape,)

        if block_storage_size_in_gbs:
            config_kwargs["block_storage_size_in_gbs"] = block_storage_size_in_gbs

        
        if subnet_id:
            config_kwargs["subnet_id"] = subnet_id
        if private_endpoint_id:
            config_kwargs["private_endpoint_id"] = private_endpoint_id
        if ocpus is not None and memory_in_gbs is not None:
            config_kwargs["notebook_session_shape_config_details"] = NotebookSessionShapeConfigDetails(ocpus=ocpus, memory_in_gbs=memory_in_gbs)

        # notebook config object
        notebook_cfg = NotebookSessionConfigDetails(**config_kwargs)

        # create request details
        create_notebook_details = CreateNotebookSessionDetails(
            display_name=display_name,
            project_id=project_id,
            compartment_id=compartment_id,
            notebook_session_config_details=notebook_cfg,  
        )

        create_notebook_session_response = ds_client.create_notebook_session(
                create_notebook_details,)

        
        notebook_dict = {}
        notebook_dict['notebook_session_url']=create_notebook_session_response.data.notebook_session_url
        notebook_dict['display_name']=create_notebook_session_response.data.display_name
        notebook_dict['time_created']=create_notebook_session_response.data.time_created
        #notebook_dict['session_details']=create_notebook_session_response.data.notebook_session_config_details
        return notebook_dict
    except Exception as e:
        logger.exception("Error creating notebook session")
        raise


@mcp.tool()
def list_model_version_set_attributes(compartment_id, model_version_set_id) -> Dict:
    """List attributes of a Model Version Set.
    
    Args:
        compartment_id: OCI compartment ID.
        model_version_set_id: ID of the model version set.
    
    Returns:
        Dictionary of model version set attributes.
    """
    try:
        mvs = ModelVersionSet.from_id(model_version_set_id)
        return mvs.to_dict()
    except Exception as e:
        logger.exception("Error listing model version set attributes")
        raise

@mcp.tool()
def list_model_version_sets(compartment_id) -> List[Dict]:
    """List all Model Version Sets in a compartment with their IDs and names.
    
    Args:
        compartment_id: OCI compartment ID.
    
    Returns:
        List of dictionaries with model version set IDs and names.
    """
    try:
        config = oci.config.from_file()
        ds_client = oci.data_science.DataScienceClient(config=config)
        mvss = ds_client.list_model_version_sets(compartment_id=compartment_id).data
        return [{"id": mvs.id, "name": mvs.name} for mvs in mvss]
    except Exception as e:
        logger.exception("Error listing model version sets")
        raise



@mcp.tool()
def download_model_artefact(model_id, target_dir) -> str:
    """Download model artifact from the catalog.
    
    Args:
        model_id: ID of the model.
        target_dir: Directory to download the artifact to.
    
    Returns:
        Information about the downloaded artifact
    """
    try:
        model = GenericModel.from_model_catalog(model_id,target_dir,force_overwrite=True,remove_existing_artifact=True)

        # seems to be an issue in cline where it downloads to tmp dir and not target dir.

        return model._to_yaml()
    except Exception as e:
        logger.exception("Error downloading model artefact")
        raise

@mcp.tool()
def create_job_from_script(compartment_id, project_id, script_path, display_name,conda_env='generalml_p311_cpu_x86_64_v1',shape='VM.Standard2.2',ocpus=None,memory_in_gbs=None,block_storage_size=50) -> Dict:
    """Create a job from a script. Currently only implemented to support service_conda runtimes.
    
    Args:
        compartment_id: OCI compartment ID.
        project_id: OCI Data Science Project OCID.
        script_path: Path to the script.
        display_name: Name of the job.
        conda_env: service managed conda environment. Valid options include ['automlx251_p311_cpu_x86_64_v2','generalml_p311_cpu_x86_64_v1'] default to 
        shape: compute shape. Valid options for non-flexible shapes are: [“VM.Standard2.2”, “VM.Standard2.1”, “VM.Standard2.4”, “VM.Standard2.8”, “VM.Standard2.16”, “VM.Standard2.24”]
        valid options for flexible shapes are: ["VM.Standard.E5.Flex","VM.Standard.E4.Flex"]
        if you select a flexible shape you MUST also provide ocpus and memory_in_gbs parameters as well. For example:
        
            VM.Standard.E5.Flex with 2 OCPUs and 16 GB memory would have ocpus=2 and memory_in_gbs = 16

        if the user does not give a shape explicitly, default the shape to “VM.Standard2.1”
        block_storage_size : size of block storage. must be at least 50
    
    Returns:
        Dictionary of created job details.
    """
    try:
        if ocpus and memory_in_gbs:
            job = (Job(name=display_name).with_infrastructure(DataScienceJob()
                .with_shape_name(shape)
            .with_compartment_id(compartment_id)
            .with_project_id(project_id)
        .with_shape_config_details(memory_in_gbs=memory_in_gbs, ocpus=ocpus)
        .with_block_storage_size(block_storage_size))
            .with_runtime(ScriptRuntime()
        .with_service_conda(conda_env)
        .with_source(script_path)))

        else:
            job = (Job(name=display_name).with_infrastructure(DataScienceJob()
                .with_shape_name(shape)
            .with_compartment_id(compartment_id)
            .with_project_id(project_id)
        .with_block_storage_size(block_storage_size))
            .with_runtime(ScriptRuntime()
        .with_service_conda(conda_env)
        .with_source(script_path)))
        
        job.create()
        return job.to_dict()
    except Exception as e:
        logger.exception("Error creating job from script")
        raise

@mcp.tool()
def list_models(compartment_id) -> Dict:
    """List models in the model catalog.
    
    Args:
        compartment_id: OCI compartment ID.
    
    Returns:
        List of models as dictionary.
    """
    try:
        mc = ModelCatalog(compartment_id=compartment_id)
        models = mc.list_models()
        return [model._to_dict() for model in models]
    except Exception as e:
        logger.exception("Error listing models")
        raise

@mcp.tool()
def list_jobs(compartment_id) -> List[Dict]:
    """List all jobs in a compartment with their IDs and names.
    
    Args:
        compartment_id: OCI compartment ID.
    
    Returns:
        List of dictionaries with job IDs and names.
    """
    try:
        jobs = DataScienceJob.list_jobs(compartment_id=compartment_id)
        jobs_list = []
        for i in range(len(jobs)):
            jobs_list.append({'job_id':jobs[i].job_id,'job_name':jobs[i].name})
        return jobs_list
    except Exception as e:
        logger.exception("Error listing jobs")
        raise

@mcp.tool()
def job_details_by_id(compartment_id, job_id) -> Dict:
    """List jobs information for a job based on its Job ID.
    
    Args:
        compartment_id: OCI compartment ID.
        job_id: ID of the job.
    
    Returns:
        Dictionary of job details.
    """
    try:
        job = Job.from_datascience_job(job_id)
        return job.to_dict()
    except Exception as e:
        logger.exception("Error listing jobs by id")
        raise

@mcp.tool()
def list_pipelines(compartment_id) -> List[Dict]:
    """List all pipelines in a compartment with their IDs and names.
    
    Args:
        compartment_id: OCI compartment ID.
    
    Returns:
        List of dictionaries with pipeline IDs and names.
    """
    try:
        config = oci.config.from_file()
        ds_client = oci.data_science.DataScienceClient(config=config)
        pipelines = ds_client.list_pipelines(compartment_id=compartment_id).data
        return [{"id": pipeline.id, "name": pipeline.display_name} for pipeline in pipelines]
    except Exception as e:
        logger.exception("Error listing pipelines")
        raise

@mcp.tool()
def pipelines_details_by_id(compartment_id, pipeline_id) -> Dict:
    """List pipeline details by Pipeline ID.
    
    Args:
        compartment_id: OCI compartment ID.
        pipeline_id: ID of the pipeline.
    
    Returns:
        Dictionary of pipeline details.
    """
    try:
        pipeline = Pipeline.from_id(pipeline_id)
        return pipeline.to_dict()
    except Exception as e:
        logger.exception("Error listing pipelines by id")
        raise

@mcp.tool()
def start_job_run(job_id,compartment_id,project_id,display_name) -> Dict:
    """Start a job run.
    
    Args:
        job_id: ID of the job to run.
        compartment_id: the compartment of the data science job
        project_id: the project_id of the data science job

    
    Returns:
        Dictionary of job run details.
    """
    try:
        config = oci.config.from_file()
        ds_client = oci.data_science.DataScienceClient(config=config)
        create_job_run_response = ds_client.create_job_run(
        create_job_run_details=oci.data_science.models.CreateJobRunDetails(
        project_id=project_id,
        compartment_id=compartment_id,
        job_id=job_id,
        display_name=display_name))

        return create_job_run_response.data.__dict__

    except Exception as e:
        logger.exception("Error starting job run")
        raise

@mcp.tool()
def start_pipeline_run(compartment_id,pipeline_id,display_name=None) -> str:
    """Start a pipeline run. Use list_pipelines to find the pipeline_id by name. give the run a meaningful name if possible.
    
    Args:
        pipeline_id: ID of the pipeline to run.
        compartment_id: Compartment OCID where the pipeline was created.
        display_name: a meaningful name for the pipeline run (optional but preferred)
    
    Returns:
        Dictionary of pipeline run details.
    """
    try:

        config = oci.config.from_file()  

        # Create a Data Science client
        ds_client = oci.data_science.DataScienceClient(config)

        # Pipeline Run details:
        create_pipeline_run_details = oci.data_science.models.CreatePipelineRunDetails(
            compartment_id=compartment_id,
            pipeline_id=pipeline_id,
            display_name=display_name
        )

        # Submit the pipeline run
        response = ds_client.create_pipeline_run(create_pipeline_run_details)

        return response.data.lifecycle_state

    except Exception as e:
        logger.exception("Error starting pipeline run")
        raise

@mcp.tool()
def create_job_from_container_image(compartment_id, project_id, image, display_name) -> Dict:
    """Create a job from a container image.
    
    Args:
        compartment_id: OCI compartment ID.
        project_id: OCI Data Science Project OCID.
        image: Container image URL.
        display_name: Name of the job.
    
    Returns:
        Dictionary of created job details.
    """
    try:
        job = Job(name=display_name) .with_infrastructure(
        DataScienceJob()
        .with_compartment_id(compartment_id)
        .with_project_id(project_id)
        .with_shape_name("VM.Standard2.1")).with_runtime(ContainerRuntime().with_image(image).with_replica(1))
        job.create()
        return job.to_dict()
    except Exception as e:
        logger.exception("Error creating job from container image")
        raise

@mcp.tool()
def delete_project(compartment_id,project_id) -> str:
    """Delete an OCI Data Science Project. Find the Project ID by calling List Projects and finding the Project ID associated with a Project Name.
    
    Args:
        project_id: OCI Data Science Project OCID.
        compartment_id: OCI Data Science Compartment OCID.
    
    Returns:
        Confirmation message.
    """
    try:
        pc = ProjectCatalog(compartment_id=compartment_id)
        pc.delete_project(project_id)
        return f"Project {project_id} deleted successfully."
    except Exception as e:
        logger.exception("Error deleting project")
        raise

@mcp.tool()
def activate_notebook_session(compartment_id,notebook_session_id) -> str:
    """ Activates a notebook session. Use list_notebook_sessions to find a notebook session id by name.
    
    Args:
        compartment_id: the OCID of the compartment where the notebook is saved.
        notebook_session_id: ID of the notebook session.
    
    Returns:
        Confirmation message with URL for the active notebook session.
    """
    try:
        config = oci.config.from_file()
        ds_client = oci.data_science.DataScienceClient(config)
        ds_client.activate_notebook_session(notebook_session_id)
        # get session url

        nb_session = notebook.NotebookCatalog(compartment_id).get_notebook_session(notebook_session_id)
        nb_url = nb_session.notebook_session_url
        return "Notebook session activating. The URL for Notebook Session is: {}".format(nb_url)

    except Exception as e:
        logger.exception("Error deleting notebook session")
        raise

@mcp.tool()
def delete_notebook_session(notebook_session_id) -> str:
    """Delete a notebook session.
    
    Args:
        notebook_session_id: ID of the notebook session.
    
    Returns:
        Confirmation message.
    """
    try:
        config = oci.config.from_file()
        ds_client = oci.data_science.DataScienceClient(config)
        ds_client.delete_notebook_session(notebook_session_id)
        return f"Notebook session {notebook_session_id} deleted successfully."
    except Exception as e:
        logger.exception("Error deleting notebook session")
        raise

@mcp.tool()
def stop_notebook_session(notebook_session_id) -> str:
    """Stop (deactivate) a notebook session.
    
    Args:
        notebook_session_id: ID of the notebook session.
    
    Returns:
        Confirmation message.
    """
    try:
        config = oci.config.from_file()
        ds_client = oci.data_science.DataScienceClient(config)
        ds_client.deactivate_notebook_session(notebook_session_id)
        return f"Notebook session {notebook_session_id} stopped successfully."
    except Exception as e:
        logger.exception("Error stopping notebook session")
        raise

@mcp.tool()
def delete_job(job_id) -> str:
    """Delete a job.
    
    Args:
        job_id: ID of the job.
    
    Returns:
        Confirmation message.
    """
    try:
        job = Job.from_datascience_job(job_id)
        job.delete()
        return f"Job {job_id} deleted successfully."
    except Exception as e:
        logger.exception("Error deleting job")
        raise

@mcp.tool()
def delete_pipeline(pipeline_id) -> str:
    """Delete a pipeline.
    
    Args:
        pipeline_id: ID of the pipeline.
    
    Returns:
        Confirmation message.
    """
    try:
        pipeline = Pipeline.from_ocid(pipeline_id)
        pipeline.delete()
        return f"Pipeline {pipeline_id} deleted successfully."
    except Exception as e:
        logger.exception("Error deleting pipeline")
        raise

@mcp.tool()
def deploy_model(model_id, compartment_id, project_id, display_name,subnet_id=None,log_group=None,access_log=None,predict_log=None, shape='VM.Standard.E2.1',ocpus=None,memory_in_gbs=None) -> Dict:
    """Deploy a model from the catalog as a model deployment. Only works for Conda based runtimes currently. Assumes you have already saved the model to the model catalog separately
    
    Args:
        model_id: ID of the model to deploy.
        compartment_id: OCI compartment ID.
        project_id: OCI Data Science Project OCID.
        display_name: Name of the deployment.
        shape: Compute shape for the deployment (default: 'VM.Standard.E2.1').
        subnet_id: subnet for custom VCN (optional)
        log_group: log group ocid for logging (optional)
        access_log: log within log group used for monitoring access (optional)
        predict_log: log within log group used for monitoring predictions (optional)
        ocpus: OCPUs allocated to compute if using a flexible shape
        memory_in_gbs: memory allocated to compute if using a flexible shape
    
    Returns:
        Dictionary of deployment details.
    """
    try:
        model = GenericModel.from_id(model_id)
        deployment_kwargs = {}
        if subnet_id:
            deployment_kwargs['subnet_id'] = subnet_id
        if log_group:
            deployment_kwargs['deployment_log_group_id'] = log_group

        if access_log:
            deployment_kwargs['deployment_access_log_id'] = access_log
        
        if predict_log:
            deployment_kwargs['deployment_predict_log_id'] = predict_log

        if ocpus:
            deployment_kwargs['deployment_ocpus'] = ocpus

        if memory_in_gbs:
            deployment_kwargs['deployment_memory_in_gbs'] = memory_in_gbs

        if shape:
            deployment_kwargs['deployment_instance_shape'] = shape

        deployment = model.deploy(
            display_name=display_name,
            project_id=project_id,
            compartment_id=compartment_id,
            **deployment_kwargs)

        return deployment.model_deployment.url
    except Exception as e:
        logger.exception("Error deploying model")
        raise

@mcp.tool()
def activate_model_deployment(deployment_id) -> str:
    """Activate an existing model deployment.
    
    Args:
        deployment_id: ID of the model deployment to activate.
    
    Returns:
        Dictionary of deployment details after activation.
    """
    try:
        deployment = ModelDeployment.from_id(deployment_id)
        deployment.activate()
        return 'Activating Model Deployment'
    except Exception as e:
        logger.exception("Error activating model deployment")
        raise

@mcp.tool()
def deactivate_model_deployment(deployment_id) -> str:
    """Deactivate (stop) a running model deployment.
    
    Args:
        deployment_id: ID of the model deployment to deactivate.
    
    Returns:
        Dictionary of deployment details after deactivation.
    """
    try:
        deployment = ModelDeployment.from_id(deployment_id)
        deployment.deactivate()
        return 'Deactivating Model Deployment'
    except Exception as e:
        logger.exception("Error deactivating model deployment")
        raise

@mcp.tool()
def list_notebook_sessions(compartment_id) -> List[Dict]:
    """List all notebook sessions in a compartment with their IDs, names, and statuses.
    
    Args:
        compartment_id: OCI compartment ID.
    
    Returns:
        List of dictionaries with notebook session details.
    """
    try:
        config = oci.config.from_file()
        ds_client = oci.data_science.DataScienceClient(config)
        sessions = ds_client.list_notebook_sessions(compartment_id=compartment_id).data
        return [{"id": session.id, "name": session.display_name, "lifecycle_state": session.lifecycle_state} for session in sessions]
    except Exception as e:
        logger.exception("Error listing notebook sessions")
        raise

@mcp.tool()
def update_project(compartment_id,project_id, new_name=None, new_description=None) -> str:
    """Update an existing project's details such as name or description.
    
    Args:
        compartment_id: compartment containing the project catalog
        project_id: OCI Data Science Project OCID.
        new_name: New name for the project (optional).
        new_description: New description for the project (optional).
    
    Returns:
        Dictionary of updated project details.
    """
    try:
        pc = ProjectCatalog(compartment_id)

        project_kwargs = {}

        if new_name:
            project_kwargs['display_name'] = new_name
        if new_description:
            project_kwargs['description'] = new_description
        updated_project = pc.update_project(project_id=project_id,**project_kwargs)
        return 'Project updated successfully'
    except Exception as e:
        logger.exception("Error updating project")
        raise

@mcp.tool()
def list_model_deployments(compartment_id) -> Dict[str, List[Dict]]:
    """List all model deployments in a compartment with their IDs, names, and statuses.
    
    Args:
        compartment_id: OCI compartment ID.
    
    Returns:
        List of dictionaries with model deployment details.
    """
    try:
        config = oci.config.from_file()
        ds_client = oci.data_science.DataScienceClient(config=config)
        deployments = ds_client.list_model_deployments(compartment_id=compartment_id).data
        return {"deployments": [{"id": dep.id, "name": dep.display_name, "lifecycle_state": dep.lifecycle_state} for dep in deployments]}
    except Exception as e:
        logger.exception("Error listing model deployments")
        raise


@mcp.tool()
def get_pipeline_run_status(pipeline_id, compartment_id) -> Dict:
    """Get the status and details of the most recent pipeline run for a given pipeline.
    This tool can be used to:
    - get the current status
    - get the started, accepted or finished date and time
    
    Args:
        pipeline_id: OCID of the pipeline.
        compartment_id: Compartment of the pipeline.
    
    Returns:
        Dictionary of pipeline run status and details.
    """
    try:
        config = oci.config.from_file()
        data_science_client = oci.data_science.DataScienceClient(config)
        
        response = data_science_client.list_pipeline_runs(
            compartment_id=compartment_id,
            pipeline_id=pipeline_id,
            sort_by="timeAccepted",
            sort_order="DESC",
            limit=1  # Only need the most recent
        )
        pipeline_runs = response.data
        if not pipeline_runs:
            return {}
        return pipeline_runs[0].__dict__
    except Exception as e:
        logger.exception("Error getting pipeline run status")
        raise


@mcp.tool()
def get_job_run_status(job_id,compartment_id) -> Dict:
    """Get the status and details of the most recent job run for a given job.
    This tool can be used to:
    - get the current status
    - get the started, accepted or finished date and time
    
    Args:
        job_id: ID of the job run.
        compartment_id: Compartment of the job
    
    Returns:
        Dictionary of job run status and details.
    """
    try:
        config = oci.config.from_file()
        data_science_client = oci.data_science.DataScienceClient(config)
        response = data_science_client.list_job_runs(
            compartment_id=compartment_id,
            job_id=job_id,
            sort_by="timeCreated",
            sort_order="DESC",
            limit=1  # Only need the most recent
        )
        job_runs = response.data
        if not job_runs:
            return {}
        return job_runs[0].__dict__
    except Exception as e:
        logger.exception("Error getting job run status")
        raise


@mcp.tool()
def list_job_runs(compartment_id,job_id=None) -> List[Dict]:
    """List all runs for a specific job, including their statuses and details.
    
    Args:
        compartment_id: ocid of compartment
        job_id: ID of the job. this is optional. if not specified, return job runs for all jobs in compartment
    
    Returns:
        List of job run dictionaries.
    """
    try:
        config = oci.config.from_file() 
        dsc_client = oci.data_science.DataScienceClient(config)

        kwargs = {'compartment_id': compartment_id}
        if job_id:
            kwargs['job_id'] = job_id

        response = dsc_client.list_job_runs(**kwargs)

        return [oci.util.to_dict(run) for run in response.data]
    except Exception as e:
        logger.exception("Error listing job runs")
        raise

@mcp.tool()
def cancel_job_run(job_id) -> str:
    """Cancel a currently running job run.
    
    Args:
        job_id: ID of the job to cancel. This cancels the job run which is assumed to be the most recent job run of a job.
    
    Returns:
        Confirmation message with updated status.
    """
    try:
        run = Job.from_datascience_job(job_id)
        job_run_id = run.run_list()[0].id
        job_run = DataScienceJobRun.from_ocid(job_run_id)

        job_run.cancel()
        return f"Job run {job_run_id} cancelled successfully. Current status: {job_run.lifecycle_state}"
    except Exception as e:
        logger.exception("Error cancelling job run")
        raise



@mcp.tool()
def list_pipeline_runs(compartment_id,pipeline_id) -> List[Dict]:
    """List all runs for a specific pipeline, including statuses and details.
    
    Args:
        pipeline_id: ID of the pipeline.
        compartment_id: ID of OCI Compartment
    
    Returns:
        List of pipeline run dictionaries.
    """
    try:
        config = oci.config.from_file()  # uses ~/.oci/config by default
        data_science_client = oci.data_science.DataScienceClient(config)

        # List pipeline runs
        response = data_science_client.list_pipeline_runs(compartment_id=compartment_id,pipeline_id=pipeline_id)

        return [run.__dict__ for run in response.data]
    except Exception as e:
        logger.exception("Error listing pipeline runs")
        raise

@mcp.tool()
def delete_model_deployment(deployment_id) -> str:
    """Delete a model deployment.
    
    Args:
        deployment_id: ID of the model deployment.
    
    Returns:
        Confirmation message.
    """
    try:
        deployment = ModelDeployment.from_id(deployment_id)
        deployment.delete()
        return f"Model deployment {deployment_id} deleted successfully."
    except Exception as e:
        logger.exception("Error deleting model deployment")
        raise


@mcp.resource("resource://config")
def get_config() -> dict:
    return {"version": "1.1", "author": "FastMCP"}


def main():
    mcp.run()

if __name__ == "__main__":
    main()
