/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname } from "node:path";

const require = createRequire(new URL("../package.json", import.meta.url));
const manifestPath = require.resolve("isolated-vm/package.json");
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
if (manifest.name !== "isolated-vm" || manifest.version !== "7.0.0" ||
    manifest.scripts?.install !== "node-gyp-build || node-gyp rebuild --release -j max") {
  throw new Error("Native setup requires the reviewed isolated-vm 7.0.0 install command");
}

// An explicit run activates only this reviewed command. The flag continues to
// suppress preinstall/postinstall even outside the repository's npm config.
execFileSync("npm", ["--ignore-scripts", "--prefix", dirname(manifestPath), "run", "install"], { stdio: "inherit" });
require("isolated-vm");
console.log("Reviewed isolated-vm 7.0.0 native setup and load completed");
