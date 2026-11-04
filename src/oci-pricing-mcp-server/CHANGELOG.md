# Changelog

## Unreleased

### Changed

- Package and install the server as `oracle.oci-pricing-mcp-server`, with the canonical command of the same name. The old `oci-pricing-mcp` command and standalone script remain compatibility launchers for one release; the script now requires the installed package. Python 3.11 remains supported.
- Replace `Dockerfile` with `Containerfile`; install locked production dependencies and run the installed command directly as a non-root user.
- Add Pricing to Moon validation with offline unit tests and enforced branch coverage; move live public API probes to an explicitly enabled integration suite.

### Fixed

- Correct the missing package layout and console entry point so wheel and source distributions include the server implementation and can be installed outside the checkout.

## 0.1.6

### Fixed

- Resolve Price List pagination `next` hrefs against the current page URL so query-relative and path-relative links stay on the API path. Off-host destinations are still rejected.

### Security

- Updated locked PyJWT to 2.15.1; updated `cryptography` to 50.0.2 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247); updated the FastMCP dependency and lockfile to 3.4.10; updated locked AnyIO to 4.15.1.

## 0.1.5

### Changed

- Updated dependency locks for FastMCP 3.4.4 and refreshed transitive packages.
