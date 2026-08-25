/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { Readable, Writable } from "node:stream";

export const WORKER_CHANNEL_CONTRACT_VERSION = 1;

export type WorkerChannelStatus = {
  exitCode: number | null;
  signal: string | null;
};

/** Trusted-side transport used by the hostile framed worker protocol. */
export interface WorkerChannel {
  readonly output: Readable;
  readonly input: Writable;
  readonly closed: Promise<WorkerChannelStatus>;
  /** Idempotently close the transport and resolve after it can no longer carry data. */
  stop(): Promise<void>;
}
