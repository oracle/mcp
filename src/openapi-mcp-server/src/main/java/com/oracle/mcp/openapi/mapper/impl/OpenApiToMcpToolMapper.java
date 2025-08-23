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
        String toolDescription = getDescription(toolName, method.name(), path, operation);

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

    // Modified helper method to populate all relevant collections
    private void extractPathAndQueryParams(Operation operation,
                                           Map<String, Map<String, Object>> pathParams,
                                           Map<String, Map<String, Object>> queryParams,
                                           Map<String, Object> properties,
                                           List<String> requiredParams) {
        if (operation.getParameters() != null) {
            for (Parameter param : operation.getParameters()) {
                if (param.getName() == null || param.getSchema() == null) continue;

                // This part is for your meta block (original behavior)
                Map<String, Object> paramMeta = parameterMetaMap(param);
                if ("path".equalsIgnoreCase(param.getIn())) {
                    pathParams.put(param.getName(), paramMeta);
                } else if ("query".equalsIgnoreCase(param.getIn())) {
                    queryParams.put(param.getName(), paramMeta);
                }

                // This part is for your inputSchema
                if ("path".equalsIgnoreCase(param.getIn()) || "query".equalsIgnoreCase(param.getIn())) {

                    // --- MODIFICATION START ---

                    // 1. Get the base schema for the parameter
                    Map<String, Object> paramSchema = extractInputSchema(param.getSchema());

                    // 2. Manually add the description from the Parameter object itself
                    if (param.getDescription() != null && !param.getDescription().isEmpty()) {
                        paramSchema.put("description", param.getDescription());
                    }

                    // 3. Add the complete schema (with description) to the properties map
                    properties.put(param.getName(), paramSchema);

                    // --- MODIFICATION END ---


                    // If required, add it to the list of required parameters
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

    public String getDescription(String toolName, String httpMethod, String path, Operation operation) {
        StringBuilder doc = new StringBuilder();

        if (operation.getSummary() != null && !operation.getSummary().isEmpty()) {
            doc.append(operation.getSummary()).append("\n");
        } else if (operation.getDescription() != null && !operation.getDescription().isEmpty()) {
            doc.append(operation.getDescription()).append("\n");
        }
//
//        doc.append("HTTP Method : ").append(httpMethod.toUpperCase()).append("\n");
//        doc.append("End URL : ").append(" `").append(path).append("`\n");
//
//        if (operation.getParameters() != null && !operation.getParameters().isEmpty()) {
//            appendParameterList(doc, "Path parameters: ", operation.getParameters(), "path");
//            appendParameterList(doc, "Query parameters: ", operation.getParameters(), "query");
//        }
//
//        if (operation.getRequestBody() != null) {
//            doc.append("Request body: ")
//                    .append(Boolean.TRUE.equals(operation.getRequestBody().getRequired()) ? "Required" : "Optional")
//                    .append("\n");
//        }
//
//        appendExampleUsage(doc, toolName);
        return doc.toString();
    }

    private void appendParameterList(StringBuilder doc, String label, List<Parameter> parameters, String type) {
        doc.append(label);
        for (Parameter p : parameters) {
            if (type.equals(p.getIn())) {
                doc.append(p.getName())
                        .append(Boolean.TRUE.equals(p.getRequired()) ? "*" : "")
                        .append(",");
            }
        }
        doc.append("\n");
    }

    private void appendExampleUsage(StringBuilder doc, String toolName) {
        doc.append("Example usage: ");
        doc.append("```json\n");
        doc.append("{\n");
        doc.append("  \"tool_name\": \"").append(toolName).append("\",\n");
        doc.append("  \"arguments\": {}\n");
        doc.append("}\n");
        doc.append("```\n");
    }

    private OpenAPI parseOpenApi(JsonNode jsonNode) {
        String jsonString = jsonNode.toString();
        ParseOptions options = new ParseOptions();
        options.setResolve(true);
        options.setResolveFully(true);
        return new OpenAPIV3Parser().readContents(jsonString, null, options).getOpenAPI();
    }

    public McpSchema.JsonSchema buildInputSchemaFromOperation(Operation operation) {
        Map<String, Object> properties = new LinkedHashMap<>();
        List<String> requiredParams = new ArrayList<>();

        extractRequestBody(operation, properties, requiredParams);

        // This now assumes McpSchema.JsonSchema is defined elsewhere in your project
        return new McpSchema.JsonSchema(
                "object",
                properties.isEmpty() ? null : properties,
                requiredParams.isEmpty() ? null : requiredParams,
                false, null, null
        );
    }

    private void extractRequestBody(Operation operation, Map<String, Object> properties, List<String> requiredParams) {
        // Extract from request body
        if (operation.getRequestBody() != null && operation.getRequestBody().getContent() != null) {
            // Assuming a single JSON media type for simplicity
            MediaType media = operation.getRequestBody().getContent().get("application/json");
            if (media != null && media.getSchema() != null) {
                Schema<?> bodySchema = media.getSchema();

                if ("object".equals(bodySchema.getType()) && bodySchema.getProperties() != null) {
                    bodySchema.getProperties().forEach((name, schema) -> {
                        properties.put(name.toString(), extractInputSchema((Schema<?>) schema));
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

        // Copy basic properties
        if (openApiSchema.getType() != null) jsonSchema.put("type", openApiSchema.getType());
        if (openApiSchema.getDescription() != null) {
            jsonSchema.put("description", openApiSchema.getDescription());
        }
        if (openApiSchema.getFormat() != null) jsonSchema.put("format", openApiSchema.getFormat());
        if (openApiSchema.getEnum() != null) jsonSchema.put("enum", openApiSchema.getEnum());

        // --- Recursive Handling ---

        // If it's an object, process its properties recursively
        if ("object".equals(openApiSchema.getType())) {
            if (openApiSchema.getProperties() != null) {
                Map<String, Object> nestedProperties = new LinkedHashMap<>();
                openApiSchema.getProperties().forEach((key, value) -> {
                    nestedProperties.put(key.toString(), extractInputSchema((Schema<?>) value));
                });
                jsonSchema.put("properties", nestedProperties);
            }
            if (openApiSchema.getRequired() != null) {
                jsonSchema.put("required", openApiSchema.getRequired());
            }
        }

        // If it's an array, process its 'items' schema recursively
        if ("array".equals(openApiSchema.getType())) {
            if (openApiSchema.getItems() != null) {
                jsonSchema.put("items", extractInputSchema(openApiSchema.getItems()));
            }
        }

        return jsonSchema;
    }


    public Map<String, Object> extractOutputSchema(Operation operation) {
        if (operation.getResponses() == null || operation.getResponses().isEmpty()) {
            return new HashMap<>();
        }

        ApiResponse response = operation.getResponses().get("200");
        if (response == null) {
            response = operation.getResponses().get("default");
        }
        if (response == null || response.getContent() == null || !response.getContent().containsKey("application/json")) {
            return new HashMap<>();
        }

        Schema<?> schema = response.getContent().get("application/json").getSchema();
        if (schema == null) {
            return new HashMap<>();
        }
        return extractOutputSchema(schema);
    }

    public Map<String, Object> extractOutputSchema(Schema<?> schema) {
        if (schema == null) {
            return Collections.emptyMap();
        }

        Map<String, Object> jsonSchema = new LinkedHashMap<>();

        // Copy basic properties
        if (schema.getType() != null) {
            jsonSchema.put("type", new String[]{schema.getType(), "null"});
        }
        if (schema.getDescription() != null) {
            jsonSchema.put("description", schema.getDescription());
        }

        // If it's an object, recursively process its properties
        if ("object".equals(schema.getType()) && schema.getProperties() != null) {
            Map<String, Object> properties = new LinkedHashMap<>();
            for (Map.Entry<String, Schema> entry : schema.getProperties().entrySet()) {
                properties.put(entry.getKey(), extractOutputSchema(entry.getValue()));
            }
            jsonSchema.put("properties", properties);
        }

        // Add other properties you may need, like "required", "items" for arrays, etc.
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
