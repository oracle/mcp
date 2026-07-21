# Oracle MCP Common

`oracle-mcp-common` is the shared Python library for Oracle MCP servers. It
provides reusable components that belong in more than one server while keeping
server-specific tools, client lifecycles, and service behavior in each server.

The library currently provides OCI SDK authentication through
`oracle_mcp_common.auth`. Future shared modules should follow the same
server-agnostic approach and expose a focused, documented public API.

## Package requirements

- Python 3.13 or later
- OCI Python SDK 2.179.0 or later
- FastMCP 3.4.2 for the optional HTTP IDCS authentication API

An adopting server normally declares a bounded dependency on this package:

```toml
dependencies = [
  "oracle-mcp-common>=0.1.0,<0.2.0",
]
```

## Authentication module

`oracle_mcp_common.auth` resolves outbound authentication for OCI Python SDK
clients. It chooses a supported authentication type and returns the SDK-native
ingredients needed to create a service client.

The module owns credential resolution only. Each server continues to own its
OCI client type, retry and circuit-breaker policy, `additional_user_agent`, and
client lifecycle.

### Quick start

Set up OCI credentials for the authentication type you intend to use, then
build a context and pass its config and signer to the OCI SDK client.

```python
import oci

from oracle_mcp_common import build_auth_context

auth_context = build_auth_context()
config = {
    **auth_context.config,
    "additional_user_agent": "oci-example-mcp/1.2.3",
}
client = oci.object_storage.ObjectStorageClient(config, signer=auth_context.signer)
```

The returned `AuthContext` contains:

| Field | Meaning |
| --- | --- |
| `auth_type` | The selected `AuthType`; `auto` is resolved to `api_key` or `security_token`. |
| `config` | An OCI SDK config dictionary. It contains the resolved `region` when one is available. |
| `signer` | The OCI SDK signer to pass to a client constructor. |
| `tenancy_id` | Tenancy metadata when the selected signer or profile supplies it. |
| `region` | The resolved client region, if available. |
| `profile_name` | The selected profile for profile-backed authentication; otherwise `None`. |

### Select an authentication type

Set `OCI_MCP_AUTH_TYPE`, or pass `AuthOptions(auth_type=...)` to
`build_auth_context()`. The supported values are:

