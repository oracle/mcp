import asyncio
import importlib


def test_import_and_list_tools():
    mod = importlib.import_module("mcp_atlassian_oauth.server")
    assert hasattr(mod, "server"), "server instance not found"

    # list_tools is the coroutine function registered via decorator; it remains directly callable
    assert hasattr(mod, "list_tools"), "list_tools coroutine not found"

    tools = asyncio.run(mod.list_tools())
    names = {t.name for t in tools}
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
    assert expected.issubset(names), f"Missing tools: {expected - names}"
