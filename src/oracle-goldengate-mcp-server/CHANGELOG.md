# Changelog

## Unreleased

### Breaking Changes

- Require Python 3.11 or later to install and run the server.

### Changed

- Use standalone FastMCP 4.2.2 for the stdio server. Tool discovery now includes FastMCP-generated display metadata.

### Security

- Require dnspython 2.9.2 or later when installing the server.
- Keep GoldenGate HTTP error response bodies out of tool execution logs.
