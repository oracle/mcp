package com.oracle.mcp.openapi.fetcher;

public enum AuthType {
    NONE,           // No authentication
    BASIC,          // Basic auth with username/password
    BEARER_TOKEN,   // OAuth2/JWT bearer token
    API_KEY         // API key in header or query param
}