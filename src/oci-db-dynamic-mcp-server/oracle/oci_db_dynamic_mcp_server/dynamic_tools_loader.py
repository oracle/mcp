from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests
import yaml

SPEC_INDEX_JSON = "https://docs.oracle.com/en-us/iaas/api/specs/index.json"
BASE_SPEC_URL = "https://docs.oracle.com/en-us/iaas/api/specs/"
HTTP_METHODS = {"get", "post", "put", "delete", "patch"}


@dataclass
class OperationMeta:
    operationId: str
    httpMethod: str
    path: str
    summary: str
    description: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    requestBodySchema: Dict[str, Any] = field(default_factory=dict)
    responseSchema: Dict[str, Any] = field(default_factory=dict)
    relatedResource: str = "other"


def load_yaml_from_url(url: str):
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return yaml.safe_load(resp.text)


def load_yaml_from_public_docs():
    try:
        resp = requests.get(SPEC_INDEX_JSON, timeout=15)
        resp.raise_for_status()
        index_json = resp.json()
        specs_node = index_json.get("database", {}).get("specs", [])
        if specs_node:
            full_url = BASE_SPEC_URL + specs_node[0].split("/")[-1]
            print(f"Loading OCI Spec from: {full_url}")
            return load_yaml_from_url(full_url)
        return {}
    except Exception as e:
        print(f"Spec load failed: {e}")
        return {}


