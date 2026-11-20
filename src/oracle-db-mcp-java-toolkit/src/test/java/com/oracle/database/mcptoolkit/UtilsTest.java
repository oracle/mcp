/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit;

import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class UtilsTest {
  @TempDir
  Path temporaryDirectory;

  @Test
  void rejectsMissingRuntimeConfigFile() {
    assertThrows(IllegalStateException.class,
        () -> Utils.loadRuntimeConfig(temporaryDirectory.resolve("missing.yaml").toString()));
  }

  @Test
  void rejectsMalformedRuntimeConfigFile() throws IOException {
    Path runtimeConfig = temporaryDirectory.resolve("runtime.yaml");
    Files.writeString(runtimeConfig, "network: [");

    assertThrows(IllegalStateException.class, () -> Utils.loadRuntimeConfig(runtimeConfig.toString()));
  }

  @Test
  void rejectsRuntimeConfigWithMissingEnvironmentVariable() throws IOException {
    Path runtimeConfig = temporaryDirectory.resolve("runtime.yaml");
    Files.writeString(runtimeConfig, "database:\n  password: ${MISSING_RUNTIME_CONFIG_TEST_VALUE}\n");

    assertThrows(IllegalStateException.class, () -> Utils.loadRuntimeConfig(runtimeConfig.toString()));
  }
}
