/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit;

import java.util.Arrays;
import java.util.regex.*;

/**
 * The EnvSubstitutor class provides a method for substituting environment variables in a given string.
 * It replaces placeholders in the format ${VARIABLE_NAME} with the corresponding environment variable values.
 */
public class EnvSubstitutor {
  /**
   * Pattern used to match placeholders in the input string.
   * The pattern matches strings in the format ${VARIABLE_NAME}.
   */
  private static final Pattern PLACEHOLDER = Pattern.compile("\\$\\{([^}]+)}");

  /**
   * Substitutes environment variables in the given input string.
   *
   * @param input the input string containing placeholders for environment variables
   * @return the input string with environment variables substituted
   * @throws IllegalStateException if an environment variable is not set
   */
  public static String substituteEnvVars(String input) {
    if (input == null) return null;
    Matcher m = PLACEHOLDER.matcher(input);
    StringBuffer sb = new StringBuffer();
    while (m.find()) {
      String var = m.group(1);
      String value = System.getenv(var);
      if (value == null) {
        throw new IllegalStateException("Missing environment variable for: " + var);
      }
      m.appendReplacement(sb, Matcher.quoteReplacement(value));
    }
    m.appendTail(sb);
    return sb.toString();
  }

  public static char[] substituteEnvVarsInCharArray(char[] input) {
    if (input == null) return null;
    StringBuilder output = new StringBuilder(input.length * 2); // Maybe bigger due to expansions
    for (int i = 0; i < input.length; ) {
      if (input[i] == '$' && (i + 1) < input.length && input[i + 1] == '{') {
        int end = i + 2;
        while (end < input.length && input[end] != '}') {
          end++;
        }
        if (end < input.length) {
          // Extract variable name
          String varName = new String(input, i + 2, end - (i + 2));
          String value = System.getenv(varName);
          if (value == null) {
            throw new IllegalStateException("Missing environment variable for: " + varName);
          }
          output.append(value);
          i = end + 1;
          continue;
        }
      }
      output.append(input[i]);
      i++;
    }
    char[] result = new char[output.length()];
    output.getChars(0, output.length(), result, 0);
    // Clear input
    Arrays.fill(input, '\0');
    return result;
  }
}