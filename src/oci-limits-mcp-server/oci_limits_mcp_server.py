"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.

OCI Service Limits and Quota Policies MCP Server
- Provides read-only access to OCI service limits and quota policies
- Supports querying limits by service, region, and compartment
- Allows checking current usage against quota limits
- Returns structured JSON for easy consumption by LLMs
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import oci
from fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("oci-limits")

# Configuration
profile_name = os.getenv("PROFILE_NAME", "DEFAULT")

try:
    config = oci.config.from_file(profile_name=profile_name)
    identity_client = oci.identity.IdentityClient(config)
    limits_client = oci.limits.LimitsClient(config)
    usage_api_client = oci.usage_api.UsageapiClient(config)
    monitoring_client = oci.monitoring.MonitoringClient(config)
    resource_search_client = oci.resource_search.ResourceSearchClient(config)
    tenancy_id = os.getenv("TENANCY_ID_OVERRIDE", config['tenancy'])
except Exception as e:
    print(f"Warning: Failed to initialize OCI clients: {e}")
    config = None
    identity_client = None
    limits_client = None
    usage_api_client = None
    monitoring_client = None
    resource_search_client = None
    tenancy_id = None


def get_compartment_by_name(compartment_name: str):
    """Internal function to get compartment by name"""
    if not identity_client:
        return None
        
    try:
        compartments = identity_client.list_compartments(
            compartment_id=tenancy_id,
            compartment_id_in_subtree=True,
            access_level="ACCESSIBLE",
            lifecycle_state="ACTIVE"
        )
        # Add root compartment (tenancy)
        compartments.data.append(identity_client.get_compartment(compartment_id=tenancy_id).data)

        # Search for the compartment by name
        for compartment in compartments.data:
            if compartment.name.lower() == compartment_name.lower():
                return compartment
        return None
    except Exception as e:
        print(f"Error getting compartment: {e}")
        return None


