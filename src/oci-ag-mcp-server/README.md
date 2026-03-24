# Oracle Access Governance MCP Server

## Overview

The Oracle Access Governance MCP Server exposes Access Governance (AG) capabilities as MCP tools, enabling secure interaction from MCP-compatible clients (e.g., Claude, custom clients etc.).

It integrates with OCI IAM (Identity Domains) using OAuth 2.0 (OIDC) to authenticate MCP clients. All tool executions require a valid token issued by OCI IAM.

### Flow
1. User authenticates via OCI IAM (OIDC)
2. MCP server receives an access/ID token
3. Token is validated
4. Authenticated requests are allowed to invoke MCP tools
5. Server uses client credentials flow to call OCI AG APIs

---

## Setup

### 1. Clone the repository

```
git clone https://github.com/anuj-git1412/oci-ag-mcp-server.git
cd oci-ag-mcp-server
```

### 2. Configure OAuth (OCI IAM)

Setting up authentication requires registering a confidential client in OCI IAM domain.
The application must include the following redirect URI:

```
http://localhost:8000/mcp/auth/callback
```

Register a second client app for access to AG APIs.

---

### 3. Create environment configuration

```
cp .env.example .env
```

Update `.env` with your values:

```
# ---------- MCP Authentication (OIDC) ----------
OCI_CONFIG_URL=
OCI_MCP_CLIENT_ID=
OCI_MCP_CLIENT_SECRET=

# ---------- Access Governance API (Client Credentials) ----------
OCI_AG_CLIENT_ID=
OCI_AG_CLIENT_SECRET=
OCI_TOKEN_URL=
AG_BASE_URL=
AG_SCOPE=
```

## Running the Server

```
uvx oracle.oci-ag-mcp-server
```

---

## Available Tools

| Tool Name                    | Description                                                                  |
|------------------------------|------------------------------------------------------------------------------|
| `list_identities`            | Retrieve all identities (users) from the AG environment.                     |
| `list_identity_collections`  | Retrieve all identity collections (groups of users) from the AG environment. |
| `create_identity_collection` | Creates a new identity collection in the AG environment.                     |
| `list_access_bundles`        | Retrieve all access bundles from the AG environment.                         |
| `list_orchestrated_systems`  | Retrieve all orchestrated systems from the AG environment.                   |
| `list_access_requests`       | Retrieve all access requests from the AG environment.                        |
| `create_access_request`      | Creates a new access request in the AG environment.                          |
| `health_check`               | Returns basic health status.                                                 |
---

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License v1.0:
https://oss.oracle.com/licenses/upl/

