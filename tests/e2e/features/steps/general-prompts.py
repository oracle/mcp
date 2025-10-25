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
        raise ConnectionError(
            f"Could not connect to Ollama or model not found: {e}. Is Ollama running?"
        )


@when('I send a request with the prompt "{prompt}"')
def step_impl_prompt(context, prompt):
    # Send a request to the bridge (which is configured to talk to Ollama)
    payload = {
        "model": context.model,
        "options": {"temperature": 0.7, "top_p": 0.9},
        "messages": [context.system_message, {"role": "user", "content": prompt}],
        "stream": False,
        "thinking": True,
    }

    context.response = requests.post(context.url, json=payload, stream=False)
    context.response.raise_for_status()

    # check if all thinking is really done...
    result = context.response.json()
    thinking = result["message"]["thinking"]
    content = result["message"]["content"]
    print("thinking & content", thinking, content, flush=True)
    if content is None and thinking is not None:
        print("Getting the next response...")
        context.response = requests.post(context.url, json=payload, stream=False)
        context.response.raise_for_status()


@then("the response should contain a list of tools available")
def step_impl_tools_available(context):
    result = context.response.json()
    print("available tools", result)
    assert "content" in result["message"], "Response does not contain a content key."

    for tool_server in context.mcp_servers:
        assert (
            tool_server in result["message"]["content"]
        ), f"{tool_server} is missing from tools."


@then("the response should contain a list of instances")
def step_impl_list_instances(context):
    result = context.response.json()
    print("Instances", result)
    assert "content" in result["message"], "Response does not contain a content key."
    assert (
        "ocid1.instance" in result["message"]["content"]
    ), "tools could not be queried."
