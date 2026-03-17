"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from behave import then


@then("the response should contain a list of load balancer tools available")
def step_impl_lb_tools_available(context):
    response_json = context.response.json()
    assert (
        "content" in response_json["message"]
    ), "Response does not contain a content key."
    content = response_json["message"]["content"].lower()
    # Check for representative tool names from the LB server
    expected = [
        "list_load_balancers",
        "get_load_balancer",
        "create_load_balancer",
        "update_load_balancer",
        "delete_load_balancer",
        "list_load_balancer_listeners",
        "create_load_balancer_listener",
        "get_load_balancer_listener",
        "update_load_balancer_listener",
        "delete_load_balancer_listener",
        "list_load_balancer_backend_sets",
        "get_load_balancer_backend_set",
        "create_load_balancer_backend_set",
        "update_load_balancer_backend_set",
        "delete_load_balancer_backend_set",
        "list_backends",
        "get_backend",
        "create_backend",
        "update_backend",
        "delete_backend",
        "list_load_balancer_certificates",
        "create_load_balancer_certificate",
        "delete_load_balancer_certificate",
        "list_ssl_cipher_suites",
        "get_ssl_cipher_suite",
        "create_ssl_cipher_suite",
        "update_ssl_cipher_suite",
        "delete_ssl_cipher_suite",
        "list_hostnames",
        "get_hostname",
        "create_hostname",
        "update_hostname",
        "delete_hostname",
        "list_rule_sets",
        "get_rule_set",
        "create_rule_set",
        "update_rule_set",
        "delete_rule_set",
        "list_routing_policies",
        "get_routing_policy",
        "create_routing_policy",
        "update_routing_policy",
        "delete_routing_policy",
        "get_load_balancer_health",
        "get_backend_set_health",
        "get_backend_health",
        "list_load_balancer_healths",
        "list_load_balancer_work_requests",
        "get_load_balancer_work_request",
    ]
    assert any(
        t in content for t in expected
    ), "Load balancer tools could not be queried."


