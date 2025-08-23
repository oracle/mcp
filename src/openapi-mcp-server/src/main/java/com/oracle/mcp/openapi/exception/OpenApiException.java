package com.oracle.mcp.openapi.exception;

public class OpenApiException extends Exception{


    public OpenApiException(String message) {
        super(message);
    }

    public OpenApiException(String message, Throwable cause) {
        super(message, cause);
    }
}
