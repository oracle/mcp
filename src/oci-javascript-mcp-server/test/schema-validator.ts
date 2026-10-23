/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { createRequire } from "node:module";
import type {
  JsonSchemaType,
  jsonSchemaValidator
} from "@modelcontextprotocol/sdk/validation/types.js";

// SDK 1.31.0's provider declaration uses a default Ajv import as a type,
// which fails under NodeNext. Use its runtime export with the public interface.
const { AjvJsonSchemaValidator } = createRequire(import.meta.url)(
  "@modelcontextprotocol/sdk/validation/ajv-provider.js"
) as { AjvJsonSchemaValidator: new () => jsonSchemaValidator };

export function schemaValidator(schema: object) {
  // Zod and the SDK differ in unused JSON Schema vocabulary type definitions.
  return new AjvJsonSchemaValidator().getValidator(schema as JsonSchemaType);
}
