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
    csi: str = Field(
        ...,
        description="The Oracle Cloud Identifier (CSI) associated with the support account used to interact with Oracle Support.",
        min_length=1,
    ),
    compartment_id: str = Field(
        ...,
        description="The OCID of the tenancy. Use the tenancy OCID here.",
        min_length=1,
    ),
    ocid: str = Field(
        ...,
        description="User OCID for Oracle Identity Cloud Service (IDCS) users who also have a federated Oracle Cloud Infrastructure account. Required for OCI users.",
        min_length=1,
    ),
    limit: Optional[int] = Field(
        None,
        description="The maximum number of items to return in a paginated call.",
        ge=1
    ),
    page: Optional[str] = Field(
        None,
        description="The pagination token for retrieving the next batch of results."
    ),
    problem_type: Optional[str] = Field(
        None,
        description="A filter to return only resources that match the specified problem type. Accepts values such as 'LIMIT', 'TECH', or 'ACCOUNT'."
    ),
    sort_by: Optional[str] = Field(
        None,
        description="The field by which to sort results. Values: 'dateUpdated', 'severity', 'resourceType', 'status'."
    ),
    sort_order: Optional[str] = Field(
        None,
        description="The sort order to use. Either 'ASC' (ascending) or 'DESC' (descending)."
    ),
    severity: Optional[str] = Field(
        None,
        description="A filter to return only incidents matching the specified severity."
    ),
    status: Optional[str] = Field(
        None,
        description="A filter to return only incidents matching the specified status."
    ),
    list_incident_resource_type: Optional[str] = Field(
        None,
        description="A filter to return only incidents related to the specified resource type."
    ),
    opc_request_id: Optional[str] = Field(
        None,
        description="The OPC request ID for tracing from the client. Optional."
    )
) -> List[IncidentSummary]:
    """
    Lists the incidents for a tenancy from the OCI CIMS (Support) API, mapped to IncidentSummary Pydantic models.
    """
    logger.info("Calling OCI CIMS IncidentClient.list_incidents")
    try:
        client = get_cims_client()
        has_next_page = True
        next_page = page
        incidents: List[IncidentSummary] = []
        total_limit = limit if limit and limit > 0 else None
        call_limit = min(limit, 1000) if limit else 1000  # CIMS API may cap at 1000

        while has_next_page and (total_limit is None or len(incidents) < total_limit):
            kwargs = {
                "csi": csi,
                "compartment_id": compartment_id,
                "ocid": ocid,
                "limit": call_limit,
                "page": next_page
            }
            if problem_type:
                kwargs["problem_type"] = problem_type
            if sort_by:
                kwargs["sort_by"] = sort_by
            if sort_order:
                kwargs["sort_order"] = sort_order
            if severity:
                kwargs["severity"] = severity
            if status:
                kwargs["status"] = status
            if list_incident_resource_type:
                kwargs["list_incident_resource_type"] = list_incident_resource_type
            if opc_request_id:
                kwargs["opc_request_id"] = opc_request_id

            response = client.list_incidents(**kwargs)
            results = getattr(response, "data", [])
            # 'items' property if present (SDK style), else treat as a simple list
            items = getattr(results, "items", results)
            # DEBUG: Write first raw item ticket to a file for inspection
            # import json
            # if items and len(items) > 0:
            #     raw_ticket = None
            #     first_item = items[0]
            #     if isinstance(first_item, dict):
            #         raw_ticket = first_item.get("ticket")
            #     elif hasattr(first_item, "ticket"):
            #         raw_ticket = getattr(first_item, "ticket")
            #     try:
            #         with open("/tmp/mcp_incident_ticket_debug.json", "w") as f:
            #             json.dump(raw_ticket, f, default=str, indent=2)
            #     except Exception as debug_exc:
            #         logger.error(f"Failed to write ticket debug info: {debug_exc}")
            mapped = [map_incident_summary(i) for i in items]
            # Sanity/sanitize the ticket field for every mapped incident
            for inc in mapped:
                if hasattr(inc, "ticket") and not (inc.ticket is None or isinstance(inc.ticket, str)):
                    t = inc.ticket
                    if isinstance(t, dict):
                        inc.ticket = t.get("key") or t.get("summary") or str(t)
                    else:
                        inc.ticket = str(t)
            incidents.extend(mapped)
            has_next_page = getattr(response, "has_next_page", False)
            next_page = getattr(response, "next_page", None)
            # Stop if we've hit user-supplied max
            if total_limit is not None and len(incidents) >= total_limit:
                incidents = incidents[:total_limit]
                break

        logger.info(f"Returning {len(incidents)} IncidentSummary records")
        # Output as plain dicts, forcibly ensuring ticket is a string for serialization
        output = []
        for inc in incidents:
            val = inc.model_dump() if hasattr(inc, "model_dump") else dict(inc)
            ticket_val = val.get("ticket")
            if ticket_val is not None and not isinstance(ticket_val, str):
                if isinstance(ticket_val, dict):
                    val["ticket"] = ticket_val.get("key") or ticket_val.get("summary") or str(ticket_val)
                else:
                    val["ticket"] = str(ticket_val)
            output.append(val)
        return output

    except Exception as e:
        logger.error(f"Error in list_incidents tool: {str(e)}")
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
