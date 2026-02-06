import os
import sys
import re
import json
import asyncio
import logging
import requests
from typing import Any, Dict, List, Annotated, Optional, Tuple
from collections import defaultdict
from pydantic import Field
from pathlib import Path

from mcp.server.lowlevel import Server
import mcp.types as types
from mcp.server.stdio import stdio_server

import oci
from oci.auth.signers import security_token_signer

from .dynamic_tools_loader import build_tools_from_latest_spec

# ---------------- LOGGING SETUP ----------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("oci-server")

# ---------------- CONFIGURATION ----------------
TYPE_MAP = {
    "integer": "int",
    "boolean": "bool",
    "number": "float",
    "array": "list",
    "object": "dict",
    "string": "str",
}

CONFIG_PATH = Path.home() / ".oci_mcp_config.json"

# ---------------- HELPERS ----------------
def clean_description_text(text: str) -> str:
    if not text: return ""
    text = re.sub(r"(?i)^Parameters\s*$", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"(?m)^\s*`[^`]+`.*$", "", text)
    return text.strip().replace('"', "'")

def escape_string(s: str) -> str:
    if not s: return ""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

def unflatten_payload(flat_input: dict, flat_schema: dict):
    root = {}
    for flat_key, meta in flat_schema.items():
        if flat_key not in flat_input: continue
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

# Synchronous worker function for OCI calls
def _invoke_oci_sync(method, path, params=None, payload=None):
    try:
        config = oci.config.from_file(
            profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
        )

        if "security_token_file" in config:
            with open(config["security_token_file"], "r") as f:
                security_token = f.read().strip()

            signer = security_token_signer.SecurityTokenSigner(
                token=security_token,
                private_key=oci.signer.load_private_key_from_file(
                    config["key_file"], pass_phrase=config.get("pass_phrase")
                ),
            )
            endpoint = f"https://database.{config['region']}.oraclecloud.com/20160918/"

            headers = {
                "Content-Type": "application/json",
                "authorization": f"Bearer {security_token}",
                "User-Agent": "oci-database-mcp-server"
            }

            url = endpoint.rstrip("/") + "/" + path.lstrip("/")

            response = requests.request(
                method=method.upper(), url=url, headers=headers, json=payload, params=params, auth=signer
            )
        else:
            signer = oci.signer.Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=config.get("pass_phrase")
            )
            endpoint = f"https://database.{config['region']}.oraclecloud.com/20160918/"
            url = endpoint.rstrip("/") + "/" + path.lstrip("/")

            response = requests.request(
                method=method.upper(), url=url, json=payload, params=params, auth=signer
            )

        if response.status_code >= 400:
            return {"error": True, "status": response.status_code, "body": response.text}

        try:
            return response.json()
        except:
            return response.text

    except Exception as e:
        logger.error(f"OCI API Error: {e}")
        return {"error": True, "system": str(e)}

# Async wrapper
async def invoke_oci_api(method, path, params=None, payload=None):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _invoke_oci_sync, method, path, params, payload)

