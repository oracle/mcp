/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.constants;


/**
 * Defines a collection of constant error message strings used throughout the application.
 * <p>
 * This interface centralizes user-facing error messages to ensure consistency and
 * ease of maintenance. By keeping them in one place, we can easily update or
 * translate them without searching through the entire codebase.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public interface ErrorMessage {

    String MISSING_API_SPEC = "API specification not provided. Please pass --api-spec or set the API_SPEC environment variable.";

    String MISSING_API_BASE_URL = "API base url not provided. Please pass --api-base-url or set the API_BASE_URL environment variable.";

    String MISSING_PATH_IN_SPEC = "'paths' object not found in the specification.";

    String INVALID_SPEC_DEFINITION = "Unsupported API definition: missing 'openapi' or 'swagger' field";

    String INVALID_SWAGGER_SPEC = "Invalid Swagger specification provided.";

}
