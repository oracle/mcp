import urllib
from dotenv import load_dotenv
import os
from dotenv import load_dotenv
from pathlib import Path

# ────────────────────────────────────────────────────────
# 1) bootstrap paths + env + llm
# ────────────────────────────────────────────────────────
THIS_DIR = Path(__file__).resolve()
PROJECT_ROOT = THIS_DIR.parent.parent.parent
print(PROJECT_ROOT)
load_dotenv(PROJECT_ROOT / "config/.env")  # expects OCI_ vars in .env

MCP_TRANSPORT = os.getenv('MCP_TRANSPORT', 'stdio')
MCP_SSE_HOST = os.getenv('MCP_SSE_HOST', '0.0.0.0')
MCP_SSE_PORT = os.getenv('MCP_SSE_PORT', '8000')

print(MCP_TRANSPORT)
print(MCP_SSE_HOST)
print(MCP_SSE_PORT)