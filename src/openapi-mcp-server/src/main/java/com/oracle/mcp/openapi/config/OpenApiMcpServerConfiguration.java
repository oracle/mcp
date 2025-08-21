package com.oracle.mcp.openapi.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.fetcher.OpenApiSchemaFetcher;
import com.oracle.mcp.openapi.fetcher.RestApiExecutionService;
import com.oracle.mcp.openapi.tool.OpenApiToMcpToolConverter;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


import java.net.http.HttpClient;
import java.time.Duration;

@Configuration
public class OpenApiMcpServerConfiguration {

    @Bean
    public HttpClient httpClient() {
        return HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    @Bean("jsonMapper")
    public ObjectMapper jsonMapper() {
        return new ObjectMapper();
    }

    @Bean("yamlMapper")
    public ObjectMapper yamlMapper() {
        return new ObjectMapper(new YAMLFactory());
    }

    @Bean
    public McpServerCacheService mcpServerCacheService(){
        return new McpServerCacheService();
    }

    @Bean
    public RestApiExecutionService restApiExecutionService(){
        return new RestApiExecutionService();
    }

    @Bean
    public OpenApiToMcpToolConverter openApiToMcpToolConverter(McpServerCacheService mcpServerCacheService) {
        return new OpenApiToMcpToolConverter(mcpServerCacheService);
    }


    @Bean
    public OpenApiSchemaFetcher openApiDefinitionFetcher(HttpClient httpClient, @Qualifier("jsonMapper") ObjectMapper jsonMapper, @Qualifier("yamlMapper") ObjectMapper yamlMapper){
        return new OpenApiSchemaFetcher(httpClient,jsonMapper,yamlMapper);
    }



}
