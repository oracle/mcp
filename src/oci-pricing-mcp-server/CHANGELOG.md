# Changelog

## Unreleased

### Breaking Changes

- Install the server as `oracle.oci-pricing-mcp-server` and migrate MCP clients that launch the old Python script to the installed command of the same name. The `oci-pricing-mcp` command remains an alias for one release.

### Changed

- Upgrade the stdio runtime to FastMCP 4.2.2. Tool discovery now includes FastMCP-generated display titles.
- Replace `Dockerfile` with an Oracle Linux 9 / Python 3.13 `Containerfile`. The image installs Pricing as a non-editable package and starts it offline as `oracle` with UID `10001`, matching the previous image. The package continues to support Python 3.11.
- Add Pricing to Moon validation with offline unit tests and enforced branch coverage; move live public API probes to an explicitly enabled integration suite.

### Fixed

- Correct the missing package layout and console entry point so wheel and source distributions include the server implementation and can be installed outside the checkout.

### Security

- Require dnspython 2.9.2 or later and lock it to 2.9.2.

## 0.1.6

### Fixed

- Resolve Price List pagination `next` hrefs against the current page URL so query-relative and path-relative links stay on the API path. Off-host destinations are still rejected.

### Security

- Updated locked PyJWT to 2.15.1; updated `cryptography` to 50.0.2 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247); updated the FastMCP dependency and lockfile to 3.4.10; updated locked AnyIO to 4.15.1.

## 0.1.5

### Changed

- Updated dependency locks for FastMCP 3.4.4 and refreshed transitive packages.
