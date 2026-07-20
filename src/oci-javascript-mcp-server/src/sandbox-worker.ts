#!/usr/bin/env -S node --no-node-snapshot --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { formatError } from "./sandbox-common.ts";
import { runJavaScriptInIsolate } from "./sandbox-isolate.ts";
import type { Json, OciReflectionManifest } from "./types.ts";

type PendingRpc = {
  resolve: (value: Json) => void;
  reject: (error: Error) => void;
};

const pendingRpc = new Map<number, PendingRpc>();
let nextRpcId = 1;
let running = false;

process.on("message", message => {
  void handleMessage(message);
});
process.on("disconnect", () => {
  rejectPending(new Error("sandbox parent disconnected"));
  process.exit(1);
});

async function handleMessage(message: unknown): Promise<void> {
  if (!message || typeof message !== "object") {
    return;
  }

  const record = message as Record<string, unknown>;
  if (record.type === "rpcResult" && typeof record.id === "number") {
    const pending = pendingRpc.get(record.id);
    if (pending) {
      pendingRpc.delete(record.id);
      pending.resolve(record.result as Json);
    }
    return;
  }

  if (record.type !== "run" || running) {
    return;
  }

  running = true;
  try {
    if (typeof record.code !== "string") {
      throw new Error("sandbox worker received invalid code");
    }
    if (!isPositiveInteger(record.memoryLimitMb) || !isPositiveInteger(record.maxResultBytes)) {
      throw new Error("sandbox worker received invalid limits");
    }
    const result = await runJavaScriptInIsolate(record.code, {
      timeoutSeconds: typeof record.timeoutSeconds === "number"
        ? record.timeoutSeconds
        : undefined,
      hostRpc,
      reflectionManifest: record.reflectionManifest as OciReflectionManifest | undefined,
      memoryLimitMb: record.memoryLimitMb,
      maxResultBytes: record.maxResultBytes
    });
    sendParent({ type: "result", result }, () => process.exit(0));
  } catch (error) {
    sendParent({ type: "fatal", error: formatError(error) }, () => process.exit(1));
  }
}

function isPositiveInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value > 0;
}

function hostRpc(request: unknown): Promise<Json> {
  return new Promise((resolve, reject) => {
    const id = nextRpcId;
    nextRpcId += 1;
    pendingRpc.set(id, { resolve, reject });
    sendParent({ type: "rpc", id, request }, error => {
      if (error) {
        pendingRpc.delete(id);
        reject(error);
      }
    });
  });
}

function sendParent(message: Record<string, unknown>, callback: (error?: Error | null) => void): void {
  if (!process.send) {
    callback(new Error("sandbox worker has no parent IPC channel"));
    return;
  }
  process.send(message, callback);
}

function rejectPending(error: Error): void {
  for (const pending of pendingRpc.values()) {
    pending.reject(error);
  }
  pendingRpc.clear();
}
