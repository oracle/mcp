import os
import asyncio

# Optional: load .env if present (only when python-dotenv is installed)
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

from .server import main as stdio_main, server as server_instance  # stdio mode
from .resources.registry import register_schemes  # for resource URI support (jira://, confluence://)


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()

    if transport == "ws":
        # WebSocket listener mode (remote URL endpoint)
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        try:
            port = int(os.environ.get("MCP_PORT", "8765"))
        except Exception:
            port = 8765

        # Enable resource URI providers for this server instance
        try:
            register_schemes(server_instance)
        except Exception:
            # Do not fail server if resources cannot be registered
            pass

        # Import on-demand to avoid hard dependency when ws mode is not used
        from .ws_server import serve_ws

        asyncio.run(serve_ws(server_instance, host=host, port=port))
        return

    # Default: stdio mode (local)
    stdio_main()


if __name__ == "__main__":
    main()
