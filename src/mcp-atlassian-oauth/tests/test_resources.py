import asyncio
import json
import types

from mcp_atlassian_oauth.jira import resources as jira_res
from mcp_atlassian_oauth.jira import api as jira_api
from mcp_atlassian_oauth.confluence import resources as conf_res
from mcp_atlassian_oauth.confluence import api as conf_api


def test_jira_list_resources_project_root(monkeypatch):
    # Mock Jira search_issues to return two issues
    def fake_search_issues(jql, fields=None, max_results=50, start_at=0):
        payload = {
            "issues": [
                {"key": "ENG-1", "fields": {"summary": "First issue"}},
                {"key": "ENG-2", "fields": {"summary": "Second issue"}},
            ]
        }
        return 200, "application/json", json.dumps(payload).encode("utf-8")

    monkeypatch.setattr(jira_api, "search_issues", fake_search_issues, raising=True)

    uri = "jira://ENG"
    res = asyncio.run(jira_res.list_resources(uri))
    uris = [str(r.uri) for r in res]
    # Should include project root, issues listing, and individual issue URIs
    assert "jira://ENG" in uris
    assert "jira://ENG/issues" in uris
    assert "jira://ENG/issues/ENG-1" in uris
    assert "jira://ENG/issues/ENG-2" in uris


def test_jira_read_issue_markdown(monkeypatch):
    # Mock get_issue to return minimal JSON
    def fake_get_issue(issue_key, expand=None, fields=None):
        payload = {
            "key": issue_key,
            "fields": {
                "summary": "Demo summary",
                "status": {"name": "To Do"},
                "assignee": {"displayName": "Alice"},
                "description": "Some description"
            }
        }
        return 200, "application/json", json.dumps(payload).encode("utf-8")

    monkeypatch.setattr(jira_api, "get_issue", fake_get_issue, raising=True)

    uri = "jira://ENG/issues/ENG-123"
    contents = asyncio.run(jira_res.read_resource(uri))
    assert contents, "Expected non-empty contents"
    text = contents[0].text
    assert "# ENG-123 Demo summary" in text
    assert "Status: To Do" in text
    assert "Assignee: Alice" in text
    assert "Some description" in text


def test_confluence_list_resources_space_root(monkeypatch):
    # Mock CQL search to return two pages
    def fake_cql_search(cql, limit=25, start=0):
        payload = {
            "results": [
                {"content": {"id": "100", "title": "Getting Started"}},
                {"content": {"id": "101", "title": "Release Notes"}},
            ]
        }
        return 200, "application/json", json.dumps(payload).encode("utf-8")

    monkeypatch.setattr(conf_api, "cql_search", fake_cql_search, raising=True)

    uri = "confluence://DOCS"
    res = asyncio.run(conf_res.list_resources(uri))
    uris = [str(r.uri) for r in res]
    assert "confluence://DOCS" in uris
    assert "confluence://DOCS/pages" in uris
    # Titles must be URL-encoded
    assert "confluence://DOCS/pages/Getting%20Started" in uris
    assert "confluence://DOCS/pages/Release%20Notes" in uris


def test_confluence_read_page_markdown(monkeypatch):
    # 1) CQL search to resolve page id by title
    def fake_cql_search(cql, limit=1, start=0):
        payload = {"results": [{"content": {"id": "200", "title": "Getting Started"}}]}
        return 200, "application/json", json.dumps(payload).encode("utf-8")

    # 2) get_page returns storage and view bodies
    def fake_get_page(page_id, expand=None):
        payload = {
            "id": page_id,
            "title": "Getting Started",
            "body": {
                "view": {"value": "<h1>Welcome</h1><p>Intro paragraph</p>"},
                "storage": {"value": "<h1>Welcome</h1><p>Intro paragraph</p>"},
            },
        }
        return 200, "application/json", json.dumps(payload).encode("utf-8")

    monkeypatch.setattr(conf_api, "cql_search", fake_cql_search, raising=True)
    monkeypatch.setattr(conf_api, "get_page", fake_get_page, raising=True)

    uri = "confluence://DOCS/pages/Getting%20Started"
    contents = asyncio.run(conf_res.read_resource(uri))
    assert contents, "Expected non-empty contents"
    text = contents[0].text
    assert text.startswith("# Getting Started"), "Title header missing"
    assert "Welcome" in text
    assert "Intro paragraph" in text
