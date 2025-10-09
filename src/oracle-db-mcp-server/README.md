# Oracle Database Documentation MCP Server

A Python-based MCP (Model Context Protocol) server that provides tools for searching the official Oracle Database documentation.

## Features

- **Search**
  - Serach the documentation by keywords and phrases

## Prerequisites

- Python 3.x
- Downloaded [Oracle Database Documentation zip file](https://docs.oracle.com/en/database/oracle/oracle-database/23/zip/oracle-database_23.zip)

## Installation

```console
git clone https://github.com/oracle/mcp.git

cd mcp/src/oracle-db-mcp-server

python3 -m venv .venv

source .venv/bin/activate

python3 -m pip install -r requirements.txt
```

## Usage

The MCP server has two modes:

1. `-doc`: Create or maintain the documentation index
2. `-mcp`: Run the MCP server.

Building the index will take some time and some MCP clients will time out while waiting for the index to be built. Hence the two modes cannot be intermixed.

The server will create a new folder under `$HOME/.oracle/oracle-db-mcp-server` to store the index and the server log file.

```console
usage: oracle-db-doc-mcp-server.py [-h] [-doc DOC] [-mcp] [-log-level LOG_LEVEL]

Oracle Database Documentation MCP Server.

options:
  -h, --help            show this help message and exit
  -doc DOC              Path to the documentation input zip file or extracted directory.
  -mcp                  Run the MCP server.
  -log-level LOG_LEVEL  Set the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
```

### Index creation/maintenance

To create or maintain the index, point the `-doc` parameter to either the Oracle Database Documentation zip file or an **already extracted** location of the Oracle Documentation.
The index creation will take several minutes to complete.
A checksum of the index is kept so that subsequent executions of the program will only reindex content that has changed.

```console
python3 oracle-db-doc-mcp-server.py -doc ~/Downloads/oracle-database_23.zip
```

### Run MCP Server

To run just the MCP server, provide the `-mcp` parameter. The index will have to exist.

```console
python3 oracle-db-doc-mcp-server.py -mcp
```

### VSCode integration

Replace the `<>` placeholders with the paths to the MCP server installation and Oracle Database Documentation zip file.

```
{
  "servers": {
    "oracle-db-doc": {
      "type": "stdio",
      "command": "<installation>/.venv/bin/python3",
      "args": [ "oracle-db-doc-mcp-server.py", "-mcp" ]
    }
  }
}
```

## Tools

### search

Searches the documentation for key words and key phrases

```python
search(search_query: str, max_results: int) -> list[str]:
```
