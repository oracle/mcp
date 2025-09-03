/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.mapper.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.mapper.McpToolMapper;
import io.modelcontextprotocol.spec.McpSchema;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.media.MediaType;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.oas.models.responses.ApiResponse;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.ParseOptions;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

/**
 * Implementation of {@link McpToolMapper} that converts an OpenAPI specification
 * into a list of {@link McpSchema.Tool} objects.
 * <p>
 * This class parses the OpenAPI JSON, extracts operations, parameters,
 * request/response schemas, and builds tool definitions compatible
 * with the MCP schema. Converted tools are also cached using
 * {@link McpServerCacheService}.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public class OpenApiToMcpToolMapper implements McpToolMapper {

    private final Set<String> usedNames = new HashSet<>();
    private final McpServerCacheService mcpServerCacheService;
    private static final Logger LOGGER = LoggerFactory.getLogger(OpenApiToMcpToolMapper.class);

    public OpenApiToMcpToolMapper(McpServerCacheService mcpServerCacheService) {
        this.mcpServerCacheService = mcpServerCacheService;
    }

    @Override
    public List<McpSchema.Tool> convert(JsonNode openApiJson) {
        LOGGER.debug("Parsing OpenAPI JsonNode to OpenAPI object...");
        OpenAPI openAPI = parseOpenApi(openApiJson);

        if (openAPI.getPaths() == null || openAPI.getPaths().isEmpty()) {
            throw new IllegalArgumentException("'paths' object not found in the specification.");
        }

        List<McpSchema.Tool> mcpTools = processPaths(openAPI);
        LOGGER.debug("Conversion complete. Total tools created: {}", mcpTools.size());
        updateToolsToCache(mcpTools);
        return mcpTools;
    }

    private List<McpSchema.Tool> processPaths(OpenAPI openAPI) {
        List<McpSchema.Tool> mcpTools = new ArrayList<>();

        for (Map.Entry<String, PathItem> pathEntry : openAPI.getPaths().entrySet()) {
            String path = pathEntry.getKey();
            PathItem pathItem = pathEntry.getValue();
            if (pathItem == null) continue;

            processOperationsForPath(path, pathItem, mcpTools);
        }
        return mcpTools;
    }

    private void processOperationsForPath(String path, PathItem pathItem, List<McpSchema.Tool> mcpTools) {
        for (Map.Entry<PathItem.HttpMethod, Operation> methodEntry : pathItem.readOperationsMap().entrySet()) {
            PathItem.HttpMethod method = methodEntry.getKey();
            Operation operation = methodEntry.getValue();
            if (operation == null) continue;

            McpSchema.Tool tool = buildToolFromOperation(path, method, operation);
            if (tool != null) {
                mcpTools.add(tool);
            }
        }
    }

    private McpSchema.Tool buildToolFromOperation(String path, PathItem.HttpMethod method, Operation operation) {
        String rawOperationId = (operation.getOperationId() != null && !operation.getOperationId().isEmpty())
                ? operation.getOperationId()
                : toCamelCase(method.name() + " " + path);

        String toolName = makeUniqueName(rawOperationId);
        LOGGER.debug("--- Parsing Operation: {} {} (ID: {}) ---", method.name().toUpperCase(), path, toolName);

        String toolTitle = (operation.getSummary() != null && !operation.getSummary().isEmpty())
                ? operation.getSummary()
                : toolName;
        String toolDescription = getDescription(operation);

        Map<String, Object> properties = new LinkedHashMap<>();
        List<String> requiredParams = new ArrayList<>();

        Map<String, Map<String, Object>> pathParams = new HashMap<>();
        Map<String, Map<String, Object>> queryParams = new HashMap<>();
        extractPathAndQueryParams(operation, pathParams, queryParams, properties, requiredParams);

        extractRequestBody(operation, properties, requiredParams);

        McpSchema.JsonSchema inputSchema = new McpSchema.JsonSchema(
                "object",
                properties.isEmpty() ? null : properties,
                requiredParams.isEmpty() ? null : requiredParams,
                false, null, null
        );
        Map<String, Object> outputSchema = extractOutputSchema(operation);
        outputSchema.put("additionalProperties", true);

        Map<String, Object> meta = buildMeta(method, path, operation, pathParams, queryParams);

        return McpSchema.Tool.builder()
                .title(toolTitle)
                .name(toolName)
                .description(toolDescription)
                .inputSchema(inputSchema)
                .outputSchema(outputSchema)
                .meta(meta)
                .build();
    }


    private Map<String, Object> buildMeta(PathItem.HttpMethod method, String path,
                                          Operation operation, Map<String, Map<String, Object>> pathParams,
                                          Map<String, Map<String, Object>> queryParams) {
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put("httpMethod", method.name());
        meta.put("path", path);
        if (operation.getTags() != null) {
            meta.put("tags", operation.getTags());
        }
        if (operation.getSecurity() != null) {
            meta.put("security", operation.getSecurity());
        }
        if (!pathParams.isEmpty()) {
            meta.put("pathParams", pathParams);
        }
        if (!queryParams.isEmpty()) {
            meta.put("queryParams", queryParams);
        }
        return meta;
    }

    private void extractPathAndQueryParams(Operation operation,
                                           Map<String, Map<String, Object>> pathParams,
                                           Map<String, Map<String, Object>> queryParams,
                                           Map<String, Object> properties,
                                           List<String> requiredParams) {
        if (operation.getParameters() != null) {
            for (Parameter param : operation.getParameters()) {
                if (param.getName() == null || param.getSchema() == null) continue;

                Map<String, Object> paramMeta = parameterMetaMap(param);
                if ("path".equalsIgnoreCase(param.getIn())) {
                    pathParams.put(param.getName(), paramMeta);
                } else if ("query".equalsIgnoreCase(param.getIn())) {
                    queryParams.put(param.getName(), paramMeta);
                }

                if ("path".equalsIgnoreCase(param.getIn()) || "query".equalsIgnoreCase(param.getIn())) {
                    Map<String, Object> paramSchema = extractInputSchema(param.getSchema());
                    if (param.getDescription() != null && !param.getDescription().isEmpty()) {
                        paramSchema.put("description", param.getDescription());
                    }
                    properties.put(param.getName(), paramSchema);
                    if (Boolean.TRUE.equals(param.getRequired())) {
                        requiredParams.add(param.getName());
                    }
                }
            }
        }
    }

    private void updateToolsToCache(List<McpSchema.Tool> tools) {
        for (McpSchema.Tool tool : tools) {
            mcpServerCacheService.putTool(tool.name(), tool);
        }
    }

    private String getDescription(Operation operation) {
        if (operation.getSummary() != null && !operation.getSummary().isEmpty()) {
            return operation.getSummary();
        } else if (operation.getDescription() != null && !operation.getDescription().isEmpty()) {
            return operation.getDescription();
        }
        return "";
    }

    private OpenAPI parseOpenApi(JsonNode jsonNode) {
        String jsonString = jsonNode.toString();
        ParseOptions options = new ParseOptions();
        options.setResolve(true);
        options.setResolveFully(true);
        return new OpenAPIV3Parser().readContents(jsonString, null, options).getOpenAPI();
    }

    private void extractRequestBody(Operation operation, Map<String, Object> properties, List<String> requiredParams) {
        if (operation.getRequestBody() != null && operation.getRequestBody().getContent() != null) {
            MediaType media = operation.getRequestBody().getContent().get("application/json");
            if (media != null && media.getSchema() != null) {
                Schema<?> bodySchema = media.getSchema();
                if ("object".equals(bodySchema.getType()) && bodySchema.getProperties() != null) {
                    bodySchema.getProperties().forEach((name, schema) -> {
                        properties.put(name, extractInputSchema((Schema<?>) schema));
                    });
                    if (bodySchema.getRequired() != null) {
                        requiredParams.addAll(bodySchema.getRequired());
                    }
                }
            }
        }
    }

    private Map<String, Object> extractInputSchema(Schema<?> openApiSchema) {
        if (openApiSchema == null) {
            return new LinkedHashMap<>();
        }

        Map<String, Object> jsonSchema = new LinkedHashMap<>();

        if (openApiSchema.getType() != null) jsonSchema.put("type", openApiSchema.getType());
        if (openApiSchema.getDescription() != null) jsonSchema.put("description", openApiSchema.getDescription());
        if (openApiSchema.getFormat() != null) jsonSchema.put("format", openApiSchema.getFormat());
        if (openApiSchema.getEnum() != null) jsonSchema.put("enum", openApiSchema.getEnum());

        if ("object".equals(openApiSchema.getType())) {
            if (openApiSchema.getProperties() != null) {
                Map<String, Object> nestedProperties = new LinkedHashMap<>();
                openApiSchema.getProperties().forEach((key, value) -> nestedProperties.put(key, extractInputSchema((Schema<?>) value)));
                jsonSchema.put("properties", nestedProperties);
            }
            if (openApiSchema.getRequired() != null) {
                jsonSchema.put("required", openApiSchema.getRequired());
            }
        }

        if ("array".equals(openApiSchema.getType())) {
            if (openApiSchema.getItems() != null) {
                jsonSchema.put("items", extractInputSchema(openApiSchema.getItems()));
            }
        }
        return jsonSchema;
    }

    private Map<String, Object> extractOutputSchema(Operation operation) {
        // This is the parent object that the tool schema requires.
        // It will ALWAYS have "type": "object".
        Map<String, Object> toolOutputSchema = new LinkedHashMap<>();
        toolOutputSchema.put("type", "object");

        // Find the actual response schema from the OpenAPI spec
        if (operation.getResponses() == null || operation.getResponses().isEmpty()) {
            return toolOutputSchema; // Return empty object schema if no responses
        }
        ApiResponse response = operation.getResponses().getOrDefault("200", operation.getResponses().get("default"));
        if (response == null || response.getContent() == null || !response.getContent().containsKey("application/json")) {
            return toolOutputSchema; // Return empty object schema
        }
        Schema<?> apiResponseSchema = response.getContent().get("application/json").getSchema();
        if (apiResponseSchema == null) {
            return toolOutputSchema; // Return empty object schema
        }

        // Recursively convert the OpenAPI response schema into a JSON schema map
        Map<String, Object> convertedApiResponseSchema = extractSchemaRecursive(apiResponseSchema);

        // Create the 'properties' map for our parent object
        Map<String, Object> properties = new LinkedHashMap<>();

        // Put the actual API response schema inside the properties map.
        // We'll use the key "response" to hold it.
        properties.put("response", convertedApiResponseSchema);

        toolOutputSchema.put("properties", properties);

        return toolOutputSchema;
    }

    private Map<String, Object> extractSchemaRecursive(Schema<?> schema) {
        if (schema == null) {
            return Collections.emptyMap();
        }

        Map<String, Object> jsonSchema = new LinkedHashMap<>();

        if (schema.getType() != null) jsonSchema.put("type", schema.getType());
        if (schema.getDescription() != null) jsonSchema.put("description", schema.getDescription());

        if ("object".equals(schema.getType()) && schema.getProperties() != null) {
            Map<String, Object> properties = new LinkedHashMap<>();
            for (Map.Entry<String, Schema> entry : schema.getProperties().entrySet()) {
                properties.put(entry.getKey(), extractSchemaRecursive(entry.getValue()));
            }
            jsonSchema.put("properties", properties);
        }

        if ("array".equals(schema.getType()) && schema.getItems() != null) {
            jsonSchema.put("items", extractSchemaRecursive(schema.getItems()));
        }

        if (schema.getRequired() != null) {
            jsonSchema.put("required", schema.getRequired());
        }

        return jsonSchema;
    }

    private Map<String, Object> parameterMetaMap(Parameter p) {
        Map<String, Object> paramMeta = new LinkedHashMap<>();
        paramMeta.put("name", p.getName());
        paramMeta.put("required", Boolean.TRUE.equals(p.getRequired()));
        if (p.getDescription() != null) {
            paramMeta.put("description", p.getDescription());
        }
        if (p.getSchema() != null && p.getSchema().getType() != null) {
            paramMeta.put("type", p.getSchema().getType());
        }
        return paramMeta;
    }

    private String makeUniqueName(String base) {
        String name = base;
        int counter = 1;
        while (usedNames.contains(name)) {
            name = base + "_" + counter++;
        }
        usedNames.add(name);
        return name;
    }

    private static String toCamelCase(String input) {
        String[] parts = input.split("[^a-zA-Z0-9]+");
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            if (parts[i].isEmpty()) continue;
            String word = parts[i].toLowerCase();
            if (i == 0) {
                sb.append(word);
            } else {
                sb.append(Character.toUpperCase(word.charAt(0))).append(word.substring(1));
            }
        }
        return sb.toString();
    }
}