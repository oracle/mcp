# Changelog

## Unreleased

## 0.1.6

### Fixed

- Resolve Price List pagination `next` hrefs against the current page URL so query-relative and path-relative links stay on the API path. Off-host destinations are still rejected.
- Reject well-formed but unknown currency codes (for example `ZZZ`) with `invalid-currency-format` in `pricing_get_sku` and `pricing_search_name`. Babel's `get_currency_name()` returns unknown codes unchanged, so every three-letter code passed validation and was sent to the Price List API.

### Security

- Updated locked PyJWT to 2.15.1; updated `cryptography` to 50.0.2 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247); updated the FastMCP dependency and lockfile to 3.4.10; updated locked AnyIO to 4.15.1.

## 0.1.5

### Changed

- Updated dependency locks for FastMCP 3.4.4 and refreshed transitive packages.