def resolve_schema(schema: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively resolve $ref AND merge 'allOf' inheritance.
    """
    if not isinstance(schema, dict):
        return schema

    # 1. Resolve $ref
    if "$ref" in schema:
        ref = schema["$ref"]
        # Handle both root-based (#/definitions/...) and relative refs
        if ref.startswith("#/"):
            parts = ref[2:].split("/")
            node = spec
            for p in parts:
                node = node.get(p, {})
            return resolve_schema(node, spec)
        else:
            parts = ref.split("/")
            node = spec
            for p in parts:
                node = node.get(p, {})
            return resolve_schema(node, spec)

    # 2. Handle 'allOf' (Merge properties from parents)
    if "allOf" in schema:
        merged = {"type": "object", "properties": {}, "required": []}

        for part in schema["allOf"]:
            resolved_part = resolve_schema(part, spec)

            if "properties" in resolved_part:
                merged["properties"].update(resolved_part["properties"])

            if "required" in resolved_part:
                merged["required"].extend(resolved_part["required"])

            if "type" in resolved_part and "type" not in merged:
                merged["type"] = resolved_part["type"]

        if "properties" in schema:
            merged["properties"].update(schema["properties"])
        if "required" in schema:
            merged["required"].extend(schema["required"])

        merged["required"] = list(set(merged["required"]))
        return merged

    # 3. Recurse
    result = {}
    for k, v in schema.items():
        if isinstance(v, dict):
            result[k] = resolve_schema(v, spec)
        elif isinstance(v, list):
            result[k] = [
                resolve_schema(i, spec) if isinstance(i, dict) else i for i in v
            ]
        else:
            result[k] = v
    return result


def flatten_schema(
    schema: Dict[str, Any], spec: Optional[Dict[str, Any]] = None
) -> Dict[str, Dict[str, Any]]:
    flat: Dict[str, Dict[str, Any]] = {}
    if not schema or not isinstance(schema, dict):
        return flat

    def _walk(obj_schema: Dict[str, Any], path: List[str]):
        if not isinstance(obj_schema, dict):
            return

        props = obj_schema.get("properties", {})
        required_props = set(obj_schema.get("required", []) or [])

        for prop_name, prop_schema in props.items():
            prop_path = path + [prop_name]
            prop_type = prop_schema.get("type")

            if not prop_type:
                if "items" in prop_schema:
                    prop_type = "array"
                elif "properties" in prop_schema:
                    prop_type = "object"
                else:
                    prop_type = "string"

            flat_key = "_".join(prop_path)

            if prop_type == "array":
                flat[flat_key] = {
                    "path": prop_path,
                    "type": "array",
                    "required": prop_name in required_props,
                }
                continue

            if prop_type == "object" and "properties" in prop_schema:
                _walk(prop_schema, prop_path)
                continue

            flat[flat_key] = {
                "path": prop_path,
                "type": prop_type,
                "required": prop_name in required_props,
                "raw_schema": prop_schema,
            }

    if schema.get("type") == "object" or "properties" in schema:
        _walk(schema, [])
    return flat


def infer_resource_from_path_or_tags(path: str, tags: list) -> str:
    if not path:
        return "unknown"
    parts = path.strip("/").split("/")
    return parts[0] if parts else "unknown"


def extract_required_output_fields(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Given a resolved schema, return a simplified schema containing
    ONLY the 'required' fields. Handles Arrays and Objects.
    """
    if not schema or not isinstance(schema, dict):
        return {}

    prop_type = schema.get("type")

    # CASE A: ARRAY (e.g. ListDbSystems returns [DbSystem])
    if prop_type == "array" and "items" in schema:
        item_schema = schema["items"]
        # Recurse into the item definition
        simplified_item = extract_required_output_fields(item_schema)
        return {"type": "array", "items": simplified_item}

    # CASE B: OBJECT (e.g. GetDbSystem returns DbSystem)
    if prop_type == "object" or "properties" in schema:
        required_keys = schema.get("required", [])
        all_props = schema.get("properties", {})

        simplified_props = {}
        for key in required_keys:
            if key in all_props:
                simplified_props[key] = all_props[key]

        return {
            "type": "object",
            "properties": simplified_props,
            "required": required_keys,
        }

    # Fallback for scalars
    return schema


def build_registry(api_spec: Dict[str, Any]) -> Dict[str, OperationMeta]:
    paths = api_spec.get("paths", {})
    registry = {}

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        path_params = path_item.get("parameters", [])

        for method, op in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(op, dict):
                continue

            op_id = op.get("operationId", f"{method}_{path}")

            # 1. Parameters
            params = []
            all_raw_params = path_params + op.get("parameters", [])
            for p in all_raw_params:
                params.append(resolve_schema(p, api_spec))

            # 2. Request Body
            req_schema = {}
            if "requestBody" in op:  # OpenAPI 3
                content = op["requestBody"].get("content", {})
                if "application/json" in content:
                    req_schema = resolve_schema(
                        content["application/json"].get("schema", {}), api_spec
                    )
            for p in params:  # Swagger 2
                if p.get("in") == "body" and "schema" in p:
                    req_schema = resolve_schema(p["schema"], api_spec)

            # 3. Response Schema
            resp_schema = {}
            responses = op.get("responses", {})
            success_code = next(
                (c for c in ["200", "201", "202", "204"] if c in responses), None
            )

            if success_code:
                resp_obj = responses[success_code]
                if "schema" in resp_obj:
                    resp_schema = resolve_schema(resp_obj["schema"], api_spec)
                elif "content" in resp_obj:
                    content = resp_obj["content"]
                    if "application/json" in content:
                        resp_schema = resolve_schema(
                            content["application/json"].get("schema", {}), api_spec
                        )

            registry[op_id] = OperationMeta(
                operationId=op_id,
                httpMethod=method.upper(),
                path=path,
                summary=op.get("summary", ""),
                description=op.get("description", ""),
                parameters=params,
                requestBodySchema=req_schema,
                responseSchema=resp_schema,
                relatedResource=infer_resource_from_path_or_tags(
                    path, op.get("tags", [])
                ),
            )
    return registry


def build_tools_from_latest_spec(
    allowed_resources: List[str] = None,
) -> List[Dict[str, Any]]:
    api_spec = load_yaml_from_public_docs()
    if not api_spec:
        return []
    registry = build_registry(api_spec)
    exposed_tools = []

    allowed_set = {r.lower() for r in allowed_resources} if allowed_resources else None

    for op_id, meta in registry.items():

        if allowed_set and meta.relatedResource.lower() not in allowed_set:
            continue
        if meta.description.startswith("**Deprecated"):
            continue

        flat_schema = (
            flatten_schema(meta.requestBodySchema) if meta.requestBodySchema else {}
        )

        final_params = []
        for p in meta.parameters:
            if p.get("in") == "body":
                continue
            if p.get("name") in flat_schema:
                continue
            final_params.append(p)

        filtered_output_schema = extract_required_output_fields(meta.responseSchema)

        exposed_tools.append(
            {
                "name": meta.operationId,
                "description": meta.description,
                "method": meta.httpMethod,
                "path": meta.path,
                "schema": meta.requestBodySchema,
                "flatSchema": flat_schema,
                "output_schema": filtered_output_schema,
                "parameters": final_params,
                "resource": meta.relatedResource,
            }
        )
    return exposed_tools


if __name__ == "__main__":
    tools = build_tools_from_latest_spec()
    print(f"Loaded {len(tools)} tools.")
