# Changelog

## Unreleased

### Security

- Updated `cryptography` to 50.0.1 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247).

### Changed

- Updated the FastMCP dependency and lockfile to 3.4.5.

## 0.1.5

### Changed

- Updated dependency locks for FastMCP 3.4.4 and refreshed transitive packages.
