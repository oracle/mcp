# Changelog

## Unreleased

### Changed

- Updated the script, FastMCP launcher, and Alpine container to use FastMCP 4.2.2 from the package lockfile.

### Fixed

- Open a separate SQLite reader for each search so queries work in FastMCP's worker threads.
- Restored the FastMCP JSON launch path and documented locked local installation.

### Security

- Require dnspython 2.9.2 or later and Soup Sieve 4.0 or later.

## 1.0.5

### Security

- Updated locked AnyIO to 4.15.1 and SoupSieve to 2.9; updated locked PyJWT to 2.15.1; updated `cryptography` to 50.0.1 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247).

## 1.0.4

### Changed

- Updated the FastMCP dependency and lockfile to 3.4.5.
