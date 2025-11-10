/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.mapper;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Unit tests for {@link McpToolMapper}.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public class McpToolMapperTest {

    private Set<String> existingNames;

    private static McpToolMapper toolNameTestMapper;

    @BeforeAll
    static void init() {
        toolNameTestMapper = (apiSpec, toolOverridesConfig) ->  List.of();
    }

    @BeforeEach
    void setUp() {
        existingNames = new HashSet<>();
    }

    @Test
    void shouldUseOperationIdWhenPresent() {
        String result = toolNameTestMapper.generateToolName("get", "/users", "listUsers", existingNames);
        assertEquals("listUsers", result);
    }

    @Test
    void shouldFallbackToMethodAndPathWhenNoOperationId() {
        String result = toolNameTestMapper.generateToolName("get", "/users", null, existingNames);
        assertEquals("getUsers", result);
    }

    @Test
    void shouldHandlePathVariables() {
        String result = toolNameTestMapper.generateToolName("get", "/users/{id}", null, existingNames);
        assertEquals("getUsersById", result);
    }

    @Test
    void shouldDifferentiateByHttpMethod() {
        String getName = toolNameTestMapper.generateToolName("get", "/users/{id}", null, existingNames);
        String deleteName = toolNameTestMapper.generateToolName("delete", "/users/{id}", null, existingNames);

        assertEquals("getUsersById", getName);
        assertEquals("deleteUsersById", deleteName);
    }

    @Test
    void shouldHandleDuplicateOperationIds() {
        String first = toolNameTestMapper.generateToolName("get", "/users", "getUsers", existingNames);
        String second = toolNameTestMapper.generateToolName("post", "/users", "getUsers", existingNames);

        assertEquals("getUsers", first);
        assertEquals("getUsersPost", second);
    }

    @Test
    void shouldAppendLastSegmentIfStillClashing() {
        existingNames.add("getUsersByIdDelete");

        String result = toolNameTestMapper.generateToolName("delete", "/users/{id}", null, existingNames);
        assertEquals("deleteUsersById", result);
    }
}
