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
import com.oracle.mcp.openapi.model.override.ToolOverride;
import com.oracle.mcp.openapi.model.override.ToolOverridesConfig;
import com.oracle.mcp.openapi.util.McpServerUtil;
import io.modelcontextprotocol.spec.McpSchema;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.ParseOptions;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.Collections;
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
    public List<McpSchema.Tool> convert(JsonNode openApiJson, ToolOverridesConfig toolOverridesConfig) throws McpServerToolInitializeException {
        LOGGER.debug("Parsing OpenAPI schema to OpenAPI object.");
        OpenAPI openAPI = parseOpenApi(openApiJson);
        LOGGER.debug("Successfully parsed OpenAPI schema");
        return convert(openAPI,toolOverridesConfig);

    }

    public List<McpSchema.Tool> convert(OpenAPI openAPI, ToolOverridesConfig toolOverridesConfig) throws McpServerToolInitializeException {
        if(openAPI==null){
            LOGGER.error("No schema found.");
            return Collections.emptyList();
        }
        if (openAPI.getPaths() == null || openAPI.getPaths().isEmpty()) {
            LOGGER.error("No paths defined in schema.");
            throw new McpServerToolInitializeException(ErrorMessage.MISSING_PATH_IN_SPEC);
        }

        List<McpSchema.Tool> mcpTools = processPaths(openAPI, toolOverridesConfig);
        LOGGER.debug("Conversion complete. Total tools created: {}", mcpTools.size());
        updateToolsToCache(mcpTools);
        return mcpTools;
    }

    private List<McpSchema.Tool> processPaths(OpenAPI openAPI, ToolOverridesConfig toolOverridesConfig) {
        List<McpSchema.Tool> mcpTools = new ArrayList<>();
        Set<String> toolNames = new HashSet<>();

        for (Map.Entry<String, PathItem> pathEntry : openAPI.getPaths().entrySet()) {
            String path = pathEntry.getKey();
            LOGGER.debug("Parsing Path: {}", path);
            PathItem pathItem = pathEntry.getValue();
            if (pathItem == null) continue;

            processOperationsForPath(openAPI, path, pathItem, mcpTools, toolNames, toolOverridesConfig);
        }
        return mcpTools;
    }

    private void processOperationsForPath(OpenAPI openAPI, String path, PathItem pathItem,
                                          List<McpSchema.Tool> mcpTools, Set<String> toolNames,
                                          ToolOverridesConfig toolOverridesConfig) {
        for (Map.Entry<PathItem.HttpMethod, Operation> methodEntry : pathItem.readOperationsMap().entrySet()) {
            PathItem.HttpMethod method = methodEntry.getKey();
            Operation operation = methodEntry.getValue();
            if (operation == null){
                continue;
            }

            McpSchema.Tool tool = buildToolFromOperation(openAPI, path, method, operation, toolNames, toolOverridesConfig);
            if (tool != null){
                mcpTools.add(tool);
            }
        }
    }

    private McpSchema.Tool buildToolFromOperation(OpenAPI openAPI, String path, PathItem.HttpMethod method,
                                                  Operation operation, Set<String> toolNames,
                                                  ToolOverridesConfig toolOverridesConfig) {

        String toolName = generateToolName(method.name(), path, operation.getOperationId(), toolNames);

        if (skipTool(toolName, toolOverridesConfig)) {
            LOGGER.debug("Skipping tool: {} as it is in tool override file", toolName);
            return null;
        }

        LOGGER.debug("--- Parsing Operation: {} {} (ID: {}) ---", method.name().toUpperCase(), path, toolName);

        ToolOverride toolOverride = toolOverridesConfig.getTools().getOrDefault(toolName, ToolOverride.EMPTY_TOOL_OVERRIDE);
        String toolTitle = getToolTitle(operation, toolOverride, toolName);
        String toolDescription = getToolDescription(operation, toolOverride);
        Map<String, Schema> componentsSchemas = openAPI.getComponents() != null ? openAPI.getComponents().getSchemas() : new HashMap<>();

        // Input Schema
        McpSchema.JsonSchema inputSchema = getInputSchema(operation, componentsSchemas);

        // Output Schema
        Map<String, Object> outputSchema = getOutputSchema();

        // Params
        Map<String, Map<String, Object>> pathParams = new HashMap<>();
        Map<String, Map<String, Object>> queryParams = new HashMap<>();
        Map<String, Map<String, Object>> headerParams = new HashMap<>();
        Map<String, Map<String, Object>> cookieParams = new HashMap<>();
        populatePathQueryHeaderCookieParams(operation, pathParams, queryParams, headerParams, cookieParams);

        // Meta
        Map<String, Object> meta = buildMeta(method, path, operation, pathParams, queryParams, headerParams, cookieParams);

        return McpSchema.Tool.builder()
                .title(toolTitle)
                .name(toolName)
                .description(toolDescription)
                .inputSchema(inputSchema)
                .outputSchema(outputSchema)
                .meta(meta)
                .build();
    }

    public void populatePathQueryHeaderCookieParams(Operation operation,
                                                    Map<String, Map<String, Object>> pathParams,
                                                    Map<String, Map<String, Object>> queryParams,
                                                    Map<String, Map<String, Object>> headerParams,
                                                    Map<String, Map<String, Object>> cookieParams) {
        if (operation.getParameters() != null) {
            for (Parameter param : operation.getParameters()) {
                Map<String, Object> propSchema = createPropertySchema(
                        param.getSchema(),
                        param.getDescription(),
                        param.getSchema() != null ? param.getSchema().getEnum() : null
                );

                String name = param.getName();

                switch (param.getIn()) {
                    case "path" -> pathParams.put(name, propSchema);
                    case "query" -> queryParams.put(name, propSchema);
                    case "header" -> headerParams.put(name, propSchema);
                    case "cookie" -> cookieParams.put(name, propSchema);
                    default -> LOGGER.warn("Unknown parameter location: {}", param.getIn());
                }
            }
        }
    }

    private Map<String, Object> createPropertySchema(Schema<?> schema, String description, List<?> enums) {
        Map<String, Object> propSchema = new LinkedHashMap<>();
        propSchema.put("type", mapOpenApiType(schema != null ? schema.getType() : null));
        if (description != null){
            propSchema.put("description", description);
        }
        if (enums != null){
            propSchema.put("enum", enums);
        }
        return propSchema;
    }

    private String getToolTitle(Operation operation, ToolOverride toolOverride, String toolName) {
        String overrideTitle = toolOverride.getTitle();
        if (McpServerUtil.isNotBlank(overrideTitle)){
            return overrideTitle;
        }

        return (operation.getSummary() != null && !operation.getSummary().isEmpty())
                ? operation.getSummary()
                : toolName;
    }

    private String getToolDescription(Operation operation, ToolOverride toolOverride) {
        String overrideDescription = toolOverride.getDescription();
        if (McpServerUtil.isNotBlank(overrideDescription)){
            return overrideDescription;
        }
        if (McpServerUtil.isNotBlank(operation.getSummary())){
            return operation.getSummary();
        }
        if (McpServerUtil.isNotBlank(operation.getDescription())){
            return operation.getDescription();
        }
        return "";
    }

    private Map<String, Object> getOutputSchema() {
        Map<String, Object> outputSchema = new HashMap<>();
        outputSchema.put("type","object");
        outputSchema.put(CommonConstant.ADDITIONAL_PROPERTIES, true);
        return outputSchema;
    }

    private Map<String, Object> buildMeta(PathItem.HttpMethod method, String path, Operation operation,
                                          Map<String, Map<String, Object>> pathParams,
                                          Map<String, Map<String, Object>> queryParams,
                                          Map<String, Map<String, Object>> headerParams,
                                          Map<String, Map<String, Object>> cookieParams) {
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put(CommonConstant.HTTP_METHOD, method.name());
        meta.put(CommonConstant.PATH, path);

        if (operation.getTags() != null){
            meta.put(CommonConstant.TAGS, operation.getTags());
        }
        if (operation.getSecurity() != null){
            meta.put(CommonConstant.SECURITY, operation.getSecurity());
        }

        if (!pathParams.isEmpty()){
            meta.put(CommonConstant.PATH_PARAMS, pathParams);
        }
        if (!queryParams.isEmpty()){
            meta.put(CommonConstant.QUERY_PARAMS, queryParams);
        }
        if (!headerParams.isEmpty()){
            meta.put(CommonConstant.HEADER_PARAMS, headerParams);
        }
        if (!cookieParams.isEmpty()){
            meta.put(CommonConstant.COOKIE_PARAMS, cookieParams);
        }

        return meta;
    }

    private void updateToolsToCache(List<McpSchema.Tool> tools) {
        for (McpSchema.Tool tool : tools) {
            mcpServerCacheService.putTool(tool.name(), tool);
        }
    }

    private OpenAPI parseOpenApi(JsonNode jsonNode) {
        String jsonString = jsonNode.toString();
        ParseOptions options = new ParseOptions();
        options.setResolve(true);
        options.setResolveFully(true);

        SwaggerParseResult result = new OpenAPIV3Parser().readContents(jsonString, null, options);
        List<String> messages = result.getMessages();
        if (messages != null && !messages.isEmpty()) {
            LOGGER.info("OpenAPI validation errors: {}", messages);
        }
        return result.getOpenAPI();
    }

    private McpSchema.JsonSchema getInputSchema(Operation operation, Map<String, Schema> componentsSchemas) {
        Map<String, Object> properties = new LinkedHashMap<>();
        List<String> required = new ArrayList<>();
        Set<String> visitedRefs = new HashSet<>();

        handleParameters(operation.getParameters(), properties, required, componentsSchemas, visitedRefs);

        if (operation.getRequestBody() != null && operation.getRequestBody().getContent() != null) {
            Schema<?> bodySchema = operation.getRequestBody().getContent().get("application/json") != null
                    ? operation.getRequestBody().getContent().get("application/json").getSchema()
                    : null;

            if (bodySchema != null) {
                bodySchema = resolveRef(bodySchema, componentsSchemas, visitedRefs);
                Map<String, Object> bodyProps = buildSchemaRecursively(bodySchema, componentsSchemas, visitedRefs);

                // Flatten object-only allOf, keep combinators nested
                if ("object".equals(bodyProps.get("type"))) {
                    Map<String, Object> topProps = new LinkedHashMap<>();
                    mergeAllOfProperties(bodyProps, topProps);
                    // merge top-level properties into final properties
                    properties.putAll(topProps);
                    // merge required
                    if (bodyProps.get("required") instanceof List<?> reqList) {
                        reqList.forEach(r -> required.add((String) r));
                    }
                } else {
                    // Non-object root schema, wrap under "body"
                    properties.put("body", bodyProps);
                    if (Boolean.TRUE.equals(operation.getRequestBody().getRequired())) {
                        required.add("body");
                    }
                }
            }
        }
        return new McpSchema.JsonSchema(
                "object",
                properties.isEmpty() ? null : properties,
                required.isEmpty() ? null : required,
                false,
                null,
                null
        );
    }


    private void handleParameters(List<Parameter> parameters,
                                  Map<String, Object> properties,
                                  List<String> required,
                                  Map<String, Schema> componentsSchemas,
                                  Set<String> visitedRefs) {
        if (parameters != null) {
            for (Parameter param : parameters) {
                Schema<?> schema = resolveRef(param.getSchema(), componentsSchemas, visitedRefs);
                Map<String, Object> propSchema = buildSchemaRecursively(schema, componentsSchemas, visitedRefs);

                String name = param.getName();
                if (name != null && !name.isEmpty()) {
                    properties.put(name, propSchema);

                    if (Boolean.TRUE.equals(param.getRequired())) {
                        required.add(name);
                    }
                } else {
                    // fallback: generate a safe name if missing
                    String safeName = "param_" + properties.size();
                    properties.put(safeName, propSchema);
                    if (Boolean.TRUE.equals(param.getRequired())) {
                        required.add(safeName);
                    }
                }

                // Log a warning if the location is unknown, but still include it
                if (!Set.of("path", "query", "header", "cookie").contains(param.getIn())) {
                    LOGGER.warn("Unknown parameter location '{}', still adding '{}' to tool schema",
                            param.getIn(), name);
                }
            }
        }
    }

    @SuppressWarnings("unchecked")
    private void mergeAllOfProperties(Map<String, Object> schema, Map<String, Object> target) {
        if (schema.containsKey("allOf")) {
            List<Map<String, Object>> allOfList = (List<Map<String, Object>>) schema.get("allOf");
            for (Map<String, Object> item : allOfList) {
                // Merge top-level properties
                if (item.get("properties") instanceof Map<?, ?> props) {
                    props.forEach((k, v) -> target.put((String) k, v));
                }
                // Merge combinators into the target map
                for (String comb : new String[]{"anyOf", "oneOf", "allOf"}) {
                    if (item.containsKey(comb)) {
                        target.put(comb, item.get(comb));
                    }
                }
            }
        }
        // Merge root-level properties if exist
        if (schema.get("properties") instanceof Map<?, ?> props) {
            props.forEach((k, v) -> target.put((String) k, v));
        }
    }

    private Map<String, Object> buildSchemaRecursively(Schema<?> schema,
                                                       Map<String, Schema> componentsSchemas,
                                                       Set<String> visitedRefs) {
        if (schema == null){
            return Map.of("type", "string");
        }

        schema = resolveRef(schema, componentsSchemas, visitedRefs);
        Map<String, Object> result = new LinkedHashMap<>();

        // Handle combinators
        if (schema.getAllOf() != null) {
            List<Map<String, Object>> allOfList = new ArrayList<>();
            for (Schema<?> s : schema.getAllOf()) {
                allOfList.add(buildSchemaRecursively(s, componentsSchemas, visitedRefs));
            }
            result.put("allOf", allOfList);
        }
        if (schema.getOneOf() != null) {
            List<Map<String, Object>> oneOfList = new ArrayList<>();
            for (Schema<?> s : schema.getOneOf()) {
                oneOfList.add(buildSchemaRecursively(s, componentsSchemas, visitedRefs));
            }
            result.put("oneOf", oneOfList);
        }
        if (schema.getAnyOf() != null) {
            List<Map<String, Object>> anyOfList = new ArrayList<>();
            for (Schema<?> s : schema.getAnyOf()) {
                anyOfList.add(buildSchemaRecursively(s, componentsSchemas, visitedRefs));
            }
            result.put("anyOf", anyOfList);
        }

        // Primitive / object / array
        String type = mapOpenApiType(schema.getType());
        result.put("type", type);
        if (schema.getDescription() != null){
            result.put("description", schema.getDescription());
        }
        if (schema.getEnum() != null){
            result.put("enum", schema.getEnum());
        }

        if ("object".equals(type)) {
            Map<String, Object> props = new LinkedHashMap<>();
            if (schema.getProperties() != null) {
                for (Map.Entry<String, Schema> e : schema.getProperties().entrySet()) {
                    props.put(e.getKey(),
                            buildSchemaRecursively(resolveRef(e.getValue(), componentsSchemas, visitedRefs),
                                    componentsSchemas, visitedRefs));
                }
            }
            // Merge allOf properties and nested combinators
            mergeAllOfProperties(result, props);

            result.put("properties", props);
            if (schema.getRequired() != null){
                result.put("required", new ArrayList<>(schema.getRequired()));
            }
        }

        if ("array".equals(type) && schema.getItems() != null) {
            result.put("items", buildSchemaRecursively(resolveRef(schema.getItems(), componentsSchemas, visitedRefs),
                    componentsSchemas, visitedRefs));
        }

        return result;
    }

    private Schema<?> resolveRef(Schema<?> schema, Map<String, Schema> componentsSchemas, Set<String> visitedRefs) {
        if (schema != null && schema.get$ref() != null) {
            String ref = schema.get$ref();
            if (visitedRefs.contains(ref)) {
                return new Schema<>();
            }
            visitedRefs.add(ref);

            String refName = ref.substring(ref.lastIndexOf('/') + 1);
            Schema<?> resolved = componentsSchemas.get(refName);
            if (resolved != null) {
                return resolved;
            }
        }
        return schema;
    }

    private String mapOpenApiType(String type) {
        if (type == null){
            return "string";
        }
        return switch (type) {
            case "integer", "number", "boolean", "array", "object" -> type;
            default -> "string";
        };
    }


}