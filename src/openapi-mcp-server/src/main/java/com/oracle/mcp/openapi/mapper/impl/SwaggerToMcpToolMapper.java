package com.oracle.mcp.openapi.mapper.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.mapper.McpToolMapper;
import io.modelcontextprotocol.spec.McpSchema;
import io.swagger.models.*;
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

import java.util.*;

public class SwaggerToMcpToolMapper implements McpToolMapper {

    private final Set<String> usedNames = new HashSet<>();
    private final McpServerCacheService mcpServerCacheService;
    private static final Logger LOGGER = LoggerFactory.getLogger(SwaggerToMcpToolMapper.class);

    public SwaggerToMcpToolMapper(McpServerCacheService mcpServerCacheService) {
        this.mcpServerCacheService = mcpServerCacheService;
    }

    @Override
    public List<McpSchema.Tool> convert(JsonNode swaggerJson) {
        LOGGER.debug("Parsing Swagger 2 JsonNode to Swagger object...");
        Swagger swagger = parseSwagger(swaggerJson);

        if (swagger.getPaths() == null || swagger.getPaths().isEmpty()) {
            throw new IllegalArgumentException("'paths' object not found in the specification.");
        }

        List<McpSchema.Tool> mcpTools = processPaths(swagger);
        LOGGER.debug("Conversion complete. Total tools created: {}", mcpTools.size());
        updateToolsToCache(mcpTools);
        return mcpTools;
    }

    private List<McpSchema.Tool> processPaths(Swagger swagger) {
        List<McpSchema.Tool> mcpTools = new ArrayList<>();

        for (Map.Entry<String, Path> pathEntry : swagger.getPaths().entrySet()) {
            String path = pathEntry.getKey();
            Path pathItem = pathEntry.getValue();
            if (pathItem == null) continue;

            processOperationsForPath(path, pathItem, mcpTools);
        }
        return mcpTools;
    }

    private void processOperationsForPath(String path, Path pathItem, List<McpSchema.Tool> mcpTools) {
        Map<HttpMethod, Operation> operations = pathItem.getOperationMap();
        if (operations == null) return;

        for (Map.Entry<HttpMethod, Operation> methodEntry : operations.entrySet()) {
            HttpMethod method = methodEntry.getKey();
            Operation operation = methodEntry.getValue();
            if (operation == null) continue;

            McpSchema.Tool tool = buildToolFromOperation(path, method, operation);
            if (tool != null) {
                mcpTools.add(tool);
            }
        }
    }

    private McpSchema.Tool buildToolFromOperation(String path, HttpMethod method, Operation operation) {
        String rawOperationId = (operation.getOperationId() != null && !operation.getOperationId().isEmpty())
                ? operation.getOperationId()
                : toCamelCase(method.name() + " " + path);

        String toolName = makeUniqueName(rawOperationId);
        LOGGER.debug("--- Parsing Operation: {} {} (ID: {}) ---", method.name(), path, toolName);

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

    private Map<String, Object> buildMeta(HttpMethod method, String path,
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
                if (param.getName() == null) continue;

                Map<String, Object> paramMeta = new LinkedHashMap<>();
                paramMeta.put("name", param.getName());
                paramMeta.put("required", param.getRequired());
                if (param.getDescription() != null) {
                    paramMeta.put("description", param.getDescription());
                }

                if (param instanceof PathParameter) {
                    pathParams.put(param.getName(), paramMeta);
                } else if (param instanceof QueryParameter) {
                    queryParams.put(param.getName(), paramMeta);
                }

                Map<String, Object> paramSchema = new LinkedHashMap<>();
                if (param.getDescription() != null) {
                    paramSchema.put("description", param.getDescription());
                }
                paramSchema.put("type", "string"); // fallback for Swagger 2 simple params
                properties.put(param.getName(), paramSchema);

                if (param.getRequired()) {
                    requiredParams.add(param.getName());
                }
            }
        }
    }

    private void extractRequestBody(Operation operation, Map<String, Object> properties, List<String> requiredParams) {
        if (operation.getParameters() != null) {
            for (Parameter param : operation.getParameters()) {
                if (param instanceof BodyParameter) {
                    Model schema = ((BodyParameter) param).getSchema();
                    if (schema instanceof ModelImpl) {
                        ModelImpl impl = (ModelImpl) schema;
                        if (impl.getProperties() != null) {
                            for (Map.Entry<String, Property> entry : impl.getProperties().entrySet()) {
                                properties.put(entry.getKey(), extractPropertySchema(entry.getValue()));
                            }
                        }
                        if (impl.getRequired() != null) {
                            requiredParams.addAll(impl.getRequired());
                        }
                    }
                }
            }
        }
    }

    private Map<String, Object> extractPropertySchema(Property property) {
        Map<String, Object> schema = new LinkedHashMap<>();
        if (property.getType() != null) schema.put("type", property.getType());
        if (property.getDescription() != null) schema.put("description", property.getDescription());

        if (property instanceof ObjectProperty) {
            Map<String, Object> nestedProps = new LinkedHashMap<>();
            ObjectProperty objProp = (ObjectProperty) property;
            if (objProp.getProperties() != null) {
                for (Map.Entry<String, Property> entry : objProp.getProperties().entrySet()) {
                    nestedProps.put(entry.getKey(), extractPropertySchema(entry.getValue()));
                }
            }
            schema.put("properties", nestedProps);
        }

        if (property instanceof ArrayProperty) {
            ArrayProperty arrProp = (ArrayProperty) property;
            schema.put("type", "array");
            schema.put("items", extractPropertySchema(arrProp.getItems()));
        }

        if (property instanceof RefProperty) {
            schema.put("$ref", ((RefProperty) property).get$ref());
        }

        return schema;
    }

    public Map<String, Object> extractOutputSchema(Operation operation) {
        if (operation.getResponses() == null || operation.getResponses().isEmpty()) {
            return new HashMap<>();
        }

        Response response = operation.getResponses().get("200");
        if (response == null) {
            response = operation.getResponses().get("default");
        }
        if (response == null || response.getSchema() == null) {
            return new HashMap<>();
        }

        return extractPropertySchema(response.getSchema());
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
        return doc.toString();
    }

    private Swagger parseSwagger(JsonNode jsonNode) {
        String jsonString = jsonNode.toString();
        return new SwaggerParser().parse(jsonString);
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
