"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import requests
from behave import given, then, when


@given("the MCP server is running with OCI tools")
def step_impl(context):
    assert context.bridge_proc.poll() is None, "Process is not running!!"


@given("the ollama model with the tools is properly working")
def step_impl_ollama_model(context):
    try:
        # Check if ollama is running and has the model
        response = requests.get("http://localhost:8000/health")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Could not connect to Ollama or model not found: {e}. Is Ollama running?")


@when('I send a request with the prompt "{prompt}"')
def step_impl_prompt(context, prompt):
    payload = {
        "model": context.model,
        "options": {
            "temperature": 0.0,
            "top_p": 1.0,
        },  # Use 0.0 to make responses more deterministic
        "messages": [context.system_message, {"role": "user", "content": prompt}],
        "stream": False,
    }

    try:
        # Timeout to prevent infinite hanging
        response = requests.post(context.url, json=payload, timeout=90)
        response.raise_for_status()
        context.response = response

        result = response.json()

        message = result.get("message", {})
        content = message.get("content", "")

        print(f"Response received: {content[:50]}...")

    except requests.exceptions.Timeout:
        print("Error: The Bridge or Ollama timed out")
        raise


@then("the response should contain a list of tools available")
def step_impl_tools_available(context):
    result = context.response.json()
    print("available tools", result)
    assert "content" in result["message"], "Response does not contain a content key."

    for tool_server in context.mcp_servers:
        assert tool_server in result["message"]["content"], f"{tool_server} is missing from tools."
