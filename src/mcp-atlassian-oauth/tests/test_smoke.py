import importlib


def test_tools_registry_contains_expected():
    mod = importlib.import_module("mcp_atlassian_oauth.http")
    assert hasattr(mod, "TOOLS"), "TOOLS registry not found on http"
    tools = getattr(mod, "TOOLS")
    names = {t.get("name") for t in tools}
    expected = {
        "jira_get_myself",
        "jira_search_issues",
        "jira_get_issue",
        "jira_add_comment",
        "jira_find_similar",
        "conf_get_server_info",
        "conf_get_page",
        "conf_search_cql",
    }
    missing = expected - names
    assert not missing, f"Missing tools: {missing}"
