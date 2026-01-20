#!/usr/bin/env python3
"""
Lens API Tools Definitions Module

Contains all MCP tool definitions and their input schemas for lens API operations.
"""

from typing import List
from mcp.types import Tool


def get_tool_definitions() -> List[Tool]:
    """Get all available lens API tool definitions."""
    return [
        Tool(
            name="lens_get_latest_health_check_state",
            description="Get the state of the latest active health check for a specific instance in the lens system",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": "The ID of the instance"
                    }
                },
                "required": ["instance_id"]
            }
        ),
        Tool(
            name="lens_create_health_check",
            description="Create a new active health check for a specific instance in the lens system",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": "The ID of the instance"
                    },
                    "type": {
                        "type": "string",
                        "description": "Type of health check to perform",
                        "enum": ["single_node", "multi_node", "advanced"],
                        "default": "single_node"
                    }
                },
                "required": ["instance_id"]
            }
        ),
        Tool(
            name="lens_get_instance_logs",
            description="Retrieve and decode base64 encoded logs from active health checks for a specific instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": "The ID of the instance to retrieve logs from"
                    }
                },
                "required": ["instance_id"]
            }
        ),
        Tool(
            name="lens_get_monitoring_ring_health_status",
            description="Get comprehensive health status for all instances in a monitoring ring, including active health checks, passive health checks, and failure recommendations. Identifies failed instances and provides detailed analysis with suggestions for remediation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "monitoring_ring_id": {
                        "type": "string",
                        "description": "The UUID of the monitoring ring to analyze"
                    }
                },
                "required": ["monitoring_ring_id"]
            }
        )
    ]
