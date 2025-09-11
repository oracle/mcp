"""
Jira domain package for MCP Atlassian OAuth server.

Modules:
- models.py: light dataclasses for typed issue/project representations (optional).
- api.py: thin wrappers around REST endpoints using authed_fetch.
- search.py: heuristic (and optional semantic) similarity search utilities.
- tools.py: MCP tool call handlers for Jira (delegated from server.py).
- resources.py: jira:// resource URI list/read handlers.
"""