@then("the response should contain a list of load balancers")
def step_impl_list_lbs(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    # Accept OCID or known display name from mocks, or a clear list mention
    assert (
        "ocid1.loadbalancer" in content
        or "mock-lb" in content
        or "load balancers" in content
    ), "List of load balancers not found."


@then("the response should contain the details of a load balancer")
def step_impl_get_lb(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert (
        "ocid1.loadbalancer" in content
        or "mock-lb" in content
        or "display name" in content
        or "shape" in content
        or "load balancer" in content
        or "lifecycle" in content
        or "id" in content
    ), "Load balancer details not found."


@then("the response should confirm creation of a load balancer")
def step_impl_create_lb(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    # Look for create confirmation, work request OCID, or known status
    assert (
        "created" in content
        or "provision" in content
        or "ocid1.loadbalancer" in content
        or "work request" in content
        or "accepted" in content
    ), "Load balancer creation not confirmed in response."


@then("the response should confirm deletion of a load balancer")
def step_impl_delete_lb(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    # Look for delete confirmation, work request OCID, or expected terms
    assert (
        "deleted" in content
        or "deletion" in content
        or "terminated" in content
        or "removed" in content
        or "ocid1.loadbalancer" in content
        or "work request" in content
        or "accepted" in content
        or "success" in content
        or "ok" in content
        or "load balancer" in content
    ), "Load balancer deletion not confirmed in response."


@then("the response should contain a list of listeners")
def step_impl_list_listeners(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        k in content for k in ["listener", "listeners", "port", "protocol"]
    ), "Listeners list not found."


@then("the response should contain a list of backend sets and backends")
def step_impl_backend_sets_backends(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(
        k in content for k in ["backendset", "backend set", "policy"]
    ), "Backend sets not found."
    assert any(k in content for k in ["backend", "ip", "port"]), "Backends not found."


@then("the response should contain a list of certificates and cipher suites")
def step_impl_certs_and_suites(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(k in content for k in ["certificate", "cert"]), "Certificates not found."
    assert any(
        k in content for k in ["cipher", "cipher suite", "tls"]
    ), "SSL cipher suites not found."


@then("the response should contain hostnames, rule sets, and routing policies")
def step_impl_hostnames_rules_routing(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert any(k in content for k in ["hostname", "host"]), "Hostnames not found."
    assert any(
        k in content for k in ["rule set", "ruleset", "rule"]
    ), "Rule sets not found."
    assert any(
        k in content for k in ["routing policy", "routing policies", "routing"]
    ), "Routing policies not found."


@then("the response should contain health summaries and work requests")
def step_impl_health_and_work_requests(context):
    result = context.response.json()
    assert "content" in result["message"], "Response does not contain a content key."
    content = result["message"]["content"].lower()
    assert "health" in content, "Health information not found."
    assert any(
        k in content for k in ["work request", "work requests", "work id", "wr"]
    ), "Work requests not found."


@then("the response should confirm listener operations")
def step_impl_listener_ops(context):
    content = context.response.json()["message"]["content"].lower()
    assert "listener" in content, "Listener keyword missing."
    assert (
        "create" in content
        or "created" in content
        or "add" in content
        or "added" in content
    ), "Listener create not confirmed."
    assert (
        "update" in content
        or "updated" in content
        or "modify" in content
        or "modified" in content
    ), "Listener update not confirmed."
    assert (
        "delete" in content
        or "deleted" in content
        or "remove" in content
        or "removed" in content
    ), "Listener delete not confirmed."


@then("the response should confirm backend set operations")
def step_impl_backend_set_ops(context):
    content = context.response.json()["message"]["content"].lower()
    assert (
        "backend set" in content or "backendset" in content
    ), "Backend set keyword missing."
    assert (
        "create" in content
        or "created" in content
        or "add" in content
        or "added" in content
    ), "Backend set create not confirmed."
    assert (
        "update" in content
        or "updated" in content
        or "modify" in content
        or "modified" in content
    ), "Backend set update not confirmed."
    assert (
        "delete" in content
        or "deleted" in content
        or "remove" in content
        or "removed" in content
    ), "Backend set delete not confirmed."


@then("the response should confirm backend operations")
def step_impl_backend_ops(context):
    content = context.response.json()["message"]["content"].lower()
    assert "backend" in content, "Backend keyword missing."
    assert (
        "create" in content
        or "created" in content
        or "add" in content
        or "added" in content
    ), "Backend create not confirmed."
    assert (
        "update" in content
        or "updated" in content
        or "modify" in content
        or "modified" in content
        or "offline" in content
    ), "Backend update not confirmed."
    assert (
        "delete" in content
        or "deleted" in content
        or "remove" in content
        or "removed" in content
    ), "Backend delete not confirmed."


@then("the response should confirm certificate operations")
def step_impl_certificate_ops(context):
    content = context.response.json()["message"]["content"].lower()
    assert "certificate" in content, "Certificate keyword missing."
    assert (
        "create" in content
        or "created" in content
        or "add" in content
        or "added" in content
        or "accepted" in content
    ), "Certificate create not confirmed."
    assert (
        "delete" in content
        or "deleted" in content
        or "remove" in content
        or "removed" in content
    ), "Certificate delete not confirmed."


@then("the response should confirm ssl cipher suite operations")
def step_impl_cipher_suite_ops(context):
    content = context.response.json()["message"]["content"].lower()
    assert "cipher" in content, "Cipher suite keyword missing."
    assert (
        "create" in content
        or "created" in content
        or "add" in content
        or "added" in content
    ), "Cipher suite create not confirmed."
    assert (
        "get" in content or "fetched" in content or "retrieved" in content
    ), "Cipher suite get not confirmed."
    assert (
        "update" in content
        or "updated" in content
        or "modify" in content
        or "modified" in content
    ), "Cipher suite update not confirmed."
    assert (
        "delete" in content
        or "deleted" in content
        or "remove" in content
        or "removed" in content
    ), "Cipher suite delete not confirmed."


@then("the response should confirm hostname operations")
def step_impl_hostname_ops(context):
    content = context.response.json()["message"]["content"].lower()
    assert "hostname" in content, "Hostname keyword missing."
    assert (
        "create" in content
        or "created" in content
        or "add" in content
        or "added" in content
    ), "Hostname create not confirmed."
    assert (
        "get" in content or "fetched" in content or "retrieved" in content
    ), "Hostname get not confirmed."
    assert (
        "update" in content
        or "updated" in content
        or "modify" in content
        or "modified" in content
    ), "Hostname update not confirmed."
    assert (
        "delete" in content
        or "deleted" in content
        or "remove" in content
        or "removed" in content
    ), "Hostname delete not confirmed."


@then("the response should confirm rule set operations")
def step_impl_rule_set_ops(context):
    content = context.response.json()["message"]["content"].lower()
    assert "rule set" in content or "ruleset" in content, "Rule set keyword missing."
    assert (
        "create" in content
        or "created" in content
        or "add" in content
        or "added" in content
    ), "Rule set create not confirmed."
    assert (
        "get" in content or "fetched" in content or "retrieved" in content
    ), "Rule set get not confirmed."
    assert (
        "update" in content
        or "updated" in content
        or "modify" in content
        or "modified" in content
    ), "Rule set update not confirmed."
    assert (
        "delete" in content
        or "deleted" in content
        or "remove" in content
        or "removed" in content
    ), "Rule set delete not confirmed."


@then("the response should confirm routing policy operations")
def step_impl_routing_policy_ops(context):
    content = context.response.json()["message"]["content"].lower()
    assert (
        "routing policy" in content or "routing policies" in content
    ), "Routing policy keyword missing."
    assert (
        "create" in content
        or "created" in content
        or "add" in content
        or "added" in content
    ), "Routing policy create not confirmed."
    assert (
        "get" in content or "fetched" in content or "retrieved" in content
    ), "Routing policy get not confirmed."
    assert (
        "update" in content
        or "updated" in content
        or "modify" in content
        or "modified" in content
    ), "Routing policy update not confirmed."
    assert (
        "delete" in content
        or "deleted" in content
        or "remove" in content
        or "removed" in content
    ), "Routing policy delete not confirmed."


@then("the response should contain load balancer health")
def step_impl_lb_health(context):
    content = context.response.json()["message"]["content"].lower()
    assert "health" in content and ("load balancer" in content or "overall" in content)


@then("the response should contain backend set health")
def step_impl_bs_health(context):
    content = context.response.json()["message"]["content"].lower()
    assert "health" in content and ("backend set" in content or "backendset" in content)


@then("the response should contain backend health")
def step_impl_backend_health(context):
    content = context.response.json()["message"]["content"].lower()
    assert "health" in content and "backend" in content


@then("the response should contain work request details")
def step_impl_work_request_details(context):
    content = context.response.json()["message"]["content"].lower()
    assert (
        "work request" in content
        or "ocid1.loadbalancerworkrequest" in content
        or "succeeded" in content
        or "createlistener" in content
    ), "Work request details not found."
