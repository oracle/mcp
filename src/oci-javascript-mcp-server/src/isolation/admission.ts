/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { IsolationProvider } from "../types.ts";

export function admitProvider(provider: IsolationProvider, mode: "development" | "production"): void {
  const capabilities = provider.capabilities;
  if (mode === "development") return;
  if (capabilities.developmentOnly
    || capabilities.boundary !== "virtual-machine"
    || !capabilities.separateGuestKernel
    || !capabilities.hardwareVirtualization
    || !capabilities.networkCreationBlocked) {
    throw new Error(
      `isolation provider '${capabilities.provider}' is not admitted in production: `
      + "an approved VM boundary with a separate guest kernel and blocked network creation is required"
    );
  }
}
