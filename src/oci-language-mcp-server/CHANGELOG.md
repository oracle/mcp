# Changelog

All notable changes are documented here. Versions follow Semantic Versioning.

## Unreleased

### Security

- Restrict tool-selected regions to recognized OCI region identifiers, disable OCI SDK request
  logging, and prevent unauthenticated local HTTP listeners in the container image.

### Fixed

- Preserve OCI PII REMOVE output formatting, reconcile malformed batch response keys, and support
  `chars_to_consider=0`.
- Construct OCI Language clients from the current authentication context for every request.
- Make the container healthcheck transport-aware.
- Build the production container without development workspace sources and document the
  repository-standard Podman image workflow.
- Make the shared container target resolve package metadata without an undeclared tool.

### Added

- Initial generic OCI Language MCP server.
- Seven atomic shared-pretrained tools for language detection, text classification, NER, key
  phrases, sentiment analysis, PII processing, and synchronous text translation.
- API-aligned action-oriented tool identifiers with human-readable MCP titles, exposed by
  the generic `oci-language-mcp` server identity.
- Stdio and hardened Streamable HTTP transports.
- OAuth resource-server mode, OCI workload identities, bounded execution, payload-safe
  telemetry, typed results, packaging, container, registry metadata, and public documentation.
- Bounded, safely quoted, domain-oriented human output for NER, key phrases, and detailed
  sentiment while retaining complete typed `structuredContent`.
- Correct non-authentication OCI 4xx classification, domain-specific failure headlines,
  PII exclusion disclosure, and sanitized `RELEXIFY` operational errors.

### Changed

- Use the shared `oracle-mcp-common` authentication context for outbound OCI Language clients.
- Document every supported runtime configuration and clarify the separate inbound and outbound
  authentication models.
- Make the container's prepared Python environment safe for non-root, read-only runtime use.
