# Changelog

## Unreleased

### Security

- Require `dnspython>=2.9.2` and `opentelemetry-api>=1.45.2` to address CVE-2026-128089 and CVE-2026-126360, respectively.

## 0.1.6

### Fixed

- Resolve Price List pagination `next` hrefs against the current page URL so query-relative and path-relative links stay on the API path. Off-host destinations are still rejected.

### Security

- Updated locked PyJWT to 2.15.1; updated `cryptography` to 50.0.2 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247); updated the FastMCP dependency and lockfile to 3.4.10; updated locked AnyIO to 4.15.1.

## 0.1.5

### Changed

- Updated dependency locks for FastMCP 3.4.4 and refreshed transitive packages.
