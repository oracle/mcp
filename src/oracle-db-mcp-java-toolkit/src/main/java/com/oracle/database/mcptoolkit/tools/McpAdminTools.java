/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.tools;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.database.mcptoolkit.LoadedConstants;
import com.oracle.database.mcptoolkit.OracleDatabaseMCPToolkit;
import com.oracle.database.mcptoolkit.ServerConfig;
import com.oracle.database.mcptoolkit.Utils;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.spec.McpSchema;
import org.yaml.snakeyaml.Yaml;

import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

/**
 * Provides a set of admin/maintenance tools for various operations.
 *
 * <p>The available tools are:</p>
 * <ul>
 *   <li><strong>list-tools</strong>: List all available tools with descriptions.</li>
 *   <li><strong>edit-tools</strong>: Upsert a YAML-defined tool in the config file and rely on runtime reload.</li>
 * </ul>
 */
public class McpAdminTools {

  private McpAdminTools() {}

  /**
   * Returns a list of all MCP admin tool specifications, including "list-tools" and "edit-tools".
   * The returned tools are filtered based on the configuration provided.
   *
   * @param config the server configuration used to filter the tools
   * @return a list of MCP admin tool specifications
   */
  public static List<McpServerFeatures.SyncToolSpecification> getTools(ServerConfig config) {
    List<McpServerFeatures.SyncToolSpecification> tools = new ArrayList<>();

    tools.add(getListToolsTool(config));
    tools.add(getEditToolsTool());

    return tools;
  }

