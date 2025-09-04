/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.mapper;

import com.fasterxml.jackson.databind.JsonNode;
import com.oracle.mcp.openapi.exception.McpServerToolInitializeException;
import io.modelcontextprotocol.spec.McpSchema;

import java.util.List;

/**
 * Mapper interface for converting OpenAPI specifications into
 * {@link McpSchema.Tool} representations.
 * <p>
 * Implementations of this interface are responsible for reading a parsed
 * API specification (as a Jackson {@link JsonNode}) and mapping it into
 * a list of tool definitions that conform to the MCP schema.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public interface McpToolMapper {

    /**
     * Converts an OpenAPI specification into a list of MCP tools.
     *
     * @param apiSpec the OpenAPI specification represented as a {@link JsonNode};
     *                must not be {@code null}.
     * @return a list of {@link McpSchema.Tool} objects derived from the given API specification;
     *         never {@code null}, but may be empty if no tools are found.
     */
    List<McpSchema.Tool> convert(JsonNode apiSpec) throws McpServerToolInitializeException;
}
