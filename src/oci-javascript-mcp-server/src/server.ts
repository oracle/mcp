#!/usr/bin/env -S node --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { pathToFileURL } from "node:url";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { runJavaScript } from "./execution.ts";
import { OciSdkRuntime } from "./oci.ts";
import { admitProvider } from "./isolation/admission.ts";
import { AppleContainerIsolationProvider } from "./isolation/apple-container.ts";
import { ProcessIsolationProvider } from "./isolation/process.ts";
import type { IsolationProvider, JsonObject } from "./types.ts";

const VERSION = "0.1.0";

export type ServerDependencies = {
  provider: IsolationProvider;
  runtime: OciSdkRuntime;
  mode: "development" | "production";
};

export function createMcpServer(dependencies: ServerDependencies): McpServer {
  admitProvider(dependencies.provider, dependencies.mode);
  const server = new McpServer({
    name: "oci-javascript-mcp-server",
    version: VERSION
  }, {
    instructions: (
      "Run complete JavaScript programs using the injected OCI SDK-compatible `oci` facade. "
      + "Leave the desired value as the final expression. OCI credentials and clients stay in "
      + "the trusted host broker. Use discover_oci only when the SDK shape is unclear."
    )
  });

  server.registerTool("run_javascript", {
    description: (
      "Run one complete JavaScript program in a fresh execution environment. The program receives "
      + "an injected `oci` facade, and its final expression becomes result. stdout and stderr are captured."
    ),
    inputSchema: {
      code: z.string().describe("JavaScript source. Leave the desired value as the final expression."),
      timeout: z.number().min(1).max(120).default(30)
        .describe("Maximum wall-clock execution duration in seconds (1-120).")
    },
    annotations: { openWorldHint: true, readOnlyHint: false }
  }, async (args, extra) => {
    try {
      const result = await runJavaScript(args.code, {
        timeoutSeconds: args.timeout,
        provider: dependencies.provider,
        runtime: dependencies.runtime,
        mode: dependencies.mode,
        signal: extra.signal
      });
      return jsonToolResult({
        result: result.result,
        error: result.error,
        stdout: result.stdout,
        stderr: result.stderr,
        exit_code: result.exitCode,
        timed_out: result.timedOut
      });
    } catch (error) {
      return jsonToolResult({
        result: null,
        error: { message: publicExecutionError(error) },
        stdout: "",
        stderr: "",
        exit_code: 1,
        timed_out: false
      });
    }
  });

  server.registerTool("discover_oci", {
    description: (
      "Inspect installed OCI SDK services, clients, API operations, request fields, and response "
      + "information without running untrusted JavaScript."
    ),
    inputSchema: {
      service: z.string().optional().describe("OCI SDK service export, such as core or identity."),
      client: z.string().optional().describe("OCI SDK client class, such as ComputeClient."),
      operation: z.string().optional().describe("OCI SDK operation, such as listInstances.")
    },
    annotations: { openWorldHint: false, readOnlyHint: true }
  }, async args => {
    try {
      return jsonToolResult(dependencies.runtime.discover(args));
    } catch (error) {
      return jsonToolResult({ error: { message: publicDiscoveryError(error) } });
    }
  });

  return server;
}

export function dependenciesFromEnvironment(): ServerDependencies {
  const mode = process.env.OCI_JAVASCRIPT_MODE === "development" ? "development" : "production";
  const providerName = process.env.OCI_JAVASCRIPT_ISOLATION_PROVIDER ?? "process";
  let provider: IsolationProvider;
  if (providerName === "process") {
    provider = new ProcessIsolationProvider({
      allowInsecure: process.env.OCI_JAVASCRIPT_ALLOW_INSECURE_PROCESS === "1"
    });
  } else if (providerName === "apple-container") {
    provider = new AppleContainerIsolationProvider({
      cliPath: process.env.OCI_JAVASCRIPT_APPLE_CONTAINER_CLI,
      image: process.env.OCI_JAVASCRIPT_APPLE_CONTAINER_IMAGE,
      network: process.env.OCI_JAVASCRIPT_APPLE_CONTAINER_NETWORK
    });
  } else {
    throw new Error(`isolation provider '${providerName}' is not implemented`);
  }
  admitProvider(provider, mode);
  return { provider, runtime: new OciSdkRuntime(), mode };
}

export async function main(): Promise<void> {
  const server = createMcpServer(dependenciesFromEnvironment());
  await server.connect(new StdioServerTransport());
}

function jsonToolResult(result: JsonObject): CallToolResult {
  return {
    content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    structuredContent: result
  };
}

function publicExecutionError(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  return /code exceeds|timeout must|not admitted|requires OCI_JAVASCRIPT/i.test(message)
    ? message
    : "JavaScript execution could not be started";
}

function publicDiscoveryError(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  return /Unknown OCI SDK|Invalid OCI|Unsupported discovery/i.test(message)
    ? message
    : "OCI discovery failed";
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
