package com.oracle.mcp.openapi.fetcher;

public record AuthConfig(
        AuthType type,
        String username,   // for BASIC
        String password,   // for BASIC
        String token,      // for BEARER_TOKEN or API_KEY
        String apiKeyName  // if API_KEY in query/header
) {
    public static AuthConfig none() {
        return new AuthConfig(AuthType.NONE, null, null, null, null);
    }
}