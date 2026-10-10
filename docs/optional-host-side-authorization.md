# Optional host-side authorization

This note describes an optional pattern for MCP **hosts** (clients, routers, or
agent runtimes) that invoke Oracle MCP tools. It does not change any server in
this repository.

## What this is (and is not)

Oracle Cloud Infrastructure (OCI) IAM, OCI authentication, and the authorization
controls documented for these servers remain the source of truth for what a
caller may do in Oracle Cloud. Hosts must still configure least-privilege OCI
credentials and follow the [Authentication](../README.md#authentication)
guidance in the repository README.

Optional host-side authorization is an **extra** gate that a host can run
**before** it sends a sensitive tool call to an Oracle MCP server. It answers a
narrow question: given this agent, this tool, and this local policy, is the host
willing to proceed right now?

It does **not**:

- replace OCI IAM, Identity Domains / IDCS, or Oracle authorization policies
- replace OCI authentication (stdio profiles, HTTP IDCS token exchange, or
  shared `oracle-mcp-common` credential resolution)
- soften or bypass the mutating-command denylist used by
  [`oci-api-mcp-server`](../src/oci-api-mcp-server/README.md)
- require any new dependency in Oracle MCP server packages

## Why hosts care

Several servers in this repository expose consequential write or mutate tools
(for example networking create/delete paths, registry mutations, and the OCI
CLI-backed API server). The API server already treats mutating commands as a
distinct class via its denylist. A host can apply a similar distinction locally:
detect a sensitive tool intent, obtain an allow or deny decision, then execute
or stop.

## Suggested host flow

1. The agent requests an Oracle MCP tool.
2. The host classifies the call as sensitive (for example, mutating OCI work,
   or a tool your local policy marks as privileged).
3. The host requests a signed allow or deny decision from its chosen gate.
4. The host **verifies** that decision locally.
5. On deny, the host does not invoke the MCP tool.
6. On allow, the host invokes the Oracle MCP tool as usual. OCI IAM still
   enforces what the configured principal can do in the tenancy.

Fail closed: if verification fails or the gate is unavailable, do not execute
the sensitive tool.

## Example: AffixIO as an optional gate

[AffixIO](https://www.affix-io.com) is one optional implementation of this host
pattern. It provides signed allow/deny decisions for agent tool gates (ACTION /
Know Your Agent). The host verifies the decision before tool execution. AffixIO
is not an Oracle product, not a required dependency of this repository, and not
a substitute for OCI IAM.

For SDK install and `mcpToolGate` usage, see the AffixIO SDK README:

- Product: https://www.affix-io.com
- SDK source: https://github.com/AffixIO/SDK
- npm package: https://www.npmjs.com/package/affixio

Illustrative host-side sketch (Node.js). Adapt names and policy to your runtime.
Do not put AffixIO keys or OCI credentials in model prompts.

```javascript
import { AffixSDK, mcpToolGate, spendingPolicy } from "affixio";

const sdk = new AffixSDK({ apiKey: process.env.AFFIX_API_KEY });

// Local host policy only. OCI IAM still decides what the principal can do.
const policy = spendingPolicy()
  .currency("USD")
  .maxPerAction(1)
  .allowCategories(["oci"]);

export async function beforeSensitiveOracleTool(tool, meta = {}) {
  const gate = await mcpToolGate({
    sdk,
    policy,
    tool,
    agentId: meta.agentId || "agent://oracle-mcp/host",
    amount: 0,
    currency: "USD",
    category: "oci",
    meta: {
      argsDigest: String(meta.argsDigest || ""),
    },
  });

  if (!gate.allowed) {
    throw new Error(gate.reason || "host gate denied tool call");
  }

  return gate;
}

// Host pseudocode:
// const decision = await beforeSensitiveOracleTool("delete_vcn", { argsDigest });
// await oracleMcp.callTool("delete_vcn", args); // only after allow
```

Skip this example entirely if you do not want an extra host gate. Oracle MCP
servers continue to work with the authentication and IAM setup documented in
this repository alone.

## Related material in this repository

- [Authentication](../README.md#authentication) in the root README
- Shared OCI auth module: [`src/common/README.md`](../src/common/README.md)
- Mutating-command denylist for the CLI-backed API server:
  [`scripts/README.md`](../scripts/README.md) and
  `src/oci-api-mcp-server/oracle/oci_api_mcp_server/denylist`
- Security vulnerability reporting: [`SECURITY.md`](../SECURITY.md)
