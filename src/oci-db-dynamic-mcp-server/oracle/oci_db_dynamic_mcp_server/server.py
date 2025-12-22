"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0.
"""

import argparse
import os
import re
from typing import Annotated, Any, Dict, List, Optional

import oci
import requests
from fastmcp import FastMCP
from oci.auth.signers import security_token_signer
from pydantic import Field

from . import __project__
from .dynamic_tools_loader import build_tools_from_latest_spec

mcp = FastMCP(name=__project__)

# ---------------- TYPE MAPPING ----------------
TYPE_MAP = {
    "integer": "int",
    "boolean": "bool",
    "number": "float",
    "array": "list",
    "object": "dict",
    "string": "str",
}


# ---------------- OCI API INVOKER ----------------
def invoke_oci_api(method, path, params=None, payload=None, headers=None):
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )

    # Load security token
    with open(config["security_token_file"], "r") as f:
        security_token = f.read().strip()

    # Create signer
    signer = security_token_signer.SecurityTokenSigner(
        token=security_token,
        private_key=oci.signer.load_private_key_from_file(
            config["key_file"], pass_phrase=config.get("pass_phrase")
        ),
    )

    endpoint = f"https://database.{config['region']}.oraclecloud.com/20160918/"
    url = endpoint.rstrip("/") + "/" + path.lstrip("/")

    headers = headers or {"Content-Type": "application/json"}
    headers["authorization"] = f"Bearer {security_token}"
    headers["x-oci-secondary-auth"] = "true"
    headers["User-Agent"] = "oci-database-mcp-server"

    with requests.Session() as session:

        req = requests.Request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=payload,
            params=params or {},
            auth=signer,
        )

        prepared = req.prepare()

        response = session.send(prepared)
        return response.text


# ---------------- UNFLATTENER ----------------
def unflatten_payload(flat_input: dict, flat_schema: dict):
    root = {}
    for flat_key, meta in flat_schema.items():
        if flat_key not in flat_input:
            continue

        value = flat_input[flat_key]
        path = meta.get("path", [])
        if not path:
            root[flat_key] = value
            continue

        cursor = root
        for p in path[:-1]:
            if p not in cursor or not isinstance(cursor[p], dict):
                cursor[p] = {}
            cursor = cursor[p]
        cursor[path[-1]] = value
    return root


# ---------------- Utilities ----------------
def escape_string(s: str) -> str:
    if not s:
        return ""
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def clean_description_text(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"(?i)^Parameters\s*$", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"(?m)^\s*`[^`]+`.*$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_collapsed_parent_notes(resolved_schema: dict, flat_schema: dict) -> str:
    """
    Identify top-level objects that were 'collapsed' during flattening
    and append their descriptions to the tool context.
    These usually contain high-level logic (e.g., which subtype to use).
    """
    if not resolved_schema or "properties" not in resolved_schema:
        return ""

    lines = []
    # Iterate over the ORIGINAL schema properties
    for name, prop in resolved_schema["properties"].items():

        # If this top-level name is NOT in the flattened list, it means it was
        # a container object that got flattened away.
        if name not in flat_schema:
            desc_raw = prop.get("description", "").strip()
            if desc_raw:
                desc_clean = " ".join(desc_raw.splitlines()).strip()
                # Add it as a context note
                lines.append(f"\n* **{name} (Context)**: {desc_clean}")

    if not lines:
        return ""

    return "\n\n### Important Context" + "".join(lines)


def register_tools(allowed_resources: Optional[List[str]] = None):

    if allowed_resources is None:
        env_resources = os.getenv("OCI_ALLOWED_RESOURCES")
        if env_resources:
            allowed_resources = [r.strip() for r in env_resources.split(",")]

    print(f"Loading OCI Specs (Filter: {allowed_resources})...")
    tools = build_tools_from_latest_spec(allowed_resources=allowed_resources)
    print(f"Loaded {len(tools)} tools.")

    for t in tools:
        tool_name = t.get("name")
        flat_schema = t.get("flatSchema", {})
        resolved_schema = t.get("schema", {})

        param_map = {}
        required_args = []
        optional_args = []

        # --- A. Process Query/Path Params ---
        flat_top_names = {k.split("_", 1)[0] for k in flat_schema.keys()}

        for p in t.get("parameters", []):
            pname = p.get("name")
            if not pname:
                continue
            if p.get("in") == "body":
                continue
            if pname in flat_top_names:
                continue
            if pname in flat_schema:
                continue

            sanitized = pname.replace("-", "_")
            desc = escape_string(p.get("description", "No description").strip())

            raw_type = p.get("type") or p.get("schema", {}).get("type", "string")
            py_type = TYPE_MAP.get(raw_type, "str")

            param_map[sanitized] = {
                "orig_name": pname,
                "location": p.get("in", "query"),
                "type": py_type,
            }

            if p.get("required"):
                required_args.append(
                    f'{sanitized}: Annotated[{py_type}, Field(description="{desc}")]'
                )
            else:
                optional_args.append(
                    f'{sanitized}: Annotated[{py_type}, Field(description="{desc}")] = None'
                )

        # --- B. Process Flattened Body Fields ---
        for flat_key, meta in flat_schema.items():
            sanitized = flat_key.replace("-", "_")
            desc_raw = (
                meta.get("description")
                or (meta.get("raw_schema") or {}).get("description")
                or "Body field"
            )
            desc = escape_string(desc_raw.strip())

            raw_type = meta.get("type") or (meta.get("raw_schema") or {}).get(
                "type", "string"
            )
            py_type = TYPE_MAP.get(raw_type, "str")

            param_map[sanitized] = {
                "orig_name": flat_key,
                "location": "body_flat",
                "type": py_type,
            }

            if meta.get("required"):
                required_args.append(
                    f'{sanitized}: Annotated[{py_type}, Field(description="{desc}")]'
                )
            else:
                optional_args.append(
                    f'{sanitized}: Annotated[{py_type}, Field(description="{desc}")] = None'
                )

        # --- C. Build Docstring ---
        top_desc = clean_description_text(t.get("description", ""))
        context_notes = build_collapsed_parent_notes(resolved_schema, flat_schema)
        docstring = escape_string(top_desc + context_notes)

        # --- D. Generate Function Code  ---
        args_sig = ", ".join(required_args + optional_args)

        func_code = f'''
async def {tool_name}({args_sig}):
    """
    {docstring}
    """
    from oracle.oci_db_dynamic_mcp_server.server import invoke_oci_api, unflatten_payload
    args = locals()
    params = {{}}
    flat_body = {{}}
    path = "{t.get('path', '')}"
    for sanitized, info in param_map.items():
        val = args.get(sanitized)
        if val is None: continue
        # Remove 'args' from locals if it exists to avoid polluting param map
        if sanitized == "args": continue

        if info["location"] == "body_flat":
            flat_body[info["orig_name"]] = val
        else:
            placeholder = "{{" + info['orig_name'] + "}}"
            if placeholder in path:
                path = path.replace(placeholder, str(val))
            else:
                params[info['orig_name']] = val
    payload = unflatten_payload(flat_body, flat_schema)
    return invoke_oci_api(
        method="{t.get('method', 'GET')}", 
        path=path, 
        params=params, 
        payload=payload
    )
'''
        exec_globals = {
            "Annotated": Annotated,
            "Field": Field,
            "List": List,
            "Dict": Dict,
            "Any": Any,
            "Optional": Optional,
            "param_map": param_map,
            "flat_schema": flat_schema,
        }

        try:
            exec(func_code, exec_globals)
            tool_func = exec_globals[tool_name]
            mcp.tool(tool_func)
        except Exception as e:
            print(f"Failed to register tool {tool_name}: {e}")


def main():
    register_tools()
    print("Server running...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
else:
    register_tools()
