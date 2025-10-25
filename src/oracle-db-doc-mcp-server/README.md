# Oracle Database Documentation MCP Server

A Python-based MCP (Model Context Protocol) server that provides tools for searching the official Oracle Database documentation.

The MCP server leverages an inverted index to serve snippets of the Oracle Database documentation. Because the Oracle Database documentation is large and gets updated from time to time, it is unfeasible to ship a ready to go documentation index with this repository. Doing so will bloat the repository and runs risk of users searching on an outdated documentation.

Instead, users can create their own index and maintain it as often as required. See [Index creation/maintenance](#index-creation-maintenance) for more on that topic.

## Features

- **Search**
  - Serach the documentation by keywords and phrases

## Prerequisites

- Python 3.x
- Downloaded [Oracle Database Documentation zip file](https://docs.oracle.com/en/database/oracle/oracle-database/26/zip/oracle-database_26.zip) to build the initial index

## Installation

```console
git clone https://github.com/oracle/mcp.git

cd mcp/src/oracle-db-doc-mcp-server

python3 -m venv .venv

source .venv/bin/activate

python3 -m pip install -r requirements.txt
```

## Usage

```console
usage: oracle-db-doc-mcp-server.py [-h] [-log-level LOG_LEVEL] {idx,mcp} ...

Oracle Database Documentation MCP Server.

options:
  -h, --help            show this help message and exit
  -log-level LOG_LEVEL  Set the log level (DEBUG, INFO, WARNING, ERROR (default), CRITICAL).

subcommands:
  {idx,mcp}
    idx                 create/maintain the index
    mcp                 run the MCP server
```

The MCP server has two subcommands:

1. `idx`: Creates or maintains the documentation index.
2. `mcp`: Runs the MCP server.

Building the index will take some time and some MCP clients will time out while waiting for the index to be built. Hence the two subcommands cannot be intermixed. Users will first have to create the documentation index via the `idx` subcommand and once completed, run the server with the `mcp` subcommand.

### Index creation/maintenance

```console
usage: oracle-db-doc-mcp-server.py idx [-h] -path PATH [-preprocess PREPROCESS]

options:
  -h, --help            show this help message and exit
  -path PATH            path to the documentation input zip file or extracted directory
  -preprocess PREPROCESS
                        preprocessing level of documentation (NONE, BASIC (default), ADVANCED)
```

To create or maintain the index, use the `idx` subcommand and point the `-path` parameter to either the Oracle Database Documentation zip file (the file will be automatically unzipped into a temorary location under `$HOME/.oracle/oracle-db-doc-mcp-server`) or an **already extracted** location of the Oracle Database Documentation.

The server will create a new folder under `$HOME/.oracle/oracle-db-doc-mcp-server` and store the index and the server log file within. Subsequent runs of `mcp` will open that index. The index can be updated by running the `idx` mode again.

The index creation will take several minutes to complete depending on your environment and the level of preprocessing specified via the `-preprocess` parameter.

A checksum of the index is kept so that subsequent executions of the program will only reindex content that has changed.

For example, to create an index on a downloaded Oracle Database documentation zip file under `~/Downloads/oracle-database_26.zip`, run:

```console
python3 oracle-db-doc-mcp-server.py idx -path ~/Downloads/oracle-database_26.zip
```

### Running the MCP Server

```console
usage: oracle-db-doc-mcp-server.py mcp [-h] [-mode {stdio,http}] [-host HOST] [-port PORT]

options:
  -h, --help          show this help message and exit
  -mode {stdio,http}  the transport mode for the MCP server (stdio (default) or http)
  -host HOST          the IP address (default 0.0.0.0) that the MCP server is reachable at
  -port PORT          the port (default 8000) that the MCP server is reachable at
```

To run the MCP server, use the `mcp` subcommand.

**Note:** The index will have to exist. If it doesn't, the MCP server will exit with an error.

By default, the MCP server runs on `stdio`. Hence, the simplest way to run it, is:

```console
python3 oracle-db-doc-mcp-server.py mcp
```

### VSCode integration

#### Running the MCP server via Docker/Podman

To run the MCP server from inside a Docker container:

1. Add a new file `.vscode/mcp.json` file to your project folder.
2. Add the following content to your `mcp.json` file.

```
{
  "servers": {
    "oracle-db-doc": {
      "type": "stdio",
      "command": "docker",
      "args": [ "run", "--rm", "-i", "ghcr.io/oracle/mcp/oracle-db-doc" ]
    }
  }
}
```

#### Running the MCP server directly

To run the MCP server directly from your machine:

1. Follow the [Installation](#installation) instructions first.
2. Create an index as explained in [Index creation/maintenance](#index-creation-maintenance)
3. Add a new file `mcp.json` file to your project folder.
4. Add the following content to your `.vscode/mcp.json` file. Replace the `<>` placeholders with the paths to the MCP server installation.

```
{
  "servers": {
    "oracle-db-doc": {
      "type": "stdio",
      "command": "<installation>/.venv/bin/python3",
      "args": [ "oracle-db-doc-mcp-server.py", "mcp" ]
    }
  }
}
```

## Tools

### search_oracle_database_documentation

Searches the documentation for key words and key phrases.

```python
search_oracle_database_documentation(search_query: str, max_results: int) -> list[str]:
```
