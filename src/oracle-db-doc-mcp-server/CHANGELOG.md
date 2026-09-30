# Changelog

## Unreleased

### Security

- Updated `cryptography` to 50.0.1 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247).

## 1.0.4

### Changed

- Updated the FastMCP dependency and lockfile to 3.4.5.
