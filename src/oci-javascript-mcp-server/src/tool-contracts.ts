/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { createRequire } from "node:module";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import {
  DEFAULT_TIMEOUT_SECONDS,
  MAX_TIMEOUT_SECONDS,
  MIN_TIMEOUT_SECONDS
} from "./sandbox-common.ts";
import type { HostRpcHandler, JsonObject, OciDiscoverPayload, SandboxResult } from "./types.ts";

const { version: ociSdkVersion } = createRequire(import.meta.url)("oci-sdk/package.json") as { version: string };

export const SERVER_INSTRUCTIONS = (
  "Execute directly with run_javascript when the OCI SDK shape is known; otherwise use "
  + "discover_oci only to the necessary service/client/operation depth, then execute. "
  + "Write a complete JavaScript body using top-level await and an explicit return for the result. "
  + "Await every OCI call; use camelCase request objects and oci.config() for configured tenancy context. "
  + "Variables and clients are fresh on each execution. Use bounded sequential list pages, preserve "
  + "request context with continuation tokens, and return focused results. stdout/stderr are logs. "
  + "Execution failures retain a structured envelope and set isError; rejected inputs/admission "
  + "and discovery failures are tool errors without an execution envelope. Scripts are not transactions: "
  + "inspect resource state before retrying mutations and never automatically replay a failed script."
);

export const RUN_JAVASCRIPT_TOOL = {
  title: "Run OCI JavaScript",
  description: (
    "Run a complete JavaScript body against the injected OCI SDK-shaped oci namespace in a fresh sandbox. "
    + `The facade exposes supported API operations from OCI SDK for TypeScript/JavaScript version ${ociSdkVersion}, `
    + "subject to the adapter restrictions described below. "
    + "Supports constructed clients and static facade calls; region is the only client option. "
    + "Host IAM permissions govern OCI calls, which may read, create, update, or delete resources. "
    + "No imports, Node built-ins, OCI credentials, direct filesystem/network access, process state, "
    + "or host environment access. Await every OCI call and return a focused result; stdout/stderr are logs. "
    + "Use discover_oci when the SDK shape is unclear. Each full OCI response is bounded before guest "
    + "projection: reduce page size or narrow the request if it is too large. Finite configured call and "
    + "concurrency budgets apply; oci.config() consumes a bridge call. Failures set isError and retain "
    + "the execution envelope. A mutation may complete before a later failure: inspect resource state "
    + "before retrying, never automatically replay the whole script. Preserve opcRetryToken for the same "
    + "logical request only where that operation supports it."
  ),
  inputSchema: {
    code: z.string().describe(
      "Complete JavaScript program body with top-level await and return, using the injected oci namespace. "
      + "Source is limited to 1 MiB of UTF-8. Await every OCI call. Prefer an explicit return; "
      + "final-expression inference is also supported. Use camelCase request fields. The configured "
      + "identity must expose tenancy context and have permission for this example:\n\n```js\n"
      + "const config = await oci.config();\n"
      + "const client = new oci.identity.IdentityClient();\n"
      + "const response = await client.listRegionSubscriptions({ tenancyId: config.tenancyId });\n"
      + "return response.items.map(item => item.regionName);\n```\n"
      + 'For a specific region: new oci.identity.IdentityClient({ region: "us-ashburn-1" }). '
      + "Each execution has fresh variables and clients; supply continuation tokens explicitly."
    ),
    timeout: z.number().min(MIN_TIMEOUT_SECONDS).max(MAX_TIMEOUT_SECONDS)
      .default(DEFAULT_TIMEOUT_SECONDS).describe(
        "Execution deadline in seconds (1–120, default 30), covering startup, JavaScript, and OCI calls. "
        + "Existing bounded cleanup phases can extend the response time after that deadline."
      )
  },
  outputSchema: z.object({
    result: z.json().describe("Returned JSON value, including null, arrays, primitives, and tagged wire objects."),
    error: z.object({ message: z.string().min(1) }).catchall(z.json()).nullable()
      .describe("Null on success, otherwise a sanitized error with optional OCI details."),
    stdout: z.string().describe("Captured standard-output logs."),
    stderr: z.string().describe("Captured standard-error logs."),
    exit_code: z.int().describe("Zero on success; nonzero on execution failure."),
    timed_out: z.boolean().describe("Whether execution exceeded its deadline.")
  }),
  annotations: {
    readOnlyHint: false,
    destructiveHint: true,
    idempotentHint: false,
    openWorldHint: true
  }
};

const identifier = z.string().regex(/^[A-Za-z][A-Za-z0-9_]*$/);
const discoveryInputSchema = z.object({
  service: identifier.optional().describe(
    "Case-sensitive OCI SDK service export, e.g. identity, core, resourcesearch. "
    + "Omit all identifiers for the service index. Must match ^[A-Za-z][A-Za-z0-9_]*$; no whitespace."
  ),
  client: identifier.optional().describe(
    "Case-sensitive client class, e.g. IdentityClient or ComputeClient. Requires service; "
    + "omit client and operation to list that service's clients. Must match ^[A-Za-z][A-Za-z0-9_]*$."
  ),
  operation: identifier.optional().describe(
    "Case-sensitive operation, e.g. listCompartments or listInstances. Requires service and client; "
    + "omit to list the client's operations. Must match ^[A-Za-z][A-Za-z0-9_]*$."
  )
});

