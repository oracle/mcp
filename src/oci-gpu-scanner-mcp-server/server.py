#!/usr/bin/env python3
"""
Lens API MCP Server

This server provides comprehensive Model Context Protocol (MCP) tools for interacting with
the lens API for instance and health check management.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import List, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
    ServerCapabilities,
    ToolsCapability
)

# Import our modular components
from log_setup import setup_logging
from config import init_lens_client, is_initialized
from tools.tool_definition import get_tool_definitions
from tools.tool_handler import (
    handle_get_latest_health_check,
    handle_create_health_check,
    handle_get_instance_log,
    handle_get_monitoring_ring_health_status
)

# Initialize logging
logger = setup_logging()

# Create server instance
server = Server("lens-mcp")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available lens API tools."""
    return get_tool_definitions()

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
    """Handle tool calls for lens API operations."""
    # Enhanced logging for debugging HTTP requests
    logger.info("="*60)
    logger.info(f"🎯 Claude is calling tool: {name}")
    logger.info(f"📝 Arguments received: {json.dumps(arguments, indent=2)}")
    logger.info(f"🕐 Request timestamp: {datetime.now().isoformat()}")
    
    # Log environment variables that might contain HTTP context (set by mcpo)
    http_context_vars = [
        'HTTP_X_API_KEY', 'HTTP_AUTHORIZATION', 'HTTP_USER_AGENT', 
        'HTTP_HOST', 'HTTP_CONTENT_TYPE', 'REQUEST_METHOD', 'HTTP_ORIGIN',
        'REMOTE_ADDR', 'HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP'
    ]
    
    http_context = {}
    for var in http_context_vars:
        value = os.environ.get(var)
        if value:
            http_context[var] = value
    
    if http_context:
        logger.info(f"🌐 HTTP Context from mcpo: {json.dumps(http_context, indent=2)}")
    else:
        logger.debug("📭 No HTTP context variables found in environment")
    
    # Log current working directory and process info
    logger.debug(f"📂 Working directory: {os.getcwd()}")
    logger.debug(f"🔧 Process ID: {os.getpid()}")
    
    if not is_initialized():
        logger.warning("⚠️  Lens client not initialized, attempting to initialize...")
        init_lens_client()
        if not is_initialized():
            error_msg = "Error: Lens client not initialized. Please check your configuration."
            logger.error(f"❌ {error_msg}")
            return [TextContent(type="text", text=error_msg)]

    try:
        logger.info(f"🔄 Processing tool call: {name}")
        
        if name == "lens_get_latest_health_check_state":
            return await handle_get_latest_health_check(arguments)
        elif name == "lens_create_health_check":
            return await handle_create_health_check(arguments)
        elif name == "lens_get_instance_logs":
            return await handle_get_instance_log(arguments)
        elif name == "lens_get_monitoring_ring_health_status":
            return await handle_get_monitoring_ring_health_status(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error in {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]


async def main():
    """Main entry point for the MCP server."""
    # Initialize lens client on startup
    init_lens_client()
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="lens-mcp",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    tools=ToolsCapability(listChanged=False)
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
