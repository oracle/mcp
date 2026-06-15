#!/usr/bin/env -S node --no-node-snapshot --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { createOciReflectionManifest, createOciSdkHostRpc } from "./oci-host.ts";
import { runJavaScript } from "./sandbox.ts";
import type { JsonObject } from "./types.ts";

const MAX_CONCURRENT_TOOL_CALLS = positiveIntegerEnv(
  "OCI_JAVASCRIPT_MAX_CONCURRENT_TOOL_CALLS",
  4
);
const MAX_QUEUED_TOOL_CALLS = positiveIntegerEnv("OCI_JAVASCRIPT_MAX_QUEUED_TOOL_CALLS", 64);
const hostRpc = createOciSdkHostRpc();
let reflectionManifest: ReturnType<typeof createOciReflectionManifest> | undefined;
const DEFAULT_TIMEOUT_SECONDS = 30;
const MIN_TIMEOUT_SECONDS = 1;
const MAX_TIMEOUT_SECONDS = 120;
let activeToolCalls = 0;
const queuedToolCalls: Array<() => void> = [];

const server = new McpServer({
  name: "oci-javascript-mcp-server",
  version: "0.1.0"
}, {
  instructions: (
    "Run one complete JavaScript script against the injected OCI binding. "
    + "Leave the result value as the final expression; "
    + "stdout/stderr are for logs. "
    + "Try normal JavaScript first, use list limit/page tokens for pagination, and call "
    + "discover_oci only after an SDK shape error or genuine uncertainty."
  )
});

server.registerTool(
  "run_javascript",
  {
    description: (
      "Primary tool for Oracle Cloud Infrastructure (OCI) tasks. "
      + "Run one complete JavaScript script in a fresh sandbox with an injected "
      + "`oci` binding. Leave the result value as the final expression; "
      + "stdout/stderr are for incidental logs. Try straightforward code first; "
      + "use OCI list limit/page tokens for pagination, and use `discover_oci` only after "
      + "SDK shape errors or genuine uncertainty. "
      + "The sandbox has no OCI credentials, filesystem, network, or environment access."
    ),
    inputSchema: {
      code: z.string().describe(
        "JavaScript to execute. Use the injected `oci` binding and leave the result value as the final expression."
      ),
      stdin: z.string().optional().describe(
        "Optional data exposed to sandbox code as `globalThis.stdin`."
      ),
      timeout: z.number().min(MIN_TIMEOUT_SECONDS).max(MAX_TIMEOUT_SECONDS).default(
        DEFAULT_TIMEOUT_SECONDS
      ).describe("Maximum wall-clock seconds allowed for execution.")
    },
    annotations: {
      openWorldHint: true,
      readOnlyHint: false
    }
  },
  async args => {
    return jsonToolResult(await limitToolCall(async () => {
      reflectionManifest ??= createOciReflectionManifest();
      const result = await runJavaScript(args.code, {
        stdin: args.stdin ?? null,
        timeoutSeconds: args.timeout,
        hostRpc,
        reflectionManifest
      });
      return {
        result: result.result,
        stdout: result.stdout,
        stderr: result.stderr,
        exit_code: result.exitCode,
        timed_out: result.timedOut
      };
    }));
  }
);

server.registerTool(
  "discover_oci",
  {
    description: (
      "Fallback OCI JavaScript SDK introspection. Do not call this by default. "
      + "Use it after a JavaScript attempt fails or when the service, client, "
      + "operation, or request/model shape is genuinely unclear."
    ),
    inputSchema: {
      service: z.string().optional().describe(
        "OCI SDK service export name, e.g. core, identity, resourcesearch."
      ),
      client: z.string().optional().describe(
        "Client class name, e.g. ComputeClient or IdentityClient."
      ),
      operation: z.string().optional().describe("Operation name, e.g. listInstances.")
    },
    annotations: {
      openWorldHint: false,
      readOnlyHint: true
    }
  },
  async args => {
    return jsonToolResult(await limitToolCall(async () => {
      const result = await hostRpc({
        binding: "oracle",
        namespace: "oci",
        operation: "discover",
        payload: args as JsonObject
      });
      return result && typeof result === "object" && !Array.isArray(result)
        ? result as JsonObject
        : { value: result };
    }));
  }
);

await server.connect(new StdioServerTransport());

function jsonToolResult(result: JsonObject): CallToolResult {
  return {
    content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    structuredContent: result
  };
}

async function limitToolCall<T>(callback: () => Promise<T>): Promise<T> {
  await acquireToolCall();
  try {
    return await callback();
  } finally {
    activeToolCalls -= 1;
    queuedToolCalls.shift()?.();
  }
}

function acquireToolCall(): Promise<void> {
  if (activeToolCalls < MAX_CONCURRENT_TOOL_CALLS) {
    activeToolCalls += 1;
    return Promise.resolve();
  }
  if (queuedToolCalls.length >= MAX_QUEUED_TOOL_CALLS) {
    throw new Error(`too many queued tool calls (${MAX_QUEUED_TOOL_CALLS})`);
  }
  return new Promise(resolve => {
    queuedToolCalls.push(() => {
      activeToolCalls += 1;
      resolve();
    });
  });
}

function positiveIntegerEnv(name: string, fallback: number): number {
  const raw = process.env[name];
  if (raw === undefined) {
    return fallback;
  }
  const value = Number.parseInt(raw, 10);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}