# ---------------- TOOL MANAGER ----------------
class ToolManager:
    def __init__(self):
        self.registry = defaultdict(list)
        self.compiled_functions = {}
        self.active_resources = self._load_state()
        self._load_and_compile()

    def _load_state(self) -> set:
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r") as f:
                    data = json.load(f)
                    logger.info(f"Loaded config from {CONFIG_PATH}")
                    return set(data.get("enabled", []))
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                return set()
        return set()

    def _save_state(self):
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump({"enabled": list(self.active_resources)}, f)
            logger.info(f"Saved state to {CONFIG_PATH}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _load_and_compile(self):
        logger.info("Fetching OCI specs...")
        try:
            raw_tools = build_tools_from_latest_spec()
        except Exception as e:
            logger.error(f"Failed to build tools: {e}")
            return

        for t in raw_tools:
            tool_name = t["name"]
            resource = t.get("resource", "Unknown")
            self.registry[resource].append(t)

            if resource in self.active_resources:
                func = self._generate_function_code(t)
                if func:
                    self.compiled_functions[tool_name] = func

        logger.info(f"Compiled {len(self.compiled_functions)} tools across {len(self.registry)} resources.")

    def _generate_function_code(self, t: Dict[str, Any]):
        flat_schema = t.get("flatSchema", {})
        param_map = {}
        required_args = []
        optional_args = []

        # 1. Params
        for p in t.get("parameters", []):
            pname = p.get("name")
            sanitized = pname.replace("-", "_")
            desc = escape_string(p.get("description", "").strip())
            py_type = TYPE_MAP.get(p.get("type"), "str")
            param_map[sanitized] = {"orig_name": pname, "location": p.get("in", "query")}

            field_def = f'Annotated[{py_type}, Field(description="{desc}")]'
            if p.get("required"):
                required_args.append(f"{sanitized}: {field_def}")
            else:
                optional_args.append(f"{sanitized}: {field_def} = None")

        # 2. Body
        for flat_key, meta in flat_schema.items():
            sanitized = flat_key.replace("-", "_")
            desc = escape_string((meta.get("description") or "Body field").strip())
            py_type = TYPE_MAP.get(meta.get("type"), "str")
            param_map[sanitized] = {"orig_name": flat_key, "location": "body_flat"}

            field_def = f'Annotated[{py_type}, Field(description="{desc}")]'
            if meta.get("required"):
                required_args.append(f"{sanitized}: {field_def}")
            else:
                optional_args.append(f"{sanitized}: {field_def} = None")

        args_sig = ", ".join(required_args + optional_args)
        docstring = clean_description_text(t.get("description", ""))

        # Function Template
        func_code = f'''
async def {t['name']}({args_sig}):
    """
    {docstring}
    """
    args = locals()
    params = {{}}
    flat_body = {{}}
    path = "{t.get('path', '')}"
    
    for sanitized, info in param_map.items():
        val = args.get(sanitized)
        if val is None: continue
        if sanitized == "args": continue

        if info["location"] == "body_flat":
            flat_body[info["orig_name"]] = val
        else:
            placeholder = "{{{{{{{{ + info['orig_name'] + "}}}}}}}}" 
            placeholder_search = "{{" + info['orig_name'] + "}}"
            if placeholder_search in path:
                path = path.replace(placeholder_search, str(val))
            else:
                params[info['orig_name']] = val

    payload = unflatten_payload(flat_body, flat_schema)
    
    return await invoke_oci_api(
        method="{t.get('method', 'GET')}", 
        path=path, 
        params=params, 
        payload=payload
    )
'''
        exec_globals = {
            "Annotated": Annotated, "Field": Field,
            "List": List, "Dict": Dict, "Optional": Optional,
            "param_map": param_map, "flat_schema": flat_schema,
            "invoke_oci_api": invoke_oci_api, "unflatten_payload": unflatten_payload
        }

        try:
            exec(func_code, exec_globals)
            return exec_globals[t['name']]
        except Exception as e:
            logger.warning(f"Failed to compile {t['name']}: {e}")
            return None

    def tool_store_logic(self, enable: List[str] = None, disable: List[str] = None, clear: bool = False) -> Tuple[str, bool]:
        enable = enable or []
        disable = disable or []

        resource_map = {k.lower(): k for k in self.registry.keys()}
        status_msgs = []
        state_changed = False

        if clear:
            if self.active_resources:
                self.active_resources.clear()
                self.compiled_functions.clear()
                state_changed = True
                status_msgs.append("Cleared all active resources.")

        for r in disable:
            k = resource_map.get(str(r).lower())
            if k and k in self.active_resources:
                self.active_resources.remove(k)
                for t in self.registry[k]:
                    if t["name"] in self.compiled_functions:
                        del self.compiled_functions[t["name"]]
                state_changed = True
                status_msgs.append(f"Disabled: {k}")

        for r in enable:
            k = resource_map.get(str(r).lower())
            if k and k not in self.active_resources:
                self.active_resources.add(k)
                for t in self.registry[k]:
                    func = self._generate_function_code(t)
                    if func:
                        self.compiled_functions[t["name"]] = func
                state_changed = True
                status_msgs.append(f"Enabled: {k}")

        if state_changed:
            self._save_state()
            status_msgs.append("Configuration saved.")
        else:
            status_msgs.append("No changes made.")

        current_list = f"\nCurrent Active Resources: {sorted(list(self.active_resources))}"
        return ( "\n".join(status_msgs) + current_list, state_changed )

    def get_doc(self):
        lines = []
        for r, tools in sorted(self.registry.items()):
            tool_names = ", ".join(t["name"] for t in tools)
            lines.append(f"{{resourceName: \"{r}\", tools: \"{tool_names}\"}}")
        return "\n".join(lines)

# ---------------- SERVER IMPLEMENTATION ----------------

manager = ToolManager()
server = Server("oci-dynamic-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    tools = []

    tools.append(types.Tool(
        name="tool_store",
        description=f"Manage OCI tools availability.\nUse this to Enable, Disable or Clear resources.\n\nAVAILABLE RESOURCES:\n\n{manager.get_doc()}",
        inputSchema={
            "type": "object",
            "properties": {
                "enable": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of EXACT resource names to ENABLE (e.g. ['dbSystems', 'vmClusters'])"
                },
                "disable": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of resource names to DISABLE"
                },
                "clear": {
                    "type": "boolean",
                    "description": "If true, removes ALL currently enabled resources before applying new changes."
                }
            }
        }
    ))

    def to_json_type(py_type):
        mapping = {
            "str": "string", "int": "integer", "float": "number",
            "bool": "boolean", "list": "array", "dict": "object"
        }
        return mapping.get(str(py_type).lower(), "string")

    for resource in manager.active_resources:
        for t in manager.registry.get(resource, []):
            properties = {}
            required_fields = []

            for p in t.get("parameters", []):
                sanitized = p.get("name", "").replace("-", "_")
                if not sanitized: continue
                properties[sanitized] = {
                    "type": to_json_type(p.get("type")),
                    "description": (p.get("description") or "")[:200]
                }
                if p.get("required"): required_fields.append(sanitized)

            for flat_key, meta in t.get("flatSchema", {}).items():
                sanitized = flat_key.replace("-", "_")
                raw_type = meta.get("type")
                if not raw_type and meta.get("raw_schema"):
                    raw_type = meta["raw_schema"].get("type")

                properties[sanitized] = {
                    "type": to_json_type(raw_type),
                    "description": (meta.get("description") or "Body param")[:200]
                }
                if meta.get("required"): required_fields.append(sanitized)

            tools.append(types.Tool(
                name=t["name"],
                description=(t.get("description") or "")[:1024],
                inputSchema={
                    "type": "object",
                    "properties": properties,
                    "required": required_fields
                }
            ))

    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    arguments = arguments or {}

    try:
        if name == "tool_store":
            (result, isChanged) = manager.tool_store_logic(
                enable=arguments.get("enable"),
                disable=arguments.get("disable"),
                clear=arguments.get("clear", False)
            )

            # NOTE: We still send this notification. Even if Cline ignores it,
            # other clients might use it to auto-refresh.
            if isChanged:
                await server.request_context.session.send_tool_list_changed()
                result += "\n\nChanges saved! Please manually REFRESH the tool list in your client to see the new tools."

            return [types.TextContent(type="text", text=result)]

        func = manager.compiled_functions.get(name)
        if func:
            res = await func(**arguments)
            return [types.TextContent(type="text", text=json.dumps(res, indent=2))]

        raise ValueError(f"Tool {name} not found")

    except Exception as e:
        logger.error(f"Error executing {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

# ---------------- ENTRY POINT ----------------

async def run_server():
    options = server.create_initialization_options()
    options.capabilities.tools = types.ToolsCapability(listChanged=True)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)

def main():
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()