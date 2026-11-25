#!/usr/bin/env -S node --no-node-snapshot --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { createIsolationProvider } from "./isolation/provider-factory.ts";
import { createOciReflectionManifest, createOciSdkHostRpc } from "./oci-host.ts";
import { positiveIntegerEnv } from "./sandbox-common.ts";
import { runJavaScript } from "./sandbox.ts";
import {
  discoverOci,
  DISCOVER_OCI_TOOL,
  executionToolResult,
  jsonToolResult,
  RUN_JAVASCRIPT_TOOL,
  SERVER_INSTRUCTIONS
} from "./tool-contracts.ts";
import type {
  HostRpcHandler,
  IsolationProvider,
  OciReflectionManifest
} from "./types.ts";

export async function startServer(options: {
  isolationProvider?: IsolationProvider;
  hostRpc?: HostRpcHandler;
  reflectionManifest?: OciReflectionManifest;
} = {}): Promise<void> {

const MAX_CONCURRENT_TOOL_CALLS = positiveIntegerEnv(
  "OCI_JAVASCRIPT_MAX_CONCURRENT_TOOL_CALLS",
  4
);
const isolationProvider = options.isolationProvider ?? await createIsolationProvider();
const hostRpc = options.hostRpc ?? createOciSdkHostRpc();
let reflectionManifest = options.reflectionManifest;
let activeToolCalls = 0;

const server = new McpServer({
  name: "oci-javascript-mcp-server",
  version: "0.1.1"
}, {
  instructions: SERVER_INSTRUCTIONS
});

server.registerTool(
  "run_javascript",
  RUN_JAVASCRIPT_TOOL,
  async (args, extra) => {
    return executionToolResult(await limitToolCall(async () => {
      reflectionManifest ??= createOciReflectionManifest();
      const result = await runJavaScript(args.code, {
        timeoutSeconds: args.timeout,
        signal: extra.signal,
        hostRpc,
        reflectionManifest,
        isolationProvider
      });
      return result;
    }));
  }
);

server.registerTool(
  "discover_oci",
  DISCOVER_OCI_TOOL,
  async args => {
    return jsonToolResult(await limitToolCall(() => discoverOci(args, hostRpc)));
  }
);

await server.connect(new StdioServerTransport());

async function limitToolCall<T>(callback: () => Promise<T>): Promise<T> {
  if (activeToolCalls >= MAX_CONCURRENT_TOOL_CALLS) {
    throw new Error(`too many concurrent tool calls (${MAX_CONCURRENT_TOOL_CALLS})`);
  }
  activeToolCalls += 1;
  try {
    return await callback();
  } finally {
    activeToolCalls -= 1;
  }
}

}

if (
  process.argv[1]
  && realpathSync(fileURLToPath(import.meta.url)) === realpathSync(process.argv[1])
) {
  await startServer();
}
