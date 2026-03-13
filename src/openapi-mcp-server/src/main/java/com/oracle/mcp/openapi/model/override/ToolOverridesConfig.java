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

import java.util.Collections;
import java.util.Map;
import java.util.Set;
/**
 * Model class representing configuration for tool overrides.
 * Allows specifying which tools to include or exclude, and detailed overrides for specific tools.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
@JsonIgnoreProperties(ignoreUnknown = true)
public class ToolOverridesConfig {

    public final static ToolOverridesConfig EMPTY_TOOL_OVERRIDE_CONFIG = new ToolOverridesConfig();

    public ToolOverridesConfig(){

    }

    @JsonProperty("includeOnly")
    private Set<String> includeOnly = Collections.emptySet();

    @JsonProperty("exclude")
    private Set<String> exclude = Collections.emptySet();

    @JsonProperty("tools")
    private Map<String, ToolOverride> tools = Collections.emptyMap();

    public Set<String> getIncludeOnly() {
        return includeOnly;
    }

    public void setIncludeOnly(Set<String> includeOnly) {
        this.includeOnly = includeOnly;
    }

    public Set<String> getExclude() {
        return exclude;
    }

    public void setExclude(Set<String> exclude) {
        this.exclude = exclude;
    }

    public Map<String, ToolOverride> getTools() {
        return tools==null?Collections.emptyMap():tools;
    }

    public void setTools(Map<String, ToolOverride> tools) {
        this.tools = tools;
    }
}
