/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.model.override;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Map;

/**
 * Model class representing overrides for a specific tool.
 * Allows customization of tool properties such as name, title, description, and input schema.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@JsonIgnoreProperties(ignoreUnknown = true)
public class ToolOverride {

    public static final ToolOverride EMPTY_TOOL_OVERRIDE = new ToolOverride();

    @JsonProperty("name")
    private String name;

    @JsonProperty("title")
    private String title;

    @JsonProperty("description")
    private String description;

    @JsonProperty("inputSchema")
    private Map<String, Object> inputSchema;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public Map<String, Object> getInputSchema() {
        return inputSchema;
    }

    public void setInputSchema(Map<String, Object> inputSchema) {
        this.inputSchema = inputSchema;
    }
}