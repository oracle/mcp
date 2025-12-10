package com.oracle.database.mcptoolkit;

import java.util.regex.*;

public class EnvSubstitutor {
  private static final Pattern PLACEHOLDER = Pattern.compile("\\$\\{([^}]+)}");

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
}