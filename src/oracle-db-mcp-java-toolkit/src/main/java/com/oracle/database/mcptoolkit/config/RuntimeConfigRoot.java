/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.config;

import com.oracle.database.mcptoolkit.EnvSubstitutor;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Represents runtime settings formerly supplied as JVM system properties.
 * This intentionally uses a separate YAML file from custom tool and datasource configuration.
 */
public class RuntimeConfigRoot {
  private final Map<String, String> properties = new LinkedHashMap<>();

  /** Creates a runtime configuration by flattening its nested YAML sections into property names. */
  public static RuntimeConfigRoot fromYaml(Map<?, ?> yaml) {
    RuntimeConfigRoot config = new RuntimeConfigRoot();
    if (yaml != null) config.flatten(null, yaml);
    return config;
  }

  /** Creates a runtime configuration from already-flattened properties. */
  public static RuntimeConfigRoot fromProperties(Map<String, String> properties) {
    RuntimeConfigRoot config = new RuntimeConfigRoot();
    if (properties != null) {
      properties.forEach((name, value) ->
          config.properties.put(RuntimePropertyNames.canonicalName(name), value));
    }
    return config;
  }

  public Map<String, String> properties() {
    return properties;
  }

  /** Substitutes environment variables in runtime settings. */
  public void substituteEnvVars() {
    properties.replaceAll((key, value) -> EnvSubstitutor.substituteEnvVars(value));
  }

  private void flatten(String prefix, Map<?, ?> section) {
    for (Map.Entry<?, ?> entry : section.entrySet()) {
      if (!(entry.getKey() instanceof String key) || key.isBlank()) {
        throw new IllegalArgumentException("Runtime configuration keys must be non-blank strings");
      }
      String propertyName = prefix == null ? key : prefix + "." + key;
      Object value = entry.getValue();
      if (value instanceof Map<?, ?> nestedSection) {
        flatten(propertyName, nestedSection);
      } else if (value != null) {
        properties.put(RuntimePropertyNames.canonicalName(propertyName), value.toString());
      }
    }
  }
}
