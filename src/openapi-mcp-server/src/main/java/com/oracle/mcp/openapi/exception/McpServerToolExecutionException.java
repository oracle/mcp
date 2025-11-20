/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.exception;

/**
 * A custom exception thrown when an error occurs during the execution of an OpenAPI-based MCP tool.
 * <p>
 * This exception is used to wrap underlying issues such as network errors, I/O problems,
 * or any other runtime failure encountered while invoking an external API endpoint.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public class McpServerToolExecutionException extends Exception {

    /**
     * Constructs a new {@code McpServerToolExecutionException} with the specified detail message.
     *
     * @param message The detail message (which is saved for later retrieval by the {@link #getMessage()} method).
     */
    public McpServerToolExecutionException(String message) {
        super(message);
    }

    /**
     * Constructs a new {@code McpServerToolExecutionException} with the specified detail message and cause.
     * <p>
     * Note that the detail message associated with {@code cause} is <em>not</em> automatically
     * incorporated in this exception's detail message.
     *
     * @param message The detail message (which is saved for later retrieval by the {@link #getMessage()} method).
     * @param cause   The cause (which is saved for later retrieval by the {@link #getCause()} method).
     * A {@code null} value is permitted, and indicates that the cause is nonexistent or unknown.
     */
    public McpServerToolExecutionException(String message, Throwable cause) {
        super(message, cause);
    }
}
