/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.mapper.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.constants.CommonConstant;
import com.oracle.mcp.openapi.constants.ErrorMessage;
import com.oracle.mcp.openapi.exception.McpServerToolInitializeException;
import com.oracle.mcp.openapi.mapper.McpToolMapper;
import com.oracle.mcp.openapi.util.McpServerUtil;
import io.modelcontextprotocol.spec.McpSchema;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.media.MediaType;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.ParseOptions;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Set;
import java.util.Map;


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

    private final McpServerCacheService mcpServerCacheService;
    private static final Logger LOGGER = LoggerFactory.getLogger(OpenApiToMcpToolMapper.class);

    public OpenApiToMcpToolMapper(McpServerCacheService mcpServerCacheService) {
        this.mcpServerCacheService = mcpServerCacheService;
    }

    @Override
    public List<McpSchema.Tool> convert(JsonNode openApiJson) throws McpServerToolInitializeException {
        LOGGER.debug("Parsing OpenAPI schema to OpenAPI object.");
        OpenAPI openAPI = parseOpenApi(openApiJson);
        LOGGER.debug("Successfully parsed OpenAPI schema");
        if (openAPI.getPaths() == null || openAPI.getPaths().isEmpty()) {
            LOGGER.error("There is not paths defined in schema ");
            throw new McpServerToolInitializeException(ErrorMessage.MISSING_PATH_IN_SPEC);
        }

        List<McpSchema.Tool> mcpTools = processPaths(openAPI);
        LOGGER.debug("Conversion complete. Total tools created: {}", mcpTools.size());
        updateToolsToCache(mcpTools);
        return mcpTools;
    }

    private List<McpSchema.Tool> processPaths(OpenAPI openAPI) {
        List<McpSchema.Tool> mcpTools = new ArrayList<>();
        Set<String> toolNames = new HashSet<>();
        for (Map.Entry<String, PathItem> pathEntry : openAPI.getPaths().entrySet()) {
            String path = pathEntry.getKey();
            LOGGER.debug("Parsing Path: {}", path);
            PathItem pathItem = pathEntry.getValue();
            if (pathItem == null){
                continue;
            }

            processOperationsForPath(path, pathItem, mcpTools,toolNames);
        }
        return mcpTools;
    }

    private void processOperationsForPath(String path, PathItem pathItem, List<McpSchema.Tool> mcpTools,Set<String> toolNames) {
        for (Map.Entry<PathItem.HttpMethod, Operation> methodEntry : pathItem.readOperationsMap().entrySet()) {
            PathItem.HttpMethod method = methodEntry.getKey();
            Operation operation = methodEntry.getValue();
            if (operation == null){
                continue;
            }

            McpSchema.Tool tool = buildToolFromOperation(path, method, operation,toolNames);
            if (tool != null) {
                mcpTools.add(tool);
            }
        }
    }

    private McpSchema.Tool buildToolFromOperation(String path, PathItem.HttpMethod method, Operation operation, Set<String> toolNames) {
        String rawOperationId = (operation.getOperationId() != null && !operation.getOperationId().isEmpty())
                ? operation.getOperationId()
                : McpServerUtil.toCamelCase(method.name() + " " + path);

        String toolName = makeUniqueName(toolNames,rawOperationId);
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
                CommonConstant.OBJECT,
                properties.isEmpty() ? null : properties,
                requiredParams.isEmpty() ? null : requiredParams,
                false, null, null
        );
        Map<String, Object> outputSchema = getOutputSchema();

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

    private Map<String, Object> getOutputSchema() {
        Map<String, Object> outputSchema = new HashMap<>();
        outputSchema.put(CommonConstant.ADDITIONAL_PROPERTIES, true);
        return outputSchema;
    }


    private Map<String, Object> buildMeta(PathItem.HttpMethod method, String path,
                                          Operation operation, Map<String, Map<String, Object>> pathParams,
                                          Map<String, Map<String, Object>> queryParams) {
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put(CommonConstant.HTTP_METHOD, method.name());
        meta.put(CommonConstant.PATH, path);
        if (operation.getTags() != null) {
            meta.put(CommonConstant.TAGS, operation.getTags());
        }
        if (operation.getSecurity() != null) {
            meta.put(CommonConstant.SECURITY, operation.getSecurity());
        }
        if (!pathParams.isEmpty()) {
            meta.put(CommonConstant.PATH_PARAMS, pathParams);
        }
        if (!queryParams.isEmpty()) {
            meta.put(CommonConstant.QUERY_PARAMS, queryParams);
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
                if (param.getName() == null || param.getSchema() == null){
                    continue;
                }

                Map<String, Object> paramMeta = parameterMetaMap(param);
                if (CommonConstant.PATH.equalsIgnoreCase(param.getIn())) {
                    pathParams.put(param.getName(), paramMeta);
                } else if (CommonConstant.QUERY.equalsIgnoreCase(param.getIn())) {
                    queryParams.put(param.getName(), paramMeta);
                }

                if (CommonConstant.PATH.equalsIgnoreCase(param.getIn()) || CommonConstant.QUERY.equalsIgnoreCase(param.getIn())) {
                    Map<String, Object> paramSchema = extractInputSchema(param.getSchema());
                    if (param.getDescription() != null && !param.getDescription().isEmpty()) {
                        paramSchema.put(CommonConstant.DESCRIPTION, param.getDescription());
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
            MediaType media = operation.getRequestBody().getContent().get(CommonConstant.APPLICATION_JSON);
            if (media != null && media.getSchema() != null) {
                Schema<?> bodySchema = media.getSchema();
                if (CommonConstant.OBJECT.equals(bodySchema.getType()) && bodySchema.getProperties() != null) {
                    bodySchema.getProperties().forEach((name, schema) ->
                        properties.put(name, extractInputSchema((Schema<?>) schema))
                    );
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

        if (openApiSchema.getType() != null){
            jsonSchema.put(CommonConstant.TYPE, openApiSchema.getType());
        }
        if (openApiSchema.getDescription() != null){
            jsonSchema.put(CommonConstant.DESCRIPTION, openApiSchema.getDescription());
        }
        if (openApiSchema.getFormat() != null){
            jsonSchema.put(CommonConstant.FORMAT, openApiSchema.getFormat());
        }
        if (openApiSchema.getEnum() != null){
            jsonSchema.put(CommonConstant.ENUM, openApiSchema.getEnum());
        }

        if (CommonConstant.OBJECT.equals(openApiSchema.getType())) {
            if (openApiSchema.getProperties() != null) {
                Map<String, Object> nestedProperties = new LinkedHashMap<>();
                openApiSchema.getProperties().forEach((key, value) -> nestedProperties.put(key, extractInputSchema((Schema<?>) value)));
                jsonSchema.put(CommonConstant.PROPERTIES, nestedProperties);
            }
            if (openApiSchema.getRequired() != null) {
                jsonSchema.put(CommonConstant.REQUIRED, openApiSchema.getRequired());
            }
        }

        if (CommonConstant.ARRAY.equals(openApiSchema.getType())) {
            if (openApiSchema.getItems() != null) {
                jsonSchema.put(CommonConstant.ITEMS, extractInputSchema(openApiSchema.getItems()));
            }
        }
        return jsonSchema;
    }

    private Map<String, Object> parameterMetaMap(Parameter p) {
        Map<String, Object> paramMeta = new LinkedHashMap<>();
        paramMeta.put(CommonConstant.NAME, p.getName());
        paramMeta.put(CommonConstant.REQUIRED, Boolean.TRUE.equals(p.getRequired()));
        if (p.getDescription() != null) {
            paramMeta.put(CommonConstant.DESCRIPTION, p.getDescription());
        }
        if (p.getSchema() != null && p.getSchema().getType() != null) {
            paramMeta.put(CommonConstant.TYPE, p.getSchema().getType());
        }
        return paramMeta;
    }

    private String makeUniqueName(Set<String> toolNames,String base) {
        String name = base;
        int counter = 1;
        while (toolNames.contains(name)) {
            name = base + CommonConstant.UNDER_SCORE + counter++;
        }
        toolNames.add(name);
        return name;
    }
}