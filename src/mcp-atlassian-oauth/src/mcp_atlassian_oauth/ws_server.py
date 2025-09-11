import asyncio
from typing import Awaitable, Callable

# Lightweight WebSocket server adapter for MCP using the "websockets" library.
# This exposes the same read/write callables shape that mcp.server.Server.run expects,
# enabling URL-based (ws/wss) connections from MCP clients like Cline Remote MCP.
#
# Notes:
# - This module is optional; import guarded by runtime. If "websockets" is not installed,
#   attempting to start ws mode will raise a clear error instructing to install the ops extra.
# - For production, place a TLS-terminating reverse proxy (e.g., NGINX/Caddy/IIS) in front and
#   expose wss:// to clients while the Python process binds to localhost over ws://.


async def serve_ws(server, host: str = "0.0.0.0", port: int = 8765) -> None:
    """
    Start a WebSocket server and run the MCP server for each incoming connection.

    :param server: mcp.server.Server instance
    :param host: interface to bind (default: 0.0.0.0)
    :param port: TCP port to listen on (default: 8765)
    """
    try:
        import websockets
    except Exception as e:
        raise RuntimeError(
            "WebSocket mode requires the 'websockets' package. "
            "Install the optional extra: pip install '.[ops]'"
        ) from e

    # Subprotocol is not strictly required by all clients, but some may negotiate it.
    # If your client requires a specific value, add it here (e.g., subprotocols=['mcp']).
    async def handler(websocket: "websockets.WebSocketServerProtocol") -> None:
        async def read() -> str:
            # Server.run expects a JSON-RPC message string
            msg = await websocket.recv()
            if isinstance(msg, bytes):
                return msg.decode("utf-8", errors="replace")
            return msg

        async def write(data: str) -> None:
            await websocket.send(data)

        try:
            await server.run(read, write, initialization_options=server.create_initialization_options())
        except websockets.ConnectionClosed:  # type: ignore
            # Client disconnected; nothing else to do
            return
        except Exception:
            # Swallow per-connection errors to keep the listener alive
            return

    async with websockets.serve(handler, host, port):
        # Run forever until cancelled/stopped by supervisor
        await asyncio.Future()