  /**
   * Returns a tool specification for the "list-tools" tool, which lists all available tools
   * with their descriptions. The tool respects the tools filter configuration.
   *
   * <p>The tool returns a list of tools, including:</p>
   * <ul>
   *   <li>Built-in log analyzer tools</li>
   *   <li>RAG tools</li>
   *   <li>Database operator tools</li>
   *   <li>Custom YAML tools</li>
   *   <li>MCP admin tools</li>
   * </ul>
   *
   * <p>The tool's output is filtered based on the {@link ServerConfig#toolsFilter} configuration.</p>
   *
   * @param config the server configuration used to filter the tools
   * @return a tool specification for the "list-tools" tool
   */
  public static McpServerFeatures.SyncToolSpecification getListToolsTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("list-tools")
         .title("List Tools")
         .description("List all available tools with their descriptions.")
         .inputSchema(ToolSchemas.NO_INPUT_SCHEMA)
         .build())
      .callHandler((exchange, callReq) -> {
        try {
          // Always use the latest runtime config to avoid requiring a rebuild
          ServerConfig current = OracleDatabaseMCPToolkit.getConfig() != null ? OracleDatabaseMCPToolkit.getConfig() : config;

          List<Map<String, Object>> tools = new ArrayList<>();

          // 1) Built-in log analyzer tools (respect toolsFilter)
          for (McpServerFeatures.SyncToolSpecification spec : LogAnalyzerTools.getTools()) {
            String name = spec.tool().name();
            if (isEnabled(current, name)) {
              tools.add(Map.of(
                      "name", name,
                      "title", spec.tool().title(),
                      "description", spec.tool().description()
              ));
            }
          }

          // 2) RAG tools (respect toolsFilter)
          for (McpServerFeatures.SyncToolSpecification spec : RagTools.getTools(current)) {
            String name = spec.tool().name();
            if (isEnabled(current, name)) {
              tools.add(Map.of(
                      "name", name,
                      "title", spec.tool().title(),
                      "description", spec.tool().description()
              ));
            }
          }

          // 3) Database operator tools (respect toolsFilter)
          for (McpServerFeatures.SyncToolSpecification spec : DatabaseOperatorTools.getTools(current)) {
            String name = spec.tool().name();
            if (isEnabled(current, name)) {
              tools.add(Map.of(
                      "name", name,
                      "title", spec.tool().title(),
                      "description", spec.tool().description()
              ));
            }
          }

          // 3) Custom YAML tools (always listed if present in config)
          if (current.tools != null) {
            for (Map.Entry<String, com.oracle.database.mcptoolkit.config.ToolConfig> e : current.tools.entrySet()) {
              var tc = e.getValue();
              tools.add(Map.of(
                      "name", tc.name,
                      "title", tc.name,
                      "description", tc.description
              ));
            }
          }

          for (McpServerFeatures.SyncToolSpecification spec : McpAdminTools.getTools(current)) {
            String name = spec.tool().name();
            if (isEnabled(current, name)) {
              tools.add(Map.of(
                      "name", name,
                      "title", spec.tool().title(),
                      "description", spec.tool().description()
              ));
            }
          }

          return McpSchema.CallToolResult.builder()
                  .structuredContent(Map.of("tools", tools))
                  .addTextContent(new ObjectMapper().writeValueAsString(tools))
                  .build();
        } catch (Exception e) {
          return McpSchema.CallToolResult.builder()
                  .addTextContent("Unexpected: " + e.getMessage())
                  .isError(true)
                  .build();
        }
      })
    .build();
  }

  /**
   * Returns a tool specification for the "edit-tools" tool, which creates or updates
   * YAML-defined tools in the configuration file. The changes are auto-reloaded.
   *
   * <p>The tool accepts the following input parameters:</p>
   * <ul>
   *   <li><strong>name</strong>: The name of the tool to create or update (required).</li>
   *   <li><strong>remove</strong>: A boolean flag indicating whether to remove the tool (optional).</li>
   *   <li><strong>description</strong>: A description of the tool (optional).</li>
   *   <li><strong>dataSource</strong>: The data source for the tool (optional).</li>
   *   <li><strong>statement</strong>: The SQL statement for the tool (optional).</li>
   *   <li><strong>parameters</strong>: A list of parameter objects for the tool (optional).
   *     Each parameter object can have the following properties:
   *     <ul>
   *       <li><strong>name</strong>: The name of the parameter.</li>
   *       <li><strong>type</strong>: The data type of the parameter.</li>
   *       <li><strong>description</strong>: A description of the parameter.</li>
   *       <li><strong>required</strong>: A boolean indicating whether the parameter is required.</li>
   *     </ul>
   *   </li>
   * </ul>
   *
   * <p>The tool returns a result with the following properties:</p>
   * <ul>
   *   <li><strong>status</strong>: The status of the operation (e.g., "ok", "noop", "error").</li>
   *   <li><strong>message</strong>: A human-readable message describing the result.</li>
   *   <li><strong>configFile</strong>: The path to the configuration file.</li>
   * </ul>
   *
   * @return a tool specification for the "edit-tools" tool
   */
  public static McpServerFeatures.SyncToolSpecification getEditToolsTool() {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("edit-tools")
         .title("Edit/Add Tools")
         .description("Create or update YAML-defined tools in the config file. Changes are auto-reloaded.")
         .inputSchema(ToolSchemas.EDIT_TOOL_SCHEMA)
         .build())
      .callHandler((exchange, callReq) -> {
        try {
          final var cfgPath = LoadedConstants.CONFIG_FILE;
          if (cfgPath == null || cfgPath.isBlank()) {
            return McpSchema.CallToolResult.builder()
                    .addTextContent("Config file path (configFile) is not set. Cannot edit tools.")
                    .isError(true)
                    .build();
          }

          String name = asString(callReq.arguments().get("name"));
          if (name == null || name.isBlank()) {
            return McpSchema.CallToolResult.builder()
                    .addTextContent("'name' is required")
                    .isError(true)
                    .build();
          }

          Path path = Paths.get(cfgPath);
          Yaml yaml = new Yaml();

          // Load existing YAML into a mutable map
          Map<String, Object> root;
          if (Files.exists(path)) {
            try (Reader r = Files.newBufferedReader(path)) {
              Object loaded = yaml.load(r);
              if (loaded instanceof Map) {
                //noinspection unchecked
                root = new LinkedHashMap<>((Map<String, Object>) loaded);
              } else {
                root = new LinkedHashMap<>();
              }
            }
          } else {
            root = new LinkedHashMap<>();
          }

          // Ensure 'tools' map exists
          Map<String, Object> tools = getOrCreateMap(root, "tools");

          // Remove if requested
          Object removeFlag = callReq.arguments().get("remove");
          boolean remove = (removeFlag instanceof Boolean b && b) ||
                  (removeFlag != null && "true".equalsIgnoreCase(String.valueOf(removeFlag)));
          if (remove) {
            if (tools.remove(name) != null) {
              root.put("tools", tools);
              try (Writer w = Files.newBufferedWriter(path)) {
                yaml.dump(root, w);
              }
              // Try to remove the tool from the running server as well
              try {
                OracleDatabaseMCPToolkit.getServer().removeTool(name);
                Utils.unregisterCustomToolLocally(name);
              } catch (Exception ignored) {}

              return McpSchema.CallToolResult.builder()
                      .structuredContent(Map.of(
                              "status", "ok",
                              "message", "Tool '" + name + "' removed from YAML. Reload will occur shortly.",
                              "configFile", cfgPath
                      ))
                      .addTextContent("{\"status\":\"ok\",\"removed\":\"" + name + "\"}")
                      .build();
            } else {
              return McpSchema.CallToolResult.builder()
                      .structuredContent(Map.of(
                              "status", "noop",
                              "message", "Tool '" + name + "' not found; nothing to remove.",
                              "configFile", cfgPath
                      ))
                      .addTextContent("{\"status\":\"noop\",\"missing\":\"" + name + "\"}")
                      .build();
            }
          }

          // Upsert tool entry
          Map<String, Object> t = getOrCreateMap(tools, name);

          // Optional fields
          putIfPresent(t, callReq.arguments(), "description");
          putIfPresent(t, callReq.arguments(), "dataSource");
          putIfPresent(t, callReq.arguments(), "statement");

          // parameters: array of objects
          Object paramsObj = callReq.arguments().get("parameters");
          if (paramsObj instanceof List<?> list) {
            List<Map<String, Object>> params = new ArrayList<>();
            for (Object o : list) {
              if (o instanceof Map<?, ?> m) {
                Map<String, Object> p = new LinkedHashMap<>();
                copyIfPresent(m, p, "name");
                copyIfPresent(m, p, "type");
                copyIfPresent(m, p, "description");
                copyIfPresent(m, p, "required");
                params.add(p);
              }
            }
            t.put("parameters", params);
          }

          tools.put(name, t);
          root.put("tools", tools);

          // Write back YAML
          try (Writer w = Files.newBufferedWriter(path)) {
            yaml.dump(root, w);
          }

          // Try to remove stale instance at runtime (best-effort hot update); server will re-add on reload
          try {
            var srv = OracleDatabaseMCPToolkit.getServer();
            if (srv != null) srv.removeTool(name);
          } catch (Exception ignored) {}


          // The config poller will pick up the change and hot-reload within ~2 seconds.
          return McpSchema.CallToolResult.builder()
                  .structuredContent(Map.of(
                          "status", "ok",
                          "message", "Tool '" + name + "' upserted into YAML. Reload will occur shortly.",
                          "configFile", cfgPath
                  ))
                  .addTextContent("{\"status\":\"ok\",\"name\":\"" + name + "\"}")
                  .build();
        } catch (Exception e) {

          return McpSchema.CallToolResult.builder()
                  .addTextContent("Unexpected: " + e.getMessage())
                  .isError(true)
                  .build();
        }
      })
    .build();
  }

  private static boolean isEnabled(ServerConfig config, String toolName) {
    if (config.toolsFilter == null) return true;
    String key = toolName.toLowerCase(Locale.ROOT);
    return config.toolsFilter.contains(key);
  }

  private static String asString(Object v) {
    return v == null ? null : String.valueOf(v);
  }

  @SuppressWarnings("unchecked")
  private static Map<String, Object> getOrCreateMap(Map<String, Object> parent, String key) {
    Object o = parent.get(key);
    if (o instanceof Map<?, ?> m) {
      return new LinkedHashMap<>((Map<String, Object>) m);
    }
    Map<String, Object> created = new LinkedHashMap<>();
    parent.put(key, created);
    return created;
  }

  private static void putIfPresent(Map<String, Object> target, Map<String, Object> source, String key) {
    Object v = source.get(key);
    if (v != null) target.put(key, v);
  }

  private static void copyIfPresent(Map<?, ?> src, Map<String, Object> dst, String key) {
    Object v = src.get(key);
    if (v != null) dst.put(key, v);
  }

}
