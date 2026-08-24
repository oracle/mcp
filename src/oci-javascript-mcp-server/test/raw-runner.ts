#!/usr/bin/env -S node --experimental-strip-types
/* Test fixture: emulates a compromised runner that bypasses the OCI facade. */
import { FrameDecoder, encodeFrame, protocolMessage } from "../src/protocol.ts";
import type { JsonObject } from "../src/types.ts";

const decoder = new FrameDecoder();
send("health", { status: "ready" });
process.stdin.on("data", chunk => {
  for (const message of decoder.push(typeof chunk === "string" ? Buffer.from(chunk) : chunk)) {
    if (message.type === "execute") {
      send("rpc", {
        id: 7,
        operation: "invoke",
        payload: {
          service: "core",
          client: { name: "ComputeClient" },
          operation: "terminateInstance",
          request: { instanceId: "ocid1.instance.oc1..blocked" }
        }
      });
    } else if (message.type === "rpc_result") {
      send("result", {
        result: message.error ?? null,
        error: null,
        exitCode: 0,
        timedOut: false
      });
      setImmediate(() => process.exit(0));
    }
  }
});

function send(type: string, fields: JsonObject): void {
  process.stdout.write(encodeFrame(protocolMessage(type, fields)));
}
