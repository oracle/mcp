# Changelog

## Unreleased

### Breaking Changes

- `list_services`, `list_limit_definitions`, and `list_limit_value` now return an object with `items` and `next_page` instead of a bare list, enabling repeated pagination resumes.

### Fixed

- List tools now stop at the total requested `limit` and request only the remaining item count on subsequent OCI pages. An unset limit still collects all pages; an explicit page still fetches only one page.

### Security

- Updated `cryptography` to 50.0.1 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247).

## 1.0.5

### Changed

- Excluded development artifacts, local configuration, and container build files from source-distribution packages.

## 1.0.4

### Changed

- Updated dependency locks for FastMCP 3.4.5, OCI SDK 2.182.1, and refreshed authentication-related transitive packages.
