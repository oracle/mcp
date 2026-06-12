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

import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Pattern;

import static com.oracle.database.mcptoolkit.Utils.openConnection;
import static com.oracle.database.mcptoolkit.Utils.getOrDefault;
import static com.oracle.database.mcptoolkit.Utils.tryCall;

/**
 * Provides the {@code oci-storage} tool for browsing OCI Object Storage buckets
 * used by RAG workflows.
 * <p>
 * All authentication is handled by the Oracle database via {@code DBMS_CLOUD} credentials —
 * no separate OCI configuration is needed. Create a credential once with
 * {@code EXEC DBMS_CLOUD.CREATE_CREDENTIAL(credential_name, ...)} and pass its name to any tool
 * that accesses private buckets. For public buckets, the credential can be omitted.
 */
public class ObjectStorageRagTools {

  private static final int DEFAULT_LIST_OBJECTS_RESULTS = 100;
  private static final int MAX_LIST_OBJECTS_RESULTS = 10000;
  private static final Pattern OCI_REGION = Pattern.compile("[a-z]+-[a-z]+-[0-9]+");
  private static final Pattern OBJECT_STORAGE_HOST =
          Pattern.compile("objectstorage\\.[a-z]+-[a-z]+-[0-9]+\\.oraclecloud\\.com");

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
   * action=list-objects — lists objects in an OCI bucket. Accepts a direct {@code bucketUrl}
   * (including PAR URLs) or individual {@code region}, {@code namespace}, and {@code bucketName}.<br>
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
                 + "action=list-objects (lists bucket contents; provide bucketUrl, or region+namespace+bucketName).")
         .inputSchema(ToolSchemas.OCI_STORAGE)
         .build())
      .callHandler((exchange, callReq) -> {
        String action = String.valueOf(callReq.arguments().getOrDefault("action", ""));
        return switch (action) {

          case "list-objects" -> tryCall(() -> {
            Map<String, Object> args = callReq.arguments();
            String credentialName = nullableCredential(args.get("credentialName"));
            String prefix         = getOrDefault(args.get("prefix"), "");
            int maxResults        = parseListObjectsMaxResults(args.get("maxResults"));

            // bucketUrl (direct or PAR) takes priority over individual components
            String rawBucketUrl = getOrDefault(args.get("bucketUrl"), null);
            String bucketUri = (rawBucketUrl != null) ? validateObjectStorageUrl(rawBucketUrl) : buildBucketUri(
                    getOrDefault(args.get("region"), null),
                    getOrDefault(args.get("namespace"), null),
                    getOrDefault(args.get("bucketName"), null));

            List<Map<String, Object>> objects = new ArrayList<>();
            boolean truncated = false;
            try (Connection c = openConnection(config, null);
                 PreparedStatement ps = c.prepareStatement(SqlQueries.LIST_OCI_BUCKET_OBJECTS_QUERY)) {

              ps.setString(1, credentialName);   // null = public bucket
              ps.setString(2, bucketUri);
              ps.setString(3, prefix);

              try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                  if (objects.size() >= maxResults) {
                    truncated = true;
                    break;
                  }
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
            result.put("prefix",       prefix);
            result.put("maxResults",   maxResults);
            result.put("truncated",    truncated);
            result.put("totalObjects", objects.size());
            result.put("objects",      objects);
            return McpSchema.CallToolResult.builder()
                    .structuredContent(result)
                    .addTextContent(new JsonMapper().writeValueAsString(result))
                    .build();
          });

          default -> new McpSchema.CallToolResult(
                  "Unknown action '" + action + "'. Must be: list-objects", true);
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
    String safeRegion = validateRegion(region);
    requireNonBlank(namespace, "namespace");
    requireNonBlank(bucketName, "bucketName");
    requireNonBlank(objectName, "objectName");

    return "https://objectstorage." + safeRegion + ".oraclecloud.com"
            + "/n/" + encodePathSegment(namespace)
            + "/b/" + encodePathSegment(bucketName)
            + "/o/" + encodeObjectName(objectName);
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
    String safeRegion = validateRegion(region);
    requireNonBlank(namespace, "namespace");
    requireNonBlank(bucketName, "bucketName");

    return "https://objectstorage." + safeRegion + ".oraclecloud.com"
            + "/n/" + encodePathSegment(namespace)
            + "/b/" + encodePathSegment(bucketName)
            + "/o/";
  }

  /**
   * Validates a direct Object Storage or PAR URL before sending it to DBMS_CLOUD.
   */
  static String validateObjectStorageUrl(String url) {
    String value = requireNonBlank(url, "objectUrl");
    URI uri;
    try {
      uri = URI.create(value);
    } catch (IllegalArgumentException e) {
      throw new IllegalArgumentException("Invalid OCI Object Storage URL", e);
    }

    String scheme = uri.getScheme();
    String host = uri.getHost();
    if (!"https".equalsIgnoreCase(scheme)) {
      throw new IllegalArgumentException("OCI Object Storage URL must use https");
    }
    if (host == null || !OBJECT_STORAGE_HOST.matcher(host.toLowerCase(Locale.ROOT)).matches()) {
      throw new IllegalArgumentException("OCI Object Storage URL host is not allowed");
    }
    return value;
  }

  /**
   * Parses the requested list limit, defaulting to 100 and capping at 10000.
   */
  public static int parseListObjectsMaxResults(Object value) {
    String s = getOrDefault(value, String.valueOf(DEFAULT_LIST_OBJECTS_RESULTS));

    int requested;
    try {
      requested = Integer.parseInt(s);
    } catch (NumberFormatException e) {
      throw new IllegalArgumentException("maxResults must be a number", e);
    }
    if (requested < 1) {
      throw new IllegalArgumentException("maxResults must be greater than zero");
    }
    return Math.min(requested, MAX_LIST_OBJECTS_RESULTS);
  }

  /**
   * Validates an OCI region name used in Object Storage host construction.
   */
  private static String validateRegion(String region) {
    String value = requireNonBlank(region, "region").toLowerCase(Locale.ROOT);
    if (!OCI_REGION.matcher(value).matches()) {
      throw new IllegalArgumentException("Invalid OCI region");
    }
    return value;
  }

  /**
   * Returns a trimmed value, rejecting missing or blank required inputs.
   */
  private static String requireNonBlank(String value, String fieldName) {
    if (value == null || value.isBlank()) {
      throw new IllegalArgumentException(fieldName + " must not be blank");
    }
    return value.trim();
  }

  /**
   * URL-encodes a single Object Storage path segment.
   */
  private static String encodePathSegment(String value) {
    return URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20");
  }

  /**
   * URL-encodes an object name while preserving slash-separated object prefixes.
   */
  private static String encodeObjectName(String objectName) {
    String[] segments = objectName.split("/", -1);
    for (int i = 0; i < segments.length; i++) {
      segments[i] = encodePathSegment(segments[i]);
    }
    return String.join("/", segments);
  }

}
