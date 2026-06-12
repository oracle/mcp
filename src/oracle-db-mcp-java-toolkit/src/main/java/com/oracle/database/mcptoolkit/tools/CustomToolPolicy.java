/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.tools;

import com.oracle.database.mcptoolkit.ServerConfig;
import com.oracle.database.mcptoolkit.config.EditToolsConfig;
import com.oracle.database.mcptoolkit.config.ToolConfig;
import com.oracle.database.mcptoolkit.config.ToolParameterConfig;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * Shared validation for YAML-defined SQL tools.
 */
public final class CustomToolPolicy {
  private static final Pattern SAFE_TOOL_NAME = Pattern.compile("[A-Za-z][A-Za-z0-9_.-]{0,127}");
  private static final Pattern SAFE_PARAMETER_NAME = Pattern.compile("[A-Za-z][A-Za-z0-9_]{0,127}");
  private static final Set<String> SUPPORTED_PARAMETER_TYPES = Set.of("string", "number", "integer", "boolean");
  private static final Set<String> DEFAULT_ALLOWED_STATEMENT_TYPES = Set.of("SELECT");

  private CustomToolPolicy() {}

  public static ValidationResult validateForEditTools(String name, ToolConfig toolConfig, ServerConfig config) {
    EditToolsConfig policy = config != null ? config.editToolsPolicy : null;
    if (policy != null && Boolean.FALSE.equals(policy.enabled)) {
      return ValidationResult.invalid("edit-tools is disabled by admin.editTools.enabled=false.");
    }
    return validate(name, toolConfig, config, true);
  }

  public static ValidationResult validateForRuntime(String name, ToolConfig toolConfig, ServerConfig config) {
    return validate(name, toolConfig, config, false);
  }

  public static ValidationResult validateToolName(String name) {
    if (name == null || name.isBlank()) {
      return ValidationResult.invalid("'name' is required");
    }
    if (!SAFE_TOOL_NAME.matcher(name).matches()) {
      return ValidationResult.invalid("Invalid tool name. Use 1-128 characters, start with a letter, and use only letters, digits, '_', '.', or '-'.");
    }
    String normalizedName = name.trim().toLowerCase(Locale.ROOT);
    if (ServerConfig.isBuiltInToolName(normalizedName) || ServerConfig.isBuiltInToolsetName(normalizedName)) {
      return ValidationResult.invalid("Invalid tool name. '" + name + "' conflicts with a built-in tool or toolset.");
    }
    return ValidationResult.ok();
  }

  private static ValidationResult validate(String name, ToolConfig toolConfig, ServerConfig config, boolean enforceEditToolsPolicy) {
    ValidationResult nameValidation = validateToolName(name);
    if (!nameValidation.valid()) {
      return nameValidation;
    }

    if (toolConfig == null) {
      return ValidationResult.invalid("Tool definition is required.");
    }

    EditToolsConfig policy = enforceEditToolsPolicy && config != null ? config.editToolsPolicy : null;
    String dataSource = toolConfig.dataSource;
    if (dataSource == null || dataSource.isBlank()) {
      return ValidationResult.invalid("'dataSource' is required for YAML-defined SQL tools.");
    }
    if (config == null || config.sources == null || !config.sources.containsKey(dataSource)) {
      return ValidationResult.invalid("Unknown dataSource '" + dataSource + "'. It must reference an entry under dataSources.");
    }
    if (policy != null && policy.allowedDataSources != null && !policy.allowedDataSources.isEmpty()
            && policy.allowedDataSources.stream().noneMatch(dataSource::equals)) {
      return ValidationResult.invalid("dataSource '" + dataSource + "' is not allowed by admin.editTools.allowedDataSources.");
    }

    String statement = toolConfig.statement;
    if (statement == null || statement.isBlank()) {
      return ValidationResult.invalid("'statement' is required for YAML-defined SQL tools.");
    }
    if (hasStatementSeparator(statement)) {
      return ValidationResult.invalid("Invalid SQL statement. Multiple statements are not allowed.");
    }

    if (enforceEditToolsPolicy) {
      String statementType = getStatementType(statement);
      if (statementType == null) {
        return ValidationResult.invalid("Invalid SQL statement. Could not determine statement type.");
      }
      Set<String> allowedStatementTypes = allowedStatementTypes(policy);
      if (!allowedStatementTypes.contains(statementType)) {
        return ValidationResult.invalid("Statement type '" + statementType + "' is not allowed. Allowed statement types: " + allowedStatementTypes + ".");
      }
    }

    List<String> parameterNames = new ArrayList<>();
    if (toolConfig.parameters != null) {
      Set<String> seen = new LinkedHashSet<>();
      for (ToolParameterConfig param : toolConfig.parameters) {
        if (param == null) {
          return ValidationResult.invalid("Invalid parameter entry. Each parameter must be an object.");
        }
        String paramName = param.name;
        if (paramName == null || !SAFE_PARAMETER_NAME.matcher(paramName).matches()) {
          return ValidationResult.invalid("Invalid parameter name. Use 1-128 characters, start with a letter, and use only letters, digits, or '_'.");
        }
        if (!seen.add(paramName)) {
          return ValidationResult.invalid("Duplicate parameter '" + paramName + "'.");
        }
        String paramType = param.type;
        if (paramType == null || !SUPPORTED_PARAMETER_TYPES.contains(paramType.toLowerCase(Locale.ROOT))) {
          return ValidationResult.invalid("Invalid type for parameter '" + paramName + "'. Supported types: " + SUPPORTED_PARAMETER_TYPES + ".");
        }
        parameterNames.add(paramName);
      }
    }

    String bindError = validateSqlBinds(statement, parameterNames);
    return bindError == null ? ValidationResult.ok() : ValidationResult.invalid(bindError);
  }

