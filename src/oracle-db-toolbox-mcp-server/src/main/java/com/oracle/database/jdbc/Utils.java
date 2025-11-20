package com.oracle.database.jdbc;

import io.modelcontextprotocol.spec.McpSchema;

import java.io.IOException;
import java.io.Reader;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.Provider;
import java.security.Security;
import java.sql.Clob;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Stream;

public class Utils {

  static McpSchema.CallToolResult errorResult(String toolName, Exception e) {
    String msg = e.getMessage() != null ? e.getMessage() : e.toString();
    return McpSchema.CallToolResult.builder()
        .isError(true)
        .addTextContent("Error in " + toolName + ": " + msg)
        .build();
  }

  /**
   * Loads external JARs from the directory given by
   * the system property {@code ojdbc.ext.dir} and makes them available
   * to the application at runtime.
   *
   * <p>Behavior:</p>
   * <ul>
   *   <li>If the property is missing/blank, does nothing.</li>
   *   <li>Recursively scans the directory for {@code .jar} files.</li>
   *   <li>Adds all found JARs to a temporary class loader and activates it.</li>
   *   <li>Logs basic problems (invalid dir, scan failures, no JARs found).</li>
   * </ul>
   *
   */
  static void installExternalExtensionsFromDir() {
    final String dir = System.getProperty("ojdbc.ext.dir");
    if (dir == null || dir.isBlank()) {
      return;
    }

    final Path root = Paths.get(dir);
    if (!Files.isDirectory(root)) {
      System.err.println("[mcp-ojdbc] ojdbc.ext.dir is not a directory: " + dir);
      return;
    }
    final List<URL> jarUrls = new ArrayList<>();
    try (Stream<Path> walk = Files.walk(root)) {
      walk.filter(p -> Files.isRegularFile(p) && p.toString().toLowerCase(Locale.ROOT).endsWith(".jar"))
          .forEach(p -> {
            try {
              jarUrls.add(p.toUri().toURL());
            } catch (Exception e) {
              System.err.println("[mcp-ojdbc] Failed to add jar: " + p + " -> " + e);
            }
          });
    } catch (Exception e) {
      System.err.println("[mcp-ojdbc] Failed to scan " + dir + " -> " + e);
      return;
    }

    if (jarUrls.isEmpty()) {
      System.err.println("[mcp-ojdbc] No jars found under " + dir);
      return;
    }

    final ClassLoader previousTccl = Thread.currentThread().getContextClassLoader();
    final URLClassLoader ucl = new URLClassLoader(jarUrls.toArray(new URL[0]), previousTccl);
    Thread.currentThread().setContextClassLoader(ucl);

    try {
      Class<?> providerClass = Class.forName("oracle.security.pki.OraclePKIProvider", true, ucl);
      Provider provider = (Provider) providerClass.getDeclaredConstructor().newInstance();
      Security.addProvider(provider);
    } catch (Throwable ignored) {}

    Runtime.getRuntime().addShutdownHook(new Thread(() -> {
      try { Thread.currentThread().setContextClassLoader(previousTccl); } catch (Throwable ignored) {}
      try { ucl.close(); } catch (Throwable ignored) {}
    }));
  }

  /**
   * Converts a ResultSet into a list of maps (rows).
   *
   * @param rs a valid ResultSet
   * @return list of rows with column:value mapping
   * @throws SQLException if reading from ResultSet fails
   */
  static List<Map<String, Object>> rsToList(ResultSet rs) throws SQLException {
    List<Map<String, Object>> out = new ArrayList<>();
    ResultSetMetaData md = rs.getMetaData();
    int cols = md.getColumnCount();
    while (rs.next()) {
      Map<String, Object> row = new LinkedHashMap<>();
      for (int i = 1; i <= cols; i++) {
        String colName = md.getColumnLabel(i);
        Object value = rs.getObject(i);

        if (value instanceof Clob clob) {
          value = clobToString(clob);
        }

        row.put(colName, value);
      }
      out.add(row);
    }
    return out;
  }

  /**
   * Safely converts a CLOB to String.
   */
  private static String clobToString(Clob clob) throws SQLException {
    if (clob == null)
      return null;
    StringBuilder sb = new StringBuilder();
    try (Reader reader = clob.getCharacterStream()) {
      char[] buf = new char[4096];
      int len;
      while ((len = reader.read(buf)) != -1) {
        sb.append(buf, 0, len);
      }
    } catch (IOException e) {
      throw new SQLException("Failed to read CLOB", e);
    }
    return sb.toString();
  }
}
