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
import com.oracle.mcp.openapi.mapper.McpToolMapper;
import com.oracle.mcp.openapi.util.McpServerUtil;
import io.modelcontextprotocol.spec.McpSchema;
import io.swagger.models.ArrayModel;
import io.swagger.models.HttpMethod;
import io.swagger.models.Model;
import io.swagger.models.ModelImpl;
import io.swagger.models.Operation;
import io.swagger.models.Path;
import io.swagger.models.RefModel;
import io.swagger.models.Swagger;
import io.swagger.models.parameters.BodyParameter;
import io.swagger.models.parameters.Parameter;
import io.swagger.models.parameters.QueryParameter;
import io.swagger.models.parameters.PathParameter;
import io.swagger.models.properties.Property;
import io.swagger.models.properties.RefProperty;
import io.swagger.models.properties.ArrayProperty;
import io.swagger.models.properties.ObjectProperty;
import io.swagger.parser.SwaggerParser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;


/**
 * Implementation of {@link McpToolMapper} that converts Swagger 2.0 specifications
 * into MCP-compliant tool definitions.
 * <p>
 * This mapper reads a Swagger JSON/YAML specification, extracts paths, operations,
 * parameters, and models, and builds a list of {@link McpSchema.Tool} objects.
 * <p>
 * The generated tools are also cached via {@link McpServerCacheService} for reuse.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public class SwaggerToMcpToolMapper implements McpToolMapper {

    private final McpServerCacheService mcpServerCacheService;
    private static final Logger LOGGER = LoggerFactory.getLogger(SwaggerToMcpToolMapper.class);
    private Swagger swaggerSpec; // Stores the full spec to resolve $ref definitions

    /**
     * Creates a new {@code SwaggerToMcpToolMapper}.
     *
     * @param mcpServerCacheService cache service used to store generated MCP tools.
     */
    public SwaggerToMcpToolMapper(McpServerCacheService mcpServerCacheService) {
        this.mcpServerCacheService = mcpServerCacheService;
    }

    /**
     * Converts a Swagger 2.0 specification (as a Jackson {@link JsonNode})
     * into a list of MCP tools.
     *
     * @param swaggerJson the Swagger specification in JSON tree form.
     * @return a list of {@link McpSchema.Tool} objects.
     * @throws IllegalArgumentException if the specification does not contain a {@code paths} object.
     */
    @Override
    public List<McpSchema.Tool> convert(JsonNode swaggerJson) {
        LOGGER.debug("Parsing Swagger 2 JsonNode to Swagger object...");
        this.swaggerSpec = parseSwagger(swaggerJson);

        if (swaggerSpec.getPaths() == null || swaggerSpec.getPaths().isEmpty()) {
            throw new IllegalArgumentException("'paths' object not found in the specification.");
        }

        List<McpSchema.Tool> mcpTools = processPaths(swaggerSpec);
        LOGGER.debug("Conversion complete. Total tools created: {}", mcpTools.size());
        updateToolsToCache(mcpTools);
        return mcpTools;
    }

    /**
     * Processes all paths in the Swagger specification and builds corresponding MCP tools.
     *
     * @param swagger the parsed Swagger object.
     * @return list of {@link McpSchema.Tool}.
     */
    private List<McpSchema.Tool> processPaths(Swagger swagger) {
        List<McpSchema.Tool> mcpTools = new ArrayList<>();
        Set<String> toolNames = new HashSet<>();
        if (swagger.getPaths() == null) return mcpTools;

        for (Map.Entry<String, Path> pathEntry : swagger.getPaths().entrySet()) {
            String path = pathEntry.getKey();
            Path pathItem = pathEntry.getValue();
            if (pathItem == null){
                continue;
            }

            processOperationsForPath(path, pathItem, mcpTools,toolNames);
        }
        return mcpTools;
    }

    /**
     * Extracts operations (GET, POST, etc.) for a given Swagger path and converts them to MCP tools.
     *
     * @param path     the API path (e.g., {@code /users}).
     * @param pathItem the Swagger path item containing operations.
     * @param mcpTools the list to which new tools will be added.
     */
    private void processOperationsForPath(String path, Path pathItem, List<McpSchema.Tool> mcpTools,Set<String> toolNames) {
        Map<HttpMethod, Operation> operations = pathItem.getOperationMap();
        if (operations == null){
            return;
        }

        for (Map.Entry<HttpMethod, Operation> methodEntry : operations.entrySet()) {
            McpSchema.Tool tool = buildToolFromOperation(path, methodEntry.getKey(), methodEntry.getValue(),toolNames);
            if (tool != null) {
                mcpTools.add(tool);
            }
        }
    }

    /**
     * Builds an MCP tool definition from a Swagger operation.
     *
     * @param path      the API path.
     * @param method    the HTTP method.
     * @param operation the Swagger operation metadata.
     * @return a constructed {@link McpSchema.Tool}, or {@code null} if the operation is invalid.
     */
    private McpSchema.Tool buildToolFromOperation(String path, HttpMethod method, Operation operation,Set<String> toolNames) {
        String rawOperationId = (operation.getOperationId() != null && !operation.getOperationId().isEmpty())
                ? operation.getOperationId()
                : McpServerUtil.toCamelCase(method.name() + " " + path);

        String toolName = makeUniqueName(toolNames,rawOperationId);
        LOGGER.debug("--- Parsing Operation: {} {} (ID: {}) ---", method.name(), path, toolName);

        String toolTitle = operation.getSummary() != null ? operation.getSummary() : toolName;
        String toolDescription = operation.getDescription() != null ? operation.getDescription() : toolTitle;

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

    /**
     * Extracts path and query parameters from a Swagger operation and adds them to the input schema.
     */
    private void extractPathAndQueryParams(Operation operation,
                                           Map<String, Map<String, Object>> pathParams,
                                           Map<String, Map<String, Object>> queryParams,
                                           Map<String, Object> properties,
                                           List<String> requiredParams) {
        if (operation.getParameters() == null){
            return;
        }

        for (Parameter param : operation.getParameters()) {
            if (param instanceof PathParameter || param instanceof QueryParameter) {
                Map<String, Object> paramSchema = new LinkedHashMap<>();
                paramSchema.put(CommonConstant.DESCRIPTION, param.getDescription());

                if (param instanceof PathParameter) {
                    paramSchema.put(CommonConstant.TYPE, ((PathParameter) param).getType());
                    pathParams.put(param.getName(), Map.of(CommonConstant.NAME, param.getName(), CommonConstant.REQUIRED, param.getRequired()));
                } else {
                    paramSchema.put(CommonConstant.TYPE, ((QueryParameter) param).getType());
                    queryParams.put(param.getName(), Map.of(CommonConstant.NAME, param.getName(), CommonConstant.REQUIRED, param.getRequired()));
                }

                properties.put(param.getName(), paramSchema);
                if (param.getRequired()) {
                    requiredParams.add(param.getName());
                }
            }
        }
    }

    /**
     * Extracts request body schema (if present) from a Swagger operation.
     */
    private void extractRequestBody(Operation operation, Map<String, Object> properties, List<String> requiredParams) {
        if (operation.getParameters() == null){
            return;
        }

        operation.getParameters().stream()
                .filter(p -> p instanceof BodyParameter)
                .findFirst()
                .ifPresent(p -> {
                    BodyParameter bodyParam = (BodyParameter) p;
                    Model schema = bodyParam.getSchema();
                    Map<String, Object> bodyProps = extractModelSchema(schema);

                    if (!bodyProps.isEmpty()) {
                        properties.put(bodyParam.getName(), bodyProps);
                        if (bodyParam.getRequired()) {
                            requiredParams.add(bodyParam.getName());
                        }
                    }
                });
    }

    /**
     * Recursively extracts schema details from a Swagger model definition.
     */
    private Map<String, Object> extractModelSchema(Model model) {
        if (model instanceof RefModel) {
            String ref = ((RefModel) model).getSimpleRef();
            model = swaggerSpec.getDefinitions().get(ref);
        }

        Map<String, Object> schema = new LinkedHashMap<>();
        if (model instanceof ModelImpl && model.getProperties() != null) {
            Map<String, Object> props = new LinkedHashMap<>();
             model.getProperties().forEach((key, prop) ->
                props.put(key, extractPropertySchema(prop))
            );
            schema.put(CommonConstant.TYPE, CommonConstant.OBJECT);
            schema.put(CommonConstant.PROPERTIES, props);
            if (((ModelImpl) model).getRequired() != null) {
                schema.put(CommonConstant.REQUIRED, ((ModelImpl) model).getRequired());
            }
        } else if (model instanceof ArrayModel) {
            schema.put(CommonConstant.TYPE, CommonConstant.ARRAY);
            schema.put(CommonConstant.ITEMS, extractPropertySchema(((ArrayModel) model).getItems()));
        }
        return schema;
    }

    /**
     * Extracts schema information from a Swagger property.
     */
    private Map<String, Object> extractPropertySchema(Property property) {
        if (property instanceof RefProperty) {
            String simpleRef = ((RefProperty) property).getSimpleRef();
            Model definition = swaggerSpec.getDefinitions().get(simpleRef);
            if (definition != null) {
                return extractModelSchema(definition);
            } else {
                return Map.of("type", CommonConstant.OBJECT, CommonConstant.DESCRIPTION, "Unresolved reference: " + simpleRef);
            }
        }

        Map<String, Object> schema = new LinkedHashMap<>();
        schema.put(CommonConstant.TYPE, property.getType());
        schema.put(CommonConstant.DESCRIPTION, property.getDescription());

        if (property instanceof ObjectProperty) {
            Map<String, Object> props = new LinkedHashMap<>();
            ((ObjectProperty) property).getProperties().forEach((key, prop) ->
                props.put(key, extractPropertySchema(prop))
            );
            schema.put(CommonConstant.PROPERTIES, props);
        } else if (property instanceof ArrayProperty) {
            schema.put(CommonConstant.ITEMS, extractPropertySchema(((ArrayProperty) property).getItems()));
        }
        return schema;
    }

    /**
     * Builds metadata for an MCP tool, including HTTP method, path, tags, security, and parameter maps.
     */
    private Map<String, Object> buildMeta(HttpMethod method, String path, Operation operation,
                                          Map<String, Map<String, Object>> pathParams, Map<String, Map<String, Object>> queryParams) {
        Map<String, Object> meta = new LinkedHashMap<>();
        meta.put(CommonConstant.HTTP_METHOD, method.name());
        meta.put(CommonConstant.PATH, path);
        if (operation.getTags() != null) meta.put(CommonConstant.TAGS, operation.getTags());
        if (operation.getSecurity() != null) meta.put(CommonConstant.SECURITY, operation.getSecurity());
        if (!pathParams.isEmpty()) meta.put(CommonConstant.PATH_PARAMS, pathParams);
        if (!queryParams.isEmpty()) meta.put(CommonConstant.QUERY_PARAMS, queryParams);
        return meta;
    }

    /**
     * Stores the generated tools into the cache service.
     */
    private void updateToolsToCache(List<McpSchema.Tool> tools) {
        for (McpSchema.Tool tool : tools) {
            mcpServerCacheService.putTool(tool.name(), tool);
        }
    }

    /**
     * Parses the Swagger JSON into a {@link Swagger} object.
     */
    private Swagger parseSwagger(JsonNode jsonNode) {
        return new SwaggerParser().parse(jsonNode.toString());
    }

    /**
     * Ensures a unique tool name by appending a numeric suffix if necessary.
     */
    private String makeUniqueName(Set<String> toolNAMES,String base) {

        String name = base;
        int counter = 1;
        while (toolNAMES.contains(name)) {
            name = base + CommonConstant.UNDER_SCORE + counter++;
        }
        toolNAMES.add(name);
        return name;
    }


}
