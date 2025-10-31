/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.util;

/**
 * Utility class for MCP Server operations.
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public final class McpServerUtil {

    private static final String CAMEL_CASE_REGEX = "[^a-zA-Z0-9]+";

    /**
     * Converts an input string into camelCase format.
     */
    public static String toCamelCase(String input) {
        if (input == null || input.isEmpty()){
            return "";
        }
        String[] parts = input.split(CAMEL_CASE_REGEX);
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            String word = parts[i].toLowerCase();
            if (word.isEmpty()) continue;
            if (i == 0) {
                sb.append(word);
            } else {
                sb.append(Character.toUpperCase(word.charAt(0))).append(word.substring(1));
            }
        }
        return sb.toString();
    }
    /**
     * Capitalizes the first letter of the given string.
     * If the string is null or empty, it is returned as is.
     *
     * @param str The input string to capitalize.
     * @return The capitalized string, or the original string if it is null or empty.
     */
    public static  String capitalize(String str) {
        if (str == null || str.isEmpty()){
            return str;
        }
        return str.substring(0, 1).toUpperCase() + str.substring(1);
    }
    /**
     * Checks if a string is not null and not empty.
     *
     * @param str The string to check.
     * @return true if the string is not null and not empty, false otherwise.
     */
    public static boolean isNotBlank(String str) {
        return str != null && !str.isEmpty();
    }

}
