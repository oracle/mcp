/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

export type Json =
  | null
  | boolean
  | number
  | string
  | Json[]
  | { [key: string]: Json };

export type JsonObject = { [key: string]: Json };

export type SandboxResult = {
  result: Json;
  stdout: string;
  stderr: string;
  exitCode: number;
  timedOut: boolean;
};

export type HostRpcRequest = {
  binding: "oracle";
  namespace: "oci";
  operation: "invoke" | "config" | "discover";
  payload: JsonObject;
};

export type HostRpcHandler = (request: HostRpcRequest, timeoutMs?: number) => Promise<Json>;

export type OciReflectionManifest = {
  services: {
    [service: string]: {
      clients: {
        [client: string]: {
          operations: string[];
        };
      };
    };
  };
};

export type OciInvokePayload = {
  service: string;
  client: {
    name: string;
    options?: {
      region?: string;
    };
  };
  operation: string;
  request?: JsonObject;
};

export type OciDiscoverPayload = {
  service?: string;
  client?: string;
  operation?: string;
};
