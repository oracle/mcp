import sys
from src.common.server import mcp
from src.common.config import *
import src.tools

class OracleDBToolsMCPServer:
    def __init__(self):
        print("Starting the OracleDBToolsMCPServer", file=sys.stderr)

    def run(self):
        mcp.run(transport=MCP_TRANSPORT)

if __name__ == "__main__":
    server = OracleDBToolsMCPServer()
    server.run()