const discoveryField = z.object({
  name: z.string(),
  required: z.boolean(),
  type: z.string(),
  modelRefs: z.array(z.string()).optional()
}).catchall(z.json());

const discoveryOutputSchema = z.object({
  type: z.enum(["index", "service", "client", "operation"]).describe("Discovery depth."),
  service: z.string().optional().describe("Service export at service, client, or operation depth."),
  client: z.string().optional().describe("Client class at client or operation depth."),
  operation: z.string().optional().describe("Operation name at operation depth."),
  services: z.array(z.string()).optional().describe("Service exports, required for index results."),
  clients: z.array(z.string()).optional().describe("Client classes, required for service results."),
  operations: z.array(z.string()).optional().describe("Operations, required for client results."),
  requestShape: z.string().optional().describe("Request-object guidance, required for operation results."),
  requestType: z.string().optional().describe("Extracted SDK request interface name, when available."),
  requestFields: z.array(discoveryField).optional().describe("Best-effort extracted request fields."),
  models: z.record(z.string(), z.object({ fields: z.array(discoveryField) }).catchall(z.json()))
    .optional().describe("Models expanded to the existing bounded depth; references can remain unresolved."),
  exampleRequest: z.record(z.string(), z.json()).optional()
    .describe("Placeholder request skeleton, not a complete validated API request."),
  responseShape: z.object({
    bodyKey: z.string().optional(),
    bodyModel: z.string().optional(),
    requestIdField: z.string().optional(),
    pagination: z.object({ nextPageField: z.string(), requestPageField: z.string() })
      .catchall(z.json()).optional()
  }).catchall(z.json()).optional().describe("Extracted body, request ID, and continuation-field hints.")
}).catchall(z.json());

const discoveryVariants = {
  index: discoveryOutputSchema.extend({ type: z.literal("index"), services: z.array(z.string()) }),
  service: discoveryOutputSchema.extend({ type: z.literal("service"), service: z.string(), clients: z.array(z.string()) }),
  client: discoveryOutputSchema.extend({
    type: z.literal("client"), service: z.string(), client: z.string(), operations: z.array(z.string())
  }),
  operation: discoveryOutputSchema.extend({
    type: z.literal("operation"), service: z.string(), client: z.string(), operation: z.string(), requestShape: z.string()
  })
};
const discoveryResultSchema = z.discriminatedUnion("type", [
  discoveryVariants.index, discoveryVariants.service, discoveryVariants.client, discoveryVariants.operation
]);

export const DISCOVER_OCI_TOOL = {
  title: "Discover OCI SDK",
  description: (
    `Inspects the installed OCI SDK for TypeScript/JavaScript version ${ociSdkVersion}; use these discovery `
    + "results when remembered or external SDK definitions differ. "
    + "Inspect declarations progressively: no arguments lists services; service lists "
    + "clients; service and client list operations; all three describe request/model and response shapes. "
    + "Use only the necessary depth when the SDK shape is unclear, then run_javascript. Runs on the host "
    + "without starting an isolation provider or making OCI network calls. Does not grant IAM permission "
    + "or guarantee regional availability. Parsing is best-effort: model expansion is bounded, inline "
    + "types may be incomplete, references unresolved, and enum/conditional constraints missing. "
    + "exampleRequest is a placeholder skeleton, not a validated API request; absent detail does not "
    + "prove an API requirement is absent. Identifiers are case-sensitive; supply each child's parents."
  ),
  inputSchema: discoveryInputSchema,
  outputSchema: discoveryOutputSchema,
  annotations: { readOnlyHint: true, openWorldHint: false }
};

export async function discoverOci(args: OciDiscoverPayload, hostRpc: HostRpcHandler): Promise<JsonObject> {
  const input = discoveryInputSchema.safeParse(args);
  if (!input.success) {
    throw new Error(`Invalid discovery input: ${input.error.message}`);
  }
  const missing: string[] = [];
  if ((args.client !== undefined || args.operation !== undefined) && args.service === undefined) {
    missing.push("service");
  }
  if (args.operation !== undefined && args.client === undefined) {
    missing.push("client");
  }
  if (missing.length) {
    throw new Error(`Invalid discovery input: missing ${missing.join(" and ")} parent identifier(s)`);
  }
  const result = await hostRpc({
    binding: "oracle", namespace: "oci", operation: "discover", payload: input.data
  });
  const validated = discoveryResultSchema.safeParse(result);
  if (!validated.success) {
    throw new Error(`Invalid discovery result: ${validated.error.message}`);
  }
  // Validation must not strip or transform host extraction data.
  return result as JsonObject;
}

export function jsonToolResult(result: JsonObject): CallToolResult {
  return {
    content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    structuredContent: result
  };
}

export function executionToolResult(result: SandboxResult): CallToolResult {
  return {
    ...jsonToolResult({
      result: result.result,
      error: result.error?.message === ""
        ? { ...result.error, message: "Execution failed without an error message" }
        : result.error,
      stdout: result.stdout,
      stderr: result.stderr,
      exit_code: result.exitCode,
      timed_out: result.timedOut
    }),
    ...(result.error !== null || result.timedOut || result.exitCode !== 0 ? { isError: true } : {})
  };
}
