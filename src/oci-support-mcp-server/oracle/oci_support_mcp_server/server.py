"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Annotated, List, Optional

import oci
from fastmcp import FastMCP
from oracle.oci_support_mcp_server.models import (
    IncidentSummary,
    map_incident_summary,
    Incident,
    map_incident,
    CreateIncident,
)
from pydantic import Field

__project__ = "oracle.oci_support_mcp_server"
__version__ = "0.1.0"

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_cims_client():
    """
    Instantiate and return an OCI CIMS IncidentClient with API-key (fingerprint) based authentication only.
    """
    config = oci.config.from_file(
        profile_name=os.environ.get("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("_mcp_server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    return oci.cims.IncidentClient(config)



@mcp.tool(
    description="List support incidents for the tenancy using the OCI Support API (CIMS). Returns mapped IncidentSummary models."
)
def list_incidents(
    compartment_id: str = Field(
        ...,
        description="The OCID of the tenancy."
    ),
    csi: Optional[str] = Field(
        None,
        description="The Customer Support Identifier (CSI) number associated with the support account. Optional for all request types."
    ),
    ocid: Optional[str] = Field(
        None,
        description="User OCID for Oracle Identity Cloud Service (IDCS) users who also have a federated Oracle Cloud Infrastructure account. Required for OCI users, optional for Multicloud users."
    ),
    limit: Optional[int] = Field(
        None,
        description="For list pagination. The maximum number of results per page, or items to return in a paginated List call."
    ),
    sort_by: Optional[str] = Field(
        None,
        description="The key to use to sort the returned items. Allowed values: 'dateUpdated', 'severity'."
    ),
    sort_order: Optional[str] = Field(
        None,
        description="The order to sort the results in. Allowed values: 'ASC', 'DESC'."
    ),
    lifecycle_state: Optional[str] = Field(
        None,
        description="The current state of the ticket. Allowed values: 'ACTIVE', 'CLOSED'."
    ),
    page: Optional[str] = Field(
        None,
        description="For list pagination. The value of the 'opc-next-page' response header from the previous List call."
    ),
    opc_request_id: Optional[str] = Field(
        None,
        description="Unique Oracle-assigned identifier for the request. If you need to contact Oracle about a particular request, provide this ID."
    ),
    homeregion: Optional[str] = Field(
        None,
        description="The region of the tenancy."
    ),
    problem_type: Optional[str] = Field(
        None,
        description="A filter to return only resources that match the specified problem type. Accepts values such as 'LIMIT', 'TECH', or 'ACCOUNT'."
    ),
    bearertokentype: Optional[str] = Field(
        None,
        description="Token type that determines which cloud provider the request comes from."
    ),
    bearertoken: Optional[str] = Field(
        None,
        description="Token provided by multi cloud provider, which helps to validate the email."
    ),
    idtoken: Optional[str] = Field(
        None,
        description="IdToken provided by multi cloud provider, which helps to validate the email."
    ),
    domainid: Optional[str] = Field(
        None,
        description="The OCID of identity domain. DomainID is mandatory if the user is part of Non Default Identity domain."
    ),
    allow_control_chars: Optional[bool] = Field(
        None,
        description="Set to True to allow control characters in the response object."
    ),
    retry_strategy: Optional[str] = Field(
        None,
        description="Retry strategy for this operation. Allowed values: 'default', 'none'. If not provided, uses SDK default. (Advanced/experimental.)"
    )
) -> List[IncidentSummary]:
    """
    Lists OCI support incidents using the OCI CIMS IncidentClient. Returns a list of mapped IncidentSummary models.
    All available filter, pagination, and context parameters are supported as per Oracle SDK documentation.
    """
    logger.info("Calling OCI CIMS IncidentClient.list_incidents")
    try:
        client = get_cims_client()
        results = []
        remaining = limit if limit is not None else None
        next_page_token = page

        while True:
            kwargs = {
                "compartment_id": compartment_id,
            }
            if csi is not None:
                kwargs["csi"] = csi
            if ocid is not None:
                kwargs["ocid"] = ocid
            if remaining is not None:
                kwargs["limit"] = remaining
            if sort_by is not None:
                kwargs["sort_by"] = sort_by
            if sort_order is not None:
                kwargs["sort_order"] = sort_order
            if lifecycle_state is not None:
                kwargs["lifecycle_state"] = lifecycle_state
            if next_page_token:
                kwargs["page"] = next_page_token
            if opc_request_id is not None:
                kwargs["opc_request_id"] = opc_request_id
            if homeregion is not None:
                kwargs["homeregion"] = homeregion
            if problem_type is not None:
                kwargs["problem_type"] = problem_type
            if bearertokentype is not None:
                kwargs["bearertokentype"] = bearertokentype
            if bearertoken is not None:
                kwargs["bearertoken"] = bearertoken
            if idtoken is not None:
                kwargs["idtoken"] = idtoken
            if domainid is not None:
                kwargs["domainid"] = domainid
            if allow_control_chars is not None:
                kwargs["allow_control_chars"] = allow_control_chars

            if retry_strategy is not None:
                import oci.retry
                if retry_strategy == "default":
                    kwargs["retry_strategy"] = oci.retry.DEFAULT_RETRY_STRATEGY
                elif retry_strategy == "none":
                    kwargs["retry_strategy"] = oci.retry.NoneRetryStrategy

            response = client.list_incidents(**kwargs)
            data = getattr(response, "data", []) or []
            mapped = [map_incident_summary(x) for x in data if x is not None]
            # Convert to dicts for serialization, using mode="json" to recursively dump submodels
            mapped_dicts = [m.model_dump(exclude_none=True, mode="json") for m in mapped if m is not None]
            results.extend(mapped_dicts)

            has_next_page = getattr(response, "has_next_page", False)
            next_page_token = getattr(response, "next_page", None)

            # If we respected a limit, trim the results and break if reached
            if remaining is not None and len(results) >= limit:
                results = results[:limit]
                break
            if not has_next_page or not next_page_token:
                break

            if remaining is not None:
                remaining = limit - len(results)
                if remaining <= 0:
                    break

        logger.info(f"Found {len(results)} incident summaries")
        return results
    except Exception as e:
        logger.error(f"Error in list_incidents tool: {str(e)}")
        raise e


@mcp.tool(
    description="Get the specified support incident from OCI CIMS. Returns mapped Incident Pydantic model."
)
def get_incident(
    incident_key: str = Field(
        ...,
        description="Unique identifier for the support request."
    ),
    compartment_id: str = Field(
        ...,
        description="The OCID of the tenancy."
    ),
    opc_request_id: Optional[str] = Field(
        None,
        description="Unique Oracle-assigned identifier for the request. Provide this if needing to contact Oracle about a particular request."
    ),
    csi: Optional[str] = Field(
        None,
        description="The Customer Support Identifier (CSI) number associated with the support account."
    ),
    ocid: Optional[str] = Field(
        None,
        description="User OCID for Oracle Identity Cloud Service (IDCS) users who also have a federated OCI account. Required for OCI users, optional for Multicloud."
    ),
    homeregion: Optional[str] = Field(
        None,
        description="The region of the tenancy."
    ),
    problemtype: Optional[str] = Field(
        None,
        description="A filter to return only resources that match the specified problem type. Accepts values such as 'LIMIT', 'TECH', or 'ACCOUNT'."
    ),
    bearertokentype: Optional[str] = Field(
        None,
        description="Token type that determines which cloud provider the request comes from."
    ),
    bearertoken: Optional[str] = Field(
        None,
        description="Token provided by multi cloud provider, which helps to validate the email."
    ),
    idtoken: Optional[str] = Field(
        None,
        description="IdToken provided by multi cloud provider, which helps to validate the email."
    ),
    domainid: Optional[str] = Field(
        None,
        description="The OCID of identity domain. DomainID is mandatory if the user is part of Non Default Identity domain."
    ),
    allow_control_chars: Optional[bool] = Field(
        None,
        description="Set to True to allow control characters in the response object."
    ),
    retry_strategy: Optional[str] = Field(
        None,
        description="Retry strategy for this operation. Allowed values: 'default', 'none'. If not provided, uses SDK default. (Advanced/experimental.)"
    )
) -> Incident:
    """
    Gets a support request from OCI CIMS by incident_key. Returns mapped Incident Pydantic model.
    """
    logger.info(f"Calling OCI CIMS IncidentClient.get_incident for key {incident_key}")
    try:
        client = get_cims_client()
        kwargs = {
            "incident_key": incident_key,
            "compartment_id": compartment_id,
        }
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if csi is not None:
            kwargs["csi"] = csi
        if ocid is not None:
            kwargs["ocid"] = ocid
        if homeregion is not None:
            kwargs["homeregion"] = homeregion
        if problemtype is not None:
            kwargs["problemtype"] = problemtype
        if bearertokentype is not None:
            kwargs["bearertokentype"] = bearertokentype
        if bearertoken is not None:
            kwargs["bearertoken"] = bearertoken
        if idtoken is not None:
            kwargs["idtoken"] = idtoken
        if domainid is not None:
            kwargs["domainid"] = domainid
        if allow_control_chars is not None:
            kwargs["allow_control_chars"] = allow_control_chars

        if retry_strategy is not None:
            import oci.retry
            if retry_strategy == "default":
                kwargs["retry_strategy"] = oci.retry.DEFAULT_RETRY_STRATEGY
            elif retry_strategy == "none":
                kwargs["retry_strategy"] = oci.retry.NoneRetryStrategy

        response = client.get_incident(**kwargs)
        incident_data = getattr(response, "data", None)
        mapped = map_incident(incident_data)
        if mapped is None:
            return Incident()
        return mapped
    except Exception as e:
        logger.error(f"Error in get_incident tool: {str(e)}")
        raise e


@mcp.tool(
    description="Create a support incident (OCI CIMS) with given incident details. Returns mapped Incident Pydantic model."
)
def create_incident(
    create_incident_details: CreateIncident = Field(
        ...,
        description="Incident information to create request. Pydantic model matching oci.cims.models.CreateIncident."
    ),
    opc_request_id: Optional[str] = Field(
        None,
        description="Unique Oracle-assigned identifier for the request."
    ),
    ocid: Optional[str] = Field(
        None,
        description="User OCID for Oracle Identity Cloud Service (IDCS) users who also have a federated Oracle Cloud Infrastructure account. Mandatory for OCI users, optional for Multicloud users."
    ),
    homeregion: Optional[str] = Field(
        None,
        description="The region of the tenancy."
    ),
    bearertokentype: Optional[str] = Field(
        None,
        description="Token type that determines which cloud provider the request comes from."
    ),
    bearertoken: Optional[str] = Field(
        None,
        description="Token provided by multi cloud provider, which helps to validate the email."
    ),
    idtoken: Optional[str] = Field(
        None,
        description="IdToken provided by multi cloud provider, which helps to validate the email."
    ),
    domainid: Optional[str] = Field(
        None,
        description="The OCID of identity domain. Mandatory if the user is part of Non Default Identity domain."
    ),
    allow_control_chars: Optional[bool] = Field(
        None,
        description="Set to True to allow control characters in the response object."
    ),
    retry_strategy: Optional[str] = Field(
        None,
        description="Retry strategy for this operation. Allowed values: 'default', 'none'. If not provided, uses SDK default. (Advanced/experimental.)"
    )
) -> Incident:
    """
    Create a support incident in OCI CIMS. Receives a CreateIncident Pydantic model, converts to OCI SDK model, and maps the Incident SDK response to API Pydantic.
    """
    logger.info("Calling OCI CIMS IncidentClient.create_incident")
    try:
        client = get_cims_client()
        # Use recursive converter for SDK CreateIncident object
        from oracle.oci_support_mcp_server.models import to_oci_create_incident
        sdk_create_incident = to_oci_create_incident(create_incident_details)
        kwargs = {"create_incident_details": sdk_create_incident}
        if opc_request_id is not None:
            kwargs["opc_request_id"] = opc_request_id
        if ocid is not None:
            kwargs["ocid"] = ocid
        if homeregion is not None:
            kwargs["homeregion"] = homeregion
        if bearertokentype is not None:
            kwargs["bearertokentype"] = bearertokentype
        if bearertoken is not None:
            kwargs["bearertoken"] = bearertoken
        if idtoken is not None:
            kwargs["idtoken"] = idtoken
        if domainid is not None:
            kwargs["domainid"] = domainid
        if allow_control_chars is not None:
            kwargs["allow_control_chars"] = allow_control_chars

        if retry_strategy is not None:
            import oci.retry
            if retry_strategy == "default":
                kwargs["retry_strategy"] = oci.retry.DEFAULT_RETRY_STRATEGY
            elif retry_strategy == "none":
                kwargs["retry_strategy"] = oci.retry.NoneRetryStrategy

        response = client.create_incident(**kwargs)
        incident_data = getattr(response, "data", None)
        mapped = map_incident(incident_data)
        if mapped is None:
            return Incident()
        return mapped
    except Exception as e:
        logger.error(f"Error in create_incident tool: {str(e)}")
        raise e

def main():
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")
    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
