from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import Response
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.types import Receive, Scope, Send
from starlette.routing import Mount, Route
from src.common.config import *
# Initialize FastMCP server

mcp = FastMCP(
    "OracleDBToolsMCPServer",
    dependencies=["oci", "dotenv", "numpy"],
    host=MCP_SSE_HOST,  # Sets the HTTP URL host (e.g., for all interfaces; use "localhost" for local-only)
    port=MCP_SSE_PORT  # Sets the port (default is often 8000; choose an available port like 8080 if needed)
)

mcp._session_manager = StreamableHTTPSessionManager(
        app=mcp._mcp_server,
        event_store=None,
        json_response=True,
        stateless=True,
    )

def handle_health(request):
        return JSONResponse({"status": "success"})

async def handle_streamable_http(
    scope: Scope, receive: Receive, send: Send
) -> None:
    await mcp._session_manager.handle_request(scope, receive, send)

mcp._custom_starlette_routes=[
            Mount("/mcp", app=handle_streamable_http),
            Route('/health', endpoint=handle_health),
        ]
