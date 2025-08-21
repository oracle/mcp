package com.oracle.mcp.openapi.enums;

import com.oracle.mcp.openapi.model.McpServerConfig;

public enum OpenApiSchemaAuthType {
    BASIC,UNKNOWN;

    public static OpenApiSchemaAuthType getType(McpServerConfig request){
        String authType = request.getRawAuthType();
        if(authType.equals(BASIC.name())){
            return BASIC;
        }
        return UNKNOWN;
    }
}
