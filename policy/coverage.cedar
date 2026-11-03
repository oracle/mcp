// Copyright (c) 2026, Oracle and/or its affiliates.
// Licensed under the Universal Permissive License v1.0: https://oss.oracle.com/licenses/upl.
@id("python-server-coverage-floor")
permit (
    principal == Repository::Check::"coverage",
    action == Repository::Action::"acceptManifest",
    resource is Repository::Manifest
)
when { context.coverageFloor >= 90 };
