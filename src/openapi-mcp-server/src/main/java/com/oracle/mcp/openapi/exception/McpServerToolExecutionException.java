package com.oracle.mcp.openapi.exception;

public class McpServerToolExecutionException extends Exception{


    public McpServerToolExecutionException(String message) {
        super(message);
    }

    public McpServerToolExecutionException(String message, Throwable cause) {
        super(message, cause);
    }
}
