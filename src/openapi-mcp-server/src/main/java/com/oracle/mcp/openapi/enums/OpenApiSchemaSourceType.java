package com.oracle.mcp.openapi.enums;

import com.oracle.mcp.openapi.model.McpServerConfig;

public enum OpenApiSchemaSourceType {
    URL,FILE;

    public static OpenApiSchemaSourceType getType(McpServerConfig request){

        if(request.getSpecUrl()!=null){
            return URL;
        }else{
            return FILE;
        }

    }
}
