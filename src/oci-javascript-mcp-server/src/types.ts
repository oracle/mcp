/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

export type Json = null | boolean | number | string | Json[] | JsonObject;
export type JsonObject = { [key: string]: Json };

export type ExecutionError = JsonObject & { message: string };

export type ExecutionResult = {
  result: Json;
  error: ExecutionError | null;
  stdout: string;
  stderr: string;
  exitCode: number;
  timedOut: boolean;
};

export type ClientOptions = { region?: string };

export type OciInvokePayload = {
  service: string;
  client: { name: string; options?: ClientOptions };
  operation: string;
  request?: JsonObject;
};

export type OciDiscoverFilter = {
  service?: string;
  client?: string;
  operation?: string;
};

export type ReflectionManifest = {
  services: Record<string, {
    clients: Record<string, {
      operations: string[];
      requestFields?: Record<string, string[]>;
    }>;
  }>;
};

export type RpcOperation = "config" | "invoke";

export type GuestRpcRequest = {
  operation: RpcOperation;
  payload: JsonObject;
};

export type ProviderCapabilities = Readonly<{
  provider: string;
  boundary: "process" | "container" | "virtual-machine";
  developmentOnly: boolean;
  separateGuestKernel: boolean;
  hardwareVirtualization: boolean;
  networkCreationBlocked: boolean;
}>;

export type ExecutionPolicy = Readonly<{
  allowedOperations: ReadonlySet<string>;
  allowMutations: boolean;
  allowedRegions?: ReadonlySet<string>;
  allowedTenancyIds?: ReadonlySet<string>;
  allowedCompartmentIds?: ReadonlySet<string>;
  allowedResourceIds?: ReadonlySet<string>;
  allowedRequestFields?: ReadonlyMap<string, ReadonlySet<string>>;
  maxCalls: number;
  maxConcurrentCalls: number;
  maxRequestBytes: number;
  maxResponseBytes: number;
  deadlineMs: number;
  maxRetries: number;
}>;

export type BrokerHandler = (request: GuestRpcRequest) => Promise<Json>;

export type IsolationExecution = {
  result: Promise<ExecutionResult>;
  destroy(): Promise<void>;
};

export interface IsolationProvider {
  readonly capabilities: ProviderCapabilities;
  start(input: {
    code: string;
    manifest: ReflectionManifest;
    deadlineMs: number;
    maxResultBytes: number;
    maxOutputBytes: number;
    broker: BrokerHandler;
    signal?: AbortSignal;
  }): Promise<IsolationExecution>;
}
