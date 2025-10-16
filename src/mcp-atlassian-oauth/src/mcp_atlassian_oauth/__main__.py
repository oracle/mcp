import os
import asyncio

# Optional: load .env if present (HTTP mode typically uses server-side .env)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

from .server import get_app  # FastMCP app (stdio runner)
# HTTP adapter that keeps the existing POST /mcp contract for Cline
def _run_http() -> None:
    from .http import create_app  # lazy import to avoid FastAPI dep unless needed
    import uvicorn  # type: ignore

    host = os.environ.get("MCP_HOST", "0.0.0.0")
    try:
        port = int(os.environ.get("MCP_PORT", "8765"))
    except Exception:
        port = 8765
    path = os.environ.get("MCP_PATH", "/mcp")
    log_level = os.environ.get("LOG_LEVEL", "info")

    app = create_app(path=path)
    uvicorn.run(app, host=host, port=port, log_level=log_level)


def _run_stdio() -> None:
    """
    Local stdio transport (for editor/agent spawn) using fastmcp.
    Run fastmcp synchronously to avoid nesting event loops under anyio.
    """
    mcp = get_app()
    try:
        mcp.run()
    except KeyboardInterrupt:
        pass


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    if transport == "http":
        _run_http()
        return
    _run_stdio()


if __name__ == "__main__":
    main()
