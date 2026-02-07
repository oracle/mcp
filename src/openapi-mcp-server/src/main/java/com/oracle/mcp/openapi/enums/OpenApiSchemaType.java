/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.enums;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

/**
 * Represents the format of an OpenAPI specification file.
 * <p>
 * This enum is used to identify whether a given specification is written in JSON or YAML,
 * or if its format cannot be determined.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public enum OpenApiSchemaType {
    /**
     * The specification is in JSON format.
     */
    JSON,
    /**
     * The specification is in YAML format.
     */
    YAML,
    /**
     * The format of the specification could not be determined.
     */
    UNKNOWN;

    /**
     * A reusable, thread-safe mapper instance for parsing JSON content.
     */
    private static final ObjectMapper JSON_MAPPER = new ObjectMapper();
    /**
     * A reusable, thread-safe mapper instance for parsing YAML content.
     */
    private static final ObjectMapper YAML_MAPPER = new ObjectMapper(new YAMLFactory());

    /**
     * Determines the schema file type from its string content by attempting to parse it.
     * <p>
     * This method first tries to parse the input string as JSON. If that fails, it
     * then attempts to parse it as YAML. If both attempts fail, or if the input is
     * null or empty, it returns {@link #UNKNOWN}.
     *
     * @param dataString The string content of the OpenAPI specification.
     * @return The determined {@code OpenApiSchemaType} ({@link #JSON}, {@link #YAML}, or {@link #UNKNOWN}).
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