# MCP Atlassian OAuth – URI Examples

Copy-paste examples demonstrating first-class resource URIs.

## Confluence

- Space listing (recent pages)
  - confluence://DOCS
  - confluence://DOCS?format=markdown
  - confluence://DOCS?format=json

- Specific page by title (URL-encode spaces and special characters)
  - confluence://DOCS/pages/Getting%20Started
  - confluence://DOCS/pages/Getting%20Started?format=markdown
  - confluence://DOCS/pages/Getting%20Started?format=storage
  - confluence://DOCS/pages/Getting%20Started?format=json

- Paging (space listing)
  - confluence://DOCS?limit=20

## Jira

- Project summary (recent issues)
  - jira://ENG
  - jira://ENG?format=markdown
  - jira://ENG?format=json
  - jira://ENG?limit=20

- Issues listing node (alias to project summary with list)
  - jira://ENG/issues

- Specific issue
  - jira://ENG/issues/ENG-12345
  - jira://ENG/issues/ENG-12345?format=markdown
  - jira://ENG/issues/ENG-12345?format=json

Notes
- Default content format for Confluence page reads is markdown.
- Default content format for Jira project/issue reads is markdown.
- Titles for Confluence pages must be URL-encoded in the URI.
