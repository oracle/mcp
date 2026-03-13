/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.tools;

import com.fasterxml.jackson.databind.json.JsonMapper;
import com.oracle.database.mcptoolkit.ServerConfig;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.spec.McpSchema;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static com.oracle.database.mcptoolkit.Utils.openConnection;
import static com.oracle.database.mcptoolkit.Utils.getOrDefault;
import static com.oracle.database.mcptoolkit.Utils.tryCall;

/**
 * Provides the {@code oci-storage} tool for browsing OCI Object Storage buckets
 * and listing database credentials.
 * <p>
 * All authentication is handled by the Oracle database via {@code DBMS_CLOUD} credentials —
 * no separate OCI configuration is needed. Create a credential once with
 * {@code EXEC DBMS_CLOUD.CREATE_CREDENTIAL(credential_name, ...)} and pass its name to any tool
 * that accesses private buckets. For public buckets, the credential can be omitted.
 */
public class ObjectStorageRagTools {

  private ObjectStorageRagTools() {}

  /**
   * Returns the OCI storage utility tool specifications.
   *
   * @param config server configuration
   * @return list containing the {@code oci-storage} tool
   */
  public static List<McpServerFeatures.SyncToolSpecification> getTools(ServerConfig config) {
    List<McpServerFeatures.SyncToolSpecification> tools = new ArrayList<>();
    tools.add(getOciStorageTool(config));
    return tools;
  }

  /**
   * Returns a tool specification for {@code oci-storage}.
   * <p>
   * action=list-objects — lists all objects in an OCI bucket. Accepts a direct {@code bucketUrl}
   * (including PAR URLs) or individual {@code region}, {@code namespace}, and {@code bucketName}.<br>
   * action=list-credentials — lists all {@code DBMS_CLOUD} credentials in the schema.
   *
   * @param config server configuration
   * @return tool specification
   */
  public static McpServerFeatures.SyncToolSpecification getOciStorageTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("oci-storage")
         .title("OCI Storage")
         .description("OCI Object Storage utilities. "
                 + "action=list-objects (lists bucket contents; provide bucketUrl, or region+namespace+bucketName). "
                 + "action=list-credentials (lists all DBMS_CLOUD credentials in the schema).")
         .inputSchema(ToolSchemas.OCI_STORAGE)
         .build())
      .callHandler((exchange, callReq) -> {
        String action = String.valueOf(callReq.arguments().getOrDefault("action", ""));
        return switch (action) {

          case "list-objects" -> tryCall(() -> {
            Map<String, Object> args = callReq.arguments();
            String credentialName = nullableCredential(args.get("credentialName"));
            String prefix         = getOrDefault(args.get("prefix"), "");

            // bucketUrl (direct or PAR) takes priority over individual components
            String rawBucketUrl = getOrDefault(args.get("bucketUrl"), null);
            String bucketUri = (rawBucketUrl != null) ? rawBucketUrl : buildBucketUri(
                    String.valueOf(args.get("region")),
                    String.valueOf(args.get("namespace")),
                    String.valueOf(args.get("bucketName")));

            List<Map<String, Object>> objects = new ArrayList<>();
            try (Connection c = openConnection(config, null);
                 PreparedStatement ps = c.prepareStatement(SqlQueries.LIST_OCI_BUCKET_OBJECTS_QUERY)) {

              ps.setString(1, credentialName);   // null = public bucket
              ps.setString(2, bucketUri);
              ps.setString(3, prefix);

              try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                  Map<String, Object> obj = new LinkedHashMap<>();
                  obj.put("name",         rs.getString("object_name"));
                  obj.put("sizeBytes",    rs.getLong("bytes"));
                  obj.put("lastModified", rs.getString("last_modified"));
                  objects.add(obj);
                }
              }
            }

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("bucketUri",    bucketUri);
            result.put("totalObjects", objects.size());
            result.put("objects",      objects);
            return McpSchema.CallToolResult.builder()
                    .structuredContent(result)
                    .addTextContent(new JsonMapper().writeValueAsString(result))
                    .build();
          });

          case "list-credentials" -> tryCall(() -> {
            List<Map<String, Object>> credentials = new ArrayList<>();
            try (Connection c = openConnection(config, null);
                 PreparedStatement ps = c.prepareStatement(SqlQueries.LIST_CREDENTIALS_QUERY);
                 ResultSet rs = ps.executeQuery()) {
              while (rs.next()) {
                Map<String, Object> row = new LinkedHashMap<>();
                row.put("credentialName", rs.getString("credential_name"));
                row.put("username",       rs.getString("username"));
                row.put("enabled",        rs.getString("enabled"));
                credentials.add(row);
              }
            }

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("totalCredentials", credentials.size());
            result.put("credentials",      credentials);
            return McpSchema.CallToolResult.builder()
                    .structuredContent(result)
                    .addTextContent(new JsonMapper().writeValueAsString(result))
                    .build();
          });

          default -> new McpSchema.CallToolResult(
                  "Unknown action '" + action + "'. Must be one of: list-objects, list-credentials", true);
        };
      })
    .build();
  }

  /**
   * Returns the credential name, or {@code null} if not provided (public bucket access).
   * Using {@code String.valueOf(null)} would produce the literal string {@code "null"},
   * so we explicitly check here.
   *
   * @param value raw argument value from the MCP request
   * @return the credential name string, or {@code null} for public access
   */
  static String nullableCredential(Object value) {
    if (value == null) return null;
    String s = value.toString().trim();
    return s.isEmpty() ? null : s;
  }

  /**
   * Builds the full OCI Object Storage URI for a single object.
   * Format: {@code https://objectstorage.{region}.oraclecloud.com/n/{namespace}/b/{bucket}/o/{objectName}}
   *
   * @param region     OCI region identifier (e.g. {@code us-ashburn-1})
   * @param namespace  OCI Object Storage namespace
   * @param bucketName bucket name
   * @param objectName object path within the bucket
   * @return the fully qualified object URI
   */
  static String buildObjectUri(String region, String namespace, String bucketName, String objectName) {
    return "https://objectstorage." + region + ".oraclecloud.com"
            + "/n/" + namespace
            + "/b/" + bucketName
            + "/o/" + objectName;
  }

  /**
   * Builds the OCI Object Storage bucket base URI used for listing and embedding objects.
   * Format: {@code https://objectstorage.{region}.oraclecloud.com/n/{namespace}/b/{bucket}/o/}
   *
   * @param region     OCI region identifier (e.g. {@code us-ashburn-1})
   * @param namespace  OCI Object Storage namespace
   * @param bucketName bucket name
   * @return the bucket base URI (always ends with {@code /o/})
   */
  static String buildBucketUri(String region, String namespace, String bucketName) {
    return "https://objectstorage." + region + ".oraclecloud.com"
            + "/n/" + namespace
            + "/b/" + bucketName
            + "/o/";
  }

}