def format_error_response(error_message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Format error responses consistently"""
    response = {"error": error_message}
    if context:
        response.update(context)
    return json.dumps(response, indent=2)


@mcp.tool()
def list_all_compartments() -> str:
    """List all compartments in the tenancy"""
    if not identity_client:
        return format_error_response("OCI client not initialized")
        
    try:
        compartments = identity_client.list_compartments(
            compartment_id=tenancy_id,
            compartment_id_in_subtree=True,
            access_level="ACCESSIBLE",
            lifecycle_state="ACTIVE"
        ).data
        
        # Add root compartment (tenancy)
        root_compartment = identity_client.get_compartment(compartment_id=tenancy_id).data
        compartments.append(root_compartment)
        
        # Format for better readability
        result = []
        for compartment in compartments:
            result.append({
                "id": compartment.id,
                "name": compartment.name,
                "description": compartment.description,
                "lifecycle_state": compartment.lifecycle_state,
                "time_created": str(compartment.time_created)
            })
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error_response(f"Failed to list compartments: {str(e)}")


@mcp.tool()
def list_service_limits(service_name: str, compartment_name: Optional[str] = None, 
                       availability_domain: Optional[str] = None, limit_name: Optional[str] = None) -> str:
    """
    List service limits for a specific service in OCI
    
    Args:
        service_name: Name of the OCI service (e.g., "compute", "block-storage", "database")
        compartment_name: Optional compartment name to scope the limits
        availability_domain: Optional availability domain filter
        limit_name: Optional specific limit name to filter by
    """
    if not limits_client:
        return format_error_response("OCI limits client not initialized")
    
    try:
        compartment_id = tenancy_id
        if compartment_name:
            compartment = get_compartment_by_name(compartment_name)
            if not compartment:
                return format_error_response(f"Compartment '{compartment_name}' not found")
            compartment_id = compartment.id
        
        # List limits for the service
        kwargs = {
            "service_name": service_name,
            "compartment_id": compartment_id
        }
        
        if availability_domain:
            kwargs["availability_domain"] = availability_domain
        if limit_name:
            kwargs["name"] = limit_name
            
        limits_response = limits_client.list_limit_values(**kwargs)
        
        result = []
        for limit in limits_response.data:
            limit_info = {
                "service_name": service_name,
                "name": limit.name,
                "description": getattr(limit, 'description', None),
                "value": limit.value,
                "scope_type": limit.scope_type,
                "availability_domain": limit.availability_domain,
                "compartment_id": compartment_id,
                "compartment_name": compartment_name or "root"
            }
            result.append(limit_info)
        
        return json.dumps({
            "service": service_name,
            "total_limits": len(result),
            "limits": result
        }, indent=2)
        
    except Exception as e:
        return format_error_response(f"Failed to list service limits: {str(e)}", {
            "service_name": service_name,
            "compartment_name": compartment_name
        })


@mcp.tool()
def get_service_limit(service_name: str, limit_name: str, compartment_name: Optional[str] = None, 
                     availability_domain: Optional[str] = None) -> str:
    """
    Get details for a specific service limit
    
    Args:
        service_name: Name of the OCI service
        limit_name: Specific limit name
        compartment_name: Optional compartment name to scope the limit
        availability_domain: Optional availability domain filter
    """
    if not limits_client:
        return format_error_response("OCI limits client not initialized")
    
    try:
        compartment_id = tenancy_id
        if compartment_name:
            compartment = get_compartment_by_name(compartment_name)
            if not compartment:
                return format_error_response(f"Compartment '{compartment_name}' not found")
            compartment_id = compartment.id
        
        # Get the specific limit
        kwargs = {
            "service_name": service_name,
            "limit_name": limit_name,
            "compartment_id": compartment_id
        }
        
        if availability_domain:
            kwargs["availability_domain"] = availability_domain
            
        limit_response = limits_client.get_limit_value(**kwargs)
        
        result = {
            "service_name": service_name,
            "name": limit_response.data.name,
            "description": getattr(limit_response.data, 'description', None),
            "value": limit_response.data.value,
            "scope_type": limit_response.data.scope_type,
            "availability_domain": limit_response.data.availability_domain,
            "compartment_id": compartment_id,
            "compartment_name": compartment_name or "root"
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return format_error_response(f"Failed to get service limit: {str(e)}", {
            "service_name": service_name,
            "limit_name": limit_name,
            "compartment_name": compartment_name
        })


@mcp.tool()
def list_supported_services() -> str:
    """List all supported services that have limits in OCI"""
    if not limits_client:
        return format_error_response("OCI limits client not initialized")
    
    try:
        services_response = limits_client.list_services(compartment_id=tenancy_id)
        
        result = []
        for service in services_response.data:
            service_info = {
                "name": service.name,
                "description": service.description,
            }
            result.append(service_info)
        
        return json.dumps({
            "total_services": len(result),
            "services": result
        }, indent=2)
        
    except Exception as e:
        return format_error_response(f"Failed to list supported services: {str(e)}")


@mcp.tool()
def list_quota_policies(compartment_name: Optional[str] = None) -> str:
    """
    List quota policies in a compartment
    
    Args:
        compartment_name: Optional compartment name. If not provided, uses root compartment.
    """
    if not limits_client:
        return format_error_response("OCI limits client not initialized")
    
    try:
        compartment_id = tenancy_id
        if compartment_name:
            compartment = get_compartment_by_name(compartment_name)
            if not compartment:
                return format_error_response(f"Compartment '{compartment_name}' not found")
            compartment_id = compartment.id
        
        quotas_response = limits_client.list_quotas(compartment_id=compartment_id)
        
        result = []
        for quota in quotas_response.data:
            quota_info = {
                "id": quota.id,
                "name": quota.name,
                "description": quota.description,
                "compartment_id": quota.compartment_id,
                "lifecycle_state": quota.lifecycle_state,
                "time_created": str(quota.time_created),
                "freeform_tags": quota.freeform_tags,
                "defined_tags": quota.defined_tags
            }
            result.append(quota_info)
        
        return json.dumps({
            "compartment_name": compartment_name or "root",
            "total_quotas": len(result),
            "quotas": result
        }, indent=2)
        
    except Exception as e:
        return format_error_response(f"Failed to list quota policies: {str(e)}", {
            "compartment_name": compartment_name
        })


@mcp.tool()
def get_quota_policy(quota_name: str, compartment_name: Optional[str] = None) -> str:
    """
    Get detailed information about a specific quota policy
    
    Args:
        quota_name: Name of the quota policy
        compartment_name: Optional compartment name. If not provided, uses root compartment.
    """
    if not limits_client:
        return format_error_response("OCI limits client not initialized")
    
    try:
        compartment_id = tenancy_id
        if compartment_name:
            compartment = get_compartment_by_name(compartment_name)
            if not compartment:
                return format_error_response(f"Compartment '{compartment_name}' not found")
            compartment_id = compartment.id
        
        # First, find the quota by name
        quotas_response = limits_client.list_quotas(compartment_id=compartment_id)
        quota_id = None
        for quota in quotas_response.data:
            if quota.name.lower() == quota_name.lower():
                quota_id = quota.id
                break
        
        if not quota_id:
            return format_error_response(f"Quota policy '{quota_name}' not found in compartment")
        
        # Get the detailed quota information
        quota_response = limits_client.get_quota(quota_id=quota_id)
        quota = quota_response.data
        
        # Get quota statements
        statements = quota.statements if hasattr(quota, 'statements') and quota.statements else []
        
        result = {
            "id": quota.id,
            "name": quota.name,
            "description": quota.description,
            "compartment_id": quota.compartment_id,
            "compartment_name": compartment_name or "root",
            "lifecycle_state": quota.lifecycle_state,
            "time_created": str(quota.time_created),
            "statements": statements,
            "freeform_tags": quota.freeform_tags,
            "defined_tags": quota.defined_tags
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return format_error_response(f"Failed to get quota policy: {str(e)}", {
            "quota_name": quota_name,
            "compartment_name": compartment_name
        })


@mcp.tool()
def check_service_limits_by_region(service_name: str, region: str, 
                                  compartment_name: Optional[str] = None) -> str:
    """
    Check service limits for a specific service in a particular region
    
    Args:
        service_name: Name of the OCI service
        region: OCI region name (e.g., "us-ashburn-1", "us-phoenix-1")
        compartment_name: Optional compartment name
    """
    if not limits_client:
        return format_error_response("OCI limits client not initialized")
    
    try:
        compartment_id = tenancy_id
        if compartment_name:
            compartment = get_compartment_by_name(compartment_name)
            if not compartment:
                return format_error_response(f"Compartment '{compartment_name}' not found")
            compartment_id = compartment.id
        
        # Create a new limits client for the specific region
        region_config = config.copy()
        region_config['region'] = region
        region_limits_client = oci.limits.LimitsClient(region_config)
        
        # List limits for the service in the specific region
        limits_response = region_limits_client.list_limit_values(
            service_name=service_name,
            compartment_id=compartment_id
        )
        
        result = []
        for limit in limits_response.data:
            limit_info = {
                "service_name": service_name,
                "region": region,
                "name": limit.name,
                "description": getattr(limit, 'description', None),
                "value": limit.value,
                "scope_type": limit.scope_type,
                "availability_domain": limit.availability_domain,
                "compartment_id": compartment_id,
                "compartment_name": compartment_name or "root"
            }
            result.append(limit_info)
        
        return json.dumps({
            "service": service_name,
            "region": region,
            "total_limits": len(result),
            "limits": result
        }, indent=2)
        
    except Exception as e:
        return format_error_response(f"Failed to check service limits by region: {str(e)}", {
            "service_name": service_name,
            "region": region,
            "compartment_name": compartment_name
        })


@mcp.tool()
def get_resource_availability(service_name: str, resource_type: str, 
                             compartment_name: Optional[str] = None, 
                             availability_domain: Optional[str] = None) -> str:
    """
    Get resource availability information for a service in OCI
    
    Args:
        service_name: Name of the OCI service
        resource_type: Type of resource to check availability for
        compartment_name: Optional compartment name
        availability_domain: Optional availability domain
    """
    if not limits_client:
        return format_error_response("OCI limits client not initialized")
    
    try:
        compartment_id = tenancy_id
        if compartment_name:
            compartment = get_compartment_by_name(compartment_name)
            if not compartment:
                return format_error_response(f"Compartment '{compartment_name}' not found")
            compartment_id = compartment.id
        
        # Get resource availability
        kwargs = {
            "service_name": service_name,
            "compartment_id": compartment_id
        }
        
        if availability_domain:
            kwargs["availability_domain"] = availability_domain
        
        # List all limits for the service first
        limits_response = limits_client.list_limit_values(**kwargs)
        
        # Filter by resource type if specified
        relevant_limits = []
        for limit in limits_response.data:
            if not resource_type or resource_type.lower() in limit.name.lower():
                relevant_limits.append({
                    "name": limit.name,
                    "description": getattr(limit, 'description', None),
                    "value": limit.value,
                    "scope_type": limit.scope_type,
                    "availability_domain": limit.availability_domain
                })
        
        result = {
            "service_name": service_name,
            "resource_type": resource_type,
            "compartment_name": compartment_name or "root",
            "availability_domain": availability_domain,
            "total_limits": len(relevant_limits),
            "limits": relevant_limits
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return format_error_response(f"Failed to get resource availability: {str(e)}", {
            "service_name": service_name,
            "resource_type": resource_type,
            "compartment_name": compartment_name
        })


@mcp.tool()
def list_availability_domains(compartment_name: Optional[str] = None) -> str:
    """
    List availability domains in a compartment or region
    
    Args:
        compartment_name: Optional compartment name. If not provided, uses root compartment.
    """
    if not identity_client:
        return format_error_response("OCI identity client not initialized")
    
    try:
        compartment_id = tenancy_id
        if compartment_name:
            compartment = get_compartment_by_name(compartment_name)
            if not compartment:
                return format_error_response(f"Compartment '{compartment_name}' not found")
            compartment_id = compartment.id
        
        # List availability domains
        ads_response = identity_client.list_availability_domains(compartment_id=compartment_id)
        
        result = []
        for ad in ads_response.data:
            ad_info = {
                "name": ad.name,
                "id": ad.id,
                "compartment_id": ad.compartment_id
            }
            result.append(ad_info)
        
        return json.dumps({
            "compartment_name": compartment_name or "root",
            "total_availability_domains": len(result),
            "availability_domains": result
        }, indent=2)
        
    except Exception as e:
        return format_error_response(f"Failed to list availability domains: {str(e)}", {
            "compartment_name": compartment_name
        })


@mcp.tool()
def ping() -> str:
    """Health check to verify the server is responsive"""
    if not config:
        return json.dumps({"status": "error", "message": "OCI configuration not initialized"})
    return json.dumps({"status": "ok", "message": "OCI Limits MCP Server is running"})


def main() -> None:
    """Start the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
