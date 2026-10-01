# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Security

- Updated `cryptography` to 50.0.1 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247).

## 1.0.1

### Fixed

- Excluded generated coverage reports, local development artifacts, and the dependency lockfile from source distributions to produce stable publishable archives.

## 1.0.0

### Changed

- Updated dependency locks for FastMCP 3.4.5, OCI SDK 2.182.1, and refreshed authentication-related transitive packages.

## 0.2.1

### Fixed

- API-key and security-token OCI clients now send the canonical telemetry user agent.