| Type | Credential source | Notes |
| --- | --- | --- |
| `auto` | Selected OCI config profile | Uses `security_token` only if the selected profile directly declares `security_token_file`; otherwise uses `api_key`. |
| `api_key` | Selected OCI config profile | Requires `tenancy`, `user`, `fingerprint`, and `key_file`. The library logs a one-time recommendation to use session-token authentication. |
| `security_token` | Selected OCI config profile | Requires `security_token_file` directly in the selected profile, plus the API-key fields required to construct its signer. |
| `identity_domain_upst` | Identity Domains JWT-to-UPST token exchange | Uses file-backed JWT and client-secret inputs. See [Identity Domains token exchange](#identity-domains-token-exchange). |
| `instance_principal` | OCI instance principal | Intended for OCI compute instances. |
| `resource_principal` | OCI resource principal | Intended for supported OCI managed-resource environments. |
| `instance_principal_delegation` | Instance principal and delegation token | Requires a delegation-token file. |
| `resource_principal_delegation` | Resource principal and delegation token | Requires a delegation-token file. |
| `oke_workload_identity` | OKE workload identity | Uses the OCI SDK's default service-account token unless an override is supplied. |

`auto` intentionally does not probe instance, resource, delegation, or OKE
principal environments. Select those types explicitly so a deployment's OCI
identity remains predictable.

### Configuration precedence

An explicit non-empty `AuthOptions` value wins over its canonical environment
variable. Empty strings are treated as unset.

| Setting | Precedence, highest first |
| --- | --- |
| Authentication type | `AuthOptions.auth_type` → `OCI_MCP_AUTH_TYPE` → supported legacy aliases → `auto` |
| Config file | `AuthOptions.config_file` → `OCI_CONFIG_FILE` → OCI SDK default location |
| Profile | `AuthOptions.profile_name` → `OCI_CONFIG_PROFILE` → `ORACLE_MCP_AUTH_PROFILE` → OCI SDK default profile |
| Region | `AuthOptions.region` → `OCI_REGION` → profile- or signer-derived region |
| Other type-specific inputs | Their matching `AuthOptions` field → canonical `OCI_MCP_*` variable → documented legacy alias, if one exists |

`OCI_REGION` changes the region used for the returned SDK client config. It
does not change the selected profile, tenancy, signing key, or principal
credential source.

#### Profile-backed authentication

`auto`, `api_key`, and `security_token` honor the usual OCI CLI-compatible
variables: `OCI_CONFIG_FILE` and `OCI_CONFIG_PROFILE`.

For safety, `security_token_file` must be declared in the selected profile's
own section. A value inherited from `[DEFAULT]` is not treated as a session
token for another profile. This prevents an inherited setting from silently
changing the OCI principal used by a named API-key profile.

Once a selected profile directly declares a session token, the library reports
an unreadable token or incomplete session configuration instead of falling
back to API-key authentication.

### Type-specific inputs

| Authentication type | Required inputs | Optional inputs |
| --- | --- | --- |
| `identity_domain_upst` | `OCI_MCP_IDENTITY_DOMAIN_URL`, `OCI_MCP_UPST_JWT_FILE`, `OCI_MCP_IDENTITY_DOMAIN_CLIENT_ID`, `OCI_MCP_IDENTITY_DOMAIN_CLIENT_SECRET_FILE`, and a region | Explicit `AuthOptions` equivalents |
| `*_delegation` | `OCI_MCP_DELEGATION_TOKEN_FILE` | Deprecated `OCI_MCP_DELEGATION_TOKEN` compatibility input |
| `oke_workload_identity` | None | `OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN_PATH`; deprecated inline-token compatibility input |
| Principal types | None | `OCI_MCP_TENANCY_ID_OVERRIDE` when signer metadata does not provide a tenancy ID |

All file-backed secret values are read as UTF-8 and surrounding whitespace is
trimmed. The library reports the variable name when a value is absent,
unreadable, or empty, without including secret contents in the error.

### Identity Domains token exchange

Use `identity_domain_upst` when a file-backed Identity Domains service-bearer
JWT must be exchanged for an OCI User Principal Security Token (UPST).

```bash
export OCI_MCP_AUTH_TYPE=identity_domain_upst
export OCI_MCP_IDENTITY_DOMAIN_URL=https://example.identity.oraclecloud.com
export OCI_MCP_UPST_JWT_FILE=/var/run/secrets/identity/jwt
export OCI_MCP_IDENTITY_DOMAIN_CLIENT_ID=example-client-id
export OCI_MCP_IDENTITY_DOMAIN_CLIENT_SECRET_FILE=/var/run/secrets/identity/client-secret
export OCI_REGION=us-chicago-1
```

The URL must be an absolute `https://` URL with a host. The Identity Domain
must have an Identity Propagation Trust that accepts the JWT and an OAuth client
authorized for token exchange.

The JWT file is read again when the OCI SDK refreshes the UPST, so a rotated JWT
at the same path can be observed by an existing signer. The client secret is
read when the signer is created; rotating that secret requires a controlled
process restart that recreates the signer and every cached OCI client. A
replacement process should complete an initial token exchange before it accepts
traffic.

This outbound token-exchange type is independent of inbound HTTP MCP OAuth.
It does not read request access tokens or FastMCP transport configuration.

### HTTP IDCS authentication

Use the HTTP IDCS API when an HTTP MCP server must authenticate each caller
through OCI IAM and make OCI SDK calls as that caller. This is intentionally a
different path from `build_auth_context()`: stdio continues to use the flexible
OCI profile, principal, and service-bearer authentication modes above.

At startup, build the HTTP policy with the scopes required by the server and
assign its provider to FastMCP. During an authenticated request, pass the
request token explicitly to create an OCI SDK context.

```python
import oci
from fastmcp.server.dependencies import get_access_token

from oracle_mcp_common import build_idcs_http_auth

http_auth = build_idcs_http_auth(
    ["openid", "profile", "email", "oci_mcp.example.invoke"]
)
mcp.auth = http_auth.provider

# Call only while handling an authenticated HTTP request.
request_token = get_access_token()
request_auth = http_auth.context_for(request_token.token)
config = {
    **request_auth.config,
    "additional_user_agent": "oci-example-mcp/1.2.3",
}
client = oci.object_storage.ObjectStorageClient(config, signer=request_auth.signer)
```

`build_idcs_http_auth()` validates the provider configuration before it creates
FastMCP's `OCIProvider`. It does not inspect `ORACLE_MCP_HOST` or
`ORACLE_MCP_PORT`, start the listener, assign `mcp.auth`, read FastMCP request
context, create a service client, or set `additional_user_agent`; the adopting
server owns each of those steps.

| Setting | Purpose |
| --- | --- |
| `IDCS_DOMAIN` | Identity Domains host, such as `example.identity.oraclecloud.com`, or an absolute `https://` origin. |
| `IDCS_CLIENT_ID` / `IDCS_CLIENT_SECRET` | OAuth client used for the provider and request-token exchange. Keep the secret in the deployment secret store. |
| `IDCS_AUDIENCE` | Audience configured for the MCP OAuth client. |
| `ORACLE_MCP_BASE_URL` | Absolute public HTTP or HTTPS server URL; include a mount path when applicable. Register `${ORACLE_MCP_BASE_URL}/auth/callback` with the OCI IAM confidential application. |
| `OCI_REGION` | Region used for the returned OCI SDK context, unless `context_for(..., region=...)` supplies one explicitly. |

The HTTP access token is required for `context_for()` and is never read from a
global FastMCP context by the library. Treat each returned signer and any OCI
client built with it as caller-specific: do not cache it globally or reuse it
for another request. Provider configuration and token-exchange errors identify
missing settings but never include access-token or client-secret values.

### Delegation and OKE token inputs

For delegation types, use a mounted file:

```bash
export OCI_MCP_AUTH_TYPE=instance_principal_delegation
export OCI_MCP_DELEGATION_TOKEN_FILE=/var/run/secrets/oci/delegation-token
```

Do not set both the file and inline token inputs. Inline delegation tokens are
compatibility-only because environment variables are more easily exposed in
process inspection and diagnostics.

For OKE workload identity, the default OCI SDK token discovery needs no
configuration. To use a non-default mounted token, set
`OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN_PATH`. Do not set both the path and the
deprecated inline token input.

### Compatibility aliases

Canonical `OCI_MCP_*` inputs take precedence. The following aliases are
accepted only during the migration window and emit a one-time deprecation
warning when used:

| Canonical input | Supported legacy aliases |
| --- | --- |
| `OCI_MCP_AUTH_TYPE` | `OCI_IOT_AUTH_TYPE`, `OCI_AUTH_TYPE`, `ORACLE_MCP_AUTH_METHOD` |
| `OCI_CONFIG_PROFILE` | `ORACLE_MCP_AUTH_PROFILE` |
| `OCI_MCP_DELEGATION_TOKEN_FILE` | `OCI_IOT_DELEGATION_TOKEN` (inline token) |
| `OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN_PATH` | `OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN_PATH` |
| Deprecated OKE inline token | `OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN` |
| `OCI_MCP_TENANCY_ID_OVERRIDE` | `OCI_IOT_TENANCY_ID_OVERRIDE`, `TENANCY_ID_OVERRIDE` |

The compatibility window begins with version 0.1.0 and ends no earlier than the
later of 180 days or two published adopter-server release waves. Removals are
planned no earlier than version 0.2.0.

### Public API

```python
from oracle_mcp_common import (
    AuthContext,
    AuthOptions,
    AuthType,
    build_auth_context,
    profile_declares_security_token,
)
```

Use `profile_declares_security_token(config_file, profile_name)` when a caller
needs the same inheritance-safe classification without constructing an OCI SDK
signer. For example, an OCI CLI wrapper can use it to decide whether an
explicit `--auth` flag is appropriate.

## Development

From the repository root, run the package test suite with:

```bash
make test project=common
```

Run the repository Python lint check after source changes:

```bash
make lint
```
