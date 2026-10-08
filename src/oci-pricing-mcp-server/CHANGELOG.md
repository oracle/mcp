# Changelog

## Unreleased

### Security

- Updated locked PyJWT to 2.15.1; updated `cryptography` to 50.0.1 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247); updated the FastMCP dependency and lockfile to 3.4.5; updated locked AnyIO to 4.15.1.

## 0.1.5

### Changed

- Updated dependency locks for FastMCP 3.4.4 and refreshed transitive packages.