  private static Set<String> allowedStatementTypes(EditToolsConfig policy) {
    if (policy == null || policy.allowedStatementTypes == null || policy.allowedStatementTypes.isEmpty()) {
      return DEFAULT_ALLOWED_STATEMENT_TYPES;
    }
    Set<String> allowed = new LinkedHashSet<>();
    for (String type : policy.allowedStatementTypes) {
      if (type != null && !type.isBlank()) {
        allowed.add(type.trim().toUpperCase(Locale.ROOT));
      }
    }
    return allowed.isEmpty() ? DEFAULT_ALLOWED_STATEMENT_TYPES : allowed;
  }

  private static String getStatementType(String statement) {
    String cleaned = stripLeadingSqlComments(statement);
    if (cleaned.isBlank()) {
      return null;
    }
    int end = 0;
    while (end < cleaned.length() && Character.isLetter(cleaned.charAt(end))) {
      end++;
    }
    return end == 0 ? null : cleaned.substring(0, end).toUpperCase(Locale.ROOT);
  }

  private static String stripLeadingSqlComments(String statement) {
    String s = statement.stripLeading();
    boolean changed;
    do {
      changed = false;
      if (s.startsWith("--")) {
        int newline = s.indexOf('\n');
        s = newline < 0 ? "" : s.substring(newline + 1).stripLeading();
        changed = true;
      } else if (s.startsWith("/*")) {
        int end = s.indexOf("*/");
        s = end < 0 ? "" : s.substring(end + 2).stripLeading();
        changed = true;
      }
    } while (changed);
    return s;
  }

  private static boolean hasStatementSeparator(String statement) {
    ScanState state = new ScanState();
    for (int i = 0; i < statement.length(); i++) {
      char c = statement.charAt(i);
      char next = i + 1 < statement.length() ? statement.charAt(i + 1) : '\0';
      if (state.consume(c, next)) {
        i++;
        continue;
      }
      if (!state.inQuotedContent() && c == ';') {
        return true;
      }
    }
    return false;
  }

  private static String validateSqlBinds(String statement, List<String> parameterNames) {
    BindInfo bindInfo = extractBinds(statement);
    Set<String> declared = new LinkedHashSet<>(parameterNames);

    if (!bindInfo.namedBinds().isEmpty() && bindInfo.positionalBindCount() > 0) {
      return "Invalid SQL statement. Do not mix named ':' binds and positional '?' binds.";
    }

    if (bindInfo.positionalBindCount() > 0) {
      if (parameterNames.size() != bindInfo.positionalBindCount()) {
        return "Parameter count does not match positional SQL binds. Expected "
                + bindInfo.positionalBindCount() + " parameter(s).";
      }
      return null;
    }

    Set<String> missingDeclarations = new LinkedHashSet<>(bindInfo.namedBinds());
    missingDeclarations.removeAll(declared);
    if (!missingDeclarations.isEmpty()) {
      return "SQL bind(s) missing parameter declarations: " + missingDeclarations + ".";
    }

    Set<String> unusedParameters = new LinkedHashSet<>(declared);
    unusedParameters.removeAll(bindInfo.namedBinds());
    if (!unusedParameters.isEmpty()) {
      return "Parameter(s) not used by SQL binds: " + unusedParameters + ".";
    }

    return null;
  }

  private static BindInfo extractBinds(String statement) {
    ScanState state = new ScanState();
    Set<String> named = new LinkedHashSet<>();
    int positional = 0;
    for (int i = 0; i < statement.length(); i++) {
      char c = statement.charAt(i);
      char next = i + 1 < statement.length() ? statement.charAt(i + 1) : '\0';
      if (state.consume(c, next)) {
        i++;
        continue;
      }
      if (state.inQuotedContent()) {
        continue;
      }
      if (c == '?') {
        positional++;
      } else if (c == ':' && isParameterStart(next)) {
        int start = i + 1;
        int end = start + 1;
        while (end < statement.length() && isParameterPart(statement.charAt(end))) {
          end++;
        }
        named.add(statement.substring(start, end));
        i = end - 1;
      }
    }
    return new BindInfo(named, positional);
  }

  private static boolean isParameterStart(char c) {
    return Character.isLetter(c);
  }

  private static boolean isParameterPart(char c) {
    return Character.isLetterOrDigit(c) || c == '_';
  }

  private record BindInfo(Set<String> namedBinds, int positionalBindCount) {}

  public record ValidationResult(boolean valid, String message) {
    static ValidationResult ok() {
      return new ValidationResult(true, null);
    }

    static ValidationResult invalid(String message) {
      return new ValidationResult(false, message);
    }
  }

  private static final class ScanState {
    private boolean singleQuote;
    private boolean doubleQuote;
    private boolean lineComment;
    private boolean blockComment;

    boolean consume(char c, char next) {
      if (lineComment) {
        if (c == '\n' || c == '\r') {
          lineComment = false;
        }
        return false;
      }
      if (blockComment) {
        if (c == '*' && next == '/') {
          blockComment = false;
          return true;
        }
        return false;
      }
      if (singleQuote) {
        if (c == '\'' && next == '\'') {
          return true;
        }
        if (c == '\'') {
          singleQuote = false;
        }
        return false;
      }
      if (doubleQuote) {
        if (c == '"') {
          doubleQuote = false;
        }
        return false;
      }
      if (c == '-' && next == '-') {
        lineComment = true;
        return true;
      }
      if (c == '/' && next == '*') {
        blockComment = true;
        return true;
      }
      if (c == '\'') {
        singleQuote = true;
      } else if (c == '"') {
        doubleQuote = true;
      }
      return false;
    }

    boolean inQuotedContent() {
      return singleQuote || doubleQuote || lineComment || blockComment;
    }
  }
}
