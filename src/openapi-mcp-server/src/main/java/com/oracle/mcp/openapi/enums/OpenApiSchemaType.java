package com.oracle.mcp.openapi.enums;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

public enum OpenApiSchemaType {
    JSON,
    YAML,
    UNKNOWN;

    // 1. Create reusable, thread-safe mapper instances. This is much more efficient.
    private static final ObjectMapper JSON_MAPPER = new ObjectMapper();
    private static final ObjectMapper YAML_MAPPER = new ObjectMapper(new YAMLFactory());

    /**
     * Determines the schema file type from a string by attempting to parse it.
     *
     * @param dataString The string content of the schema file.
     * @return The determined OpenApiSchemaFileType (JSON, YAML, or UNKNOWN).
     */
    public static OpenApiSchemaType getType(String dataString) {
        if (dataString == null || dataString.trim().isEmpty()) {
            return UNKNOWN;
        }

        // First, try to parse as JSON
        try {
            JSON_MAPPER.readTree(dataString);
            return JSON;
        } catch (JsonProcessingException e) {
            // It's not JSON, so we proceed to check for YAML.
        }

        // If JSON parsing failed, try YAML
        try {
            YAML_MAPPER.readTree(dataString);
            return YAML;
        } catch (JsonProcessingException e) {
            // It's not YAML either.
        }

        // If both attempts fail, return UNKNOWN
        return UNKNOWN;
    }
}