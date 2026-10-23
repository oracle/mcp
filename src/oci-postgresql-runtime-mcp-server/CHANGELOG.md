# Changelog

## Unreleased

### Breaking Changes

- Schema and table discovery now returns one bounded page by default. Follow `next_cursor` while `has_more` is true to retrieve the remaining objects. `count` reports the returned page size.

### Added

- Stateless continuation for metadata discovery, bounded page sizes, metadata timeouts and response-size limits.
- OS-keyring and environment references for database passwords, with explicit source selection and sanitized configuration errors.

### Changed

- Example profiles reference OS-keyring entries instead of including literal passwords.
