# Changelog

## Unreleased

### Security

- Updated locked AnyIO to 4.15.1 and SoupSieve to 2.9; updated locked PyJWT to 2.15.1; updated `cryptography` to 50.0.1 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247).

## 1.0.4

### Changed

- Updated the FastMCP dependency and lockfile to 3.4.5.
