/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.exception;

/**
 * A custom exception thrown when an error occurs during the initialization phase of the MCP server.
 * <p>
 * This exception is used to indicate failures related to initial setup, such as parsing
 * command-line arguments, reading the OpenAPI specification, or configuring the server
 * before it is ready to execute tools.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public class McpServerToolInitializeException extends Exception {

    /**
     * Constructs a new {@code McpServerToolInitializeException} with the specified detail message.
     *
     * @param message The detail message (which is saved for later retrieval by the {@link #getMessage()} method).
     */
    public McpServerToolInitializeException(String message) {
        super(message);
    }

    /**
     * Constructs a new {@code McpServerToolInitializeException} with the specified detail message and cause.
     * <p>
     * Note that the detail message associated with {@code cause} is <em>not</em> automatically
     * incorporated in this exception's detail message.
     *
     * @param message The detail message (which is saved for later retrieval by the {@link #getMessage()} method).
     * @param cause   The cause (which is saved for later retrieval by the {@link #getCause()} method).
     * A {@code null} value is permitted, and indicates that the cause is nonexistent or unknown.
     */
    public McpServerToolInitializeException(String message, Throwable cause) {
        super(message, cause);
    }
}
