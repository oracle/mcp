# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 3.0.0

Credential handling moves onto the shared `oracle-mcp-common` library end to end, and
the server gains two new guidance tools.

### Breaking Changes

- **New `oracle-mcp-common` dependency, used for every authentication mode.**
  `session`/`apikey` credentials now come from `oracle_mcp_common.build_auth_context()`,
  and the HTTP transport builds its OAuth provider with
  `oracle_mcp_common.build_idcs_http_auth()` and mints every request's OCI signer with
  that policy's `IDCSHttpAuth.context_for()`. The server-local profile resolution,
  signer construction, and `OCIProvider` wiring are gone, bringing this server onto the
  same authentication path as the other OCI MCP servers. Supported profile
  configurations are unchanged.
- **`ORACLE_MCP_AUTH_METHOD` is no longer needed and is no longer forced.** stdio
  credentials now come from `oracle-mcp-common`'s own resolution, which defaults to
  `auto`: session-token when the selected profile directly declares a
  `security_token_file`, API-key otherwise. 2.x always forced session-token unless the
  variable said `apikey`, so an API-key-only profile failed with "security_token_file
  must be declared directly in the selected OCI_CONFIG_PROFILE" until the variable was
  set. `ORACLE_MCP_AUTH_METHOD` and `ORACLE_MCP_AUTH_PROFILE` remain supported for
  existing configurations, including the unseparated `apikey` spelling; prefer
  `OCI_MCP_AUTH_TYPE` and `OCI_CONFIG_PROFILE`. When both names are set, the `OCI_*`
  one wins.
- **HTTP transport now requires `ORACLE_MCP_BASE_URL`.** Alongside the `IDCS_DOMAIN`,
  `IDCS_CLIENT_ID`, `IDCS_CLIENT_SECRET`, and `IDCS_AUDIENCE` settings 2.1.x already
  required, `oracle-mcp-common` validates all five before the listener starts, so a
  missing or malformed value now fails startup instead of surfacing later as a broken
  sign-in.
- **HTTP transport now requires `ORACLE_MCP_TENANCY_ID`.** Compartment and region
  discovery need a tenancy OCID and there is no local OCI config file to read one from
  on a hosted deployment. `TENANCY_ID_OVERRIDE` is accepted as a synonym.
- **OAuth state moved.** Client registrations and authorization state are now persisted
  by FastMCP under its home directory (`~/.fastmcp/oauth-proxy/`, relocatable with
  `FASTMCP_HOME`), encrypted at rest, with the token-signing key derived from the client
  secret so it is stable across restarts and workers without being configured.
  Deployments that mounted a `.oauth_state` directory must persist the new location
  instead; an ephemeral home directory forces clients to re-register after a restart.
- HTTP-mode UPST signers are no longer cached process-wide; a fresh signer is built for
  every tool call from the caller's own request-scoped token.

### Added

- **New `onboard_database_to_recovery_service` guidance tool** for non-destructive Cloud
  Protect onboarding assistance.
- **New `diagnose_recovery_service_issue` guidance tool.** Returns an evidence-driven,
  access-first diagnostic workflow for investigating Oracle Database backup, protection,
  and recoverability problems in a Recovery Service environment.
- Guidance text is now exposed as ordinary tools, so clients without prompt support can
  call it. This brings the tool count to 25.
- `list_protected_databases` now reports retention-lock status and Cloud-Protect-managed
  vs. Database-Service-managed classification.
- OCI requests now carry an `opc-request-id` stamped with opaque installation, caller,
  and tool markers, so a customer-reported call can be traced in service logs without
  identifying the user.
- **Every tool declares `readOnlyHint`.** The server never creates, updates, or deletes an
  OCI resource, and now says so in each tool's MCP annotations instead of only in the
  README, so a host can act on it. The three guidance tools additionally declare
  `openWorldHint: false`, since they return static text and never reach the network.
- **Summary scans report what they could not read.** `summarize_protected_database_redo_status`
  returns an `unknown` count for databases whose redo status could not be determined —
  most often because the caller cannot `GET` them. They were previously left out of every
  bucket, so a permissions gap looked like a clean bill of health. Both compartment-subtree
  summaries also stop at `ORACLE_MCP_TOOL_DEADLINE_SECONDS` (default 120) and set
  `truncated: true` rather than running until the client gives up.
- `ORACLE_MCP_STATE_DIR`, `ORACLE_MCP_TOOL_DEADLINE_SECONDS`, and
  `ORACLE_MCP_CACHE_MAX_ENTRIES` settings; the previously undocumented compartment cap,
  cache TTL, and log redaction variables are now in the README table as well.

### Changed

- Prompt text moved out of `server.py` into `oracle/oci_recovery_mcp_server/data/prompts/`.
- **CIMD client registration is disabled.** FastMCP enables Client ID Metadata Documents
  by default, which lets a client send an HTTPS URL as its `client_id` and requires this
  server to fetch that URL to learn the client's metadata. That fetch is an outbound
  request made with pinned DNS and redirects disabled, so it fails on a host with no
  egress, and also on one whose egress is a CONNECT proxy. The failure reached the user
  as "The client ID ... was not found in the server's client registry", which reads like
  a client bug. Clients now register with DCR against `/register`, which never leaves the
  host. Startup fails loudly if a future FastMCP release renames the private attribute
  this relies on.
- **Logs now live in `~/.oci-recovery-mcp/logs`, not in the install tree.** The default
  log directory was resolved relative to the package, which put it inside the virtualenv:
  read-only on a hardened deployment, and discarded with the environment on every `uvx`
  run, so the logs an operator is told to read did not survive the session. Override with
  `ORACLE_MCP_LOG_DIR` or `ORACLE_MCP_STATE_DIR`.
- **Tool results are logged as a shape summary at `INFO`, in full only at `DEBUG`.** A
  result is a tenancy's resource inventory; writing every one of them to disk was both a
  lot of volume and a lot of customer data at rest. Log files are also created `0600` now,
  on each rotation, so they are not readable by other users of the host.
- Updated dependency locks for FastMCP 3.4.5, OCI SDK 2.185.1,
  Cryptography 
  
  
  
  
  , and Pydantic 2.13.4.
- README now documents all supported environment variables and the hosted OAuth setup
  inline.

### Fixed

- **`list_restore` failed whenever `status`, `sort_by`, or `sort_order` was passed.** All
  three were advertised in the tool schema and forwarded straight into
  `oci.work_requests.WorkRequestClient.list_work_requests`, which accepts only
  `resource_id`, `limit`, `page`, and `opc_request_id` and raises `ValueError:
  list_work_requests got unknown kwargs` on anything else — so using any of them was a
  hard failure. They are now applied to the results instead, the same way the tool
  already filters to restore operations, and an invalid `sort_by`/`sort_order` is
  rejected with a message naming the accepted values.
- **`list_protection_policies` failed whenever `id` was passed.** The same class of
  defect: the SDK call names that filter `protection_policy_id` and rejects `id`. It is
  now sent under the name the SDK expects. `list_protected_databases` and
  `list_recovery_service_subnets` genuinely do accept `id`, and are unchanged.
- **One inaccessible compartment wiped protection-policy links for every database.**
  `list_databases` correlates each database to its protection policy by listing
  protected databases across the compartments in scope, and the whole loop sat inside a
  single `try` that reset the correlation map on any failure. A caller who cannot list
  protected databases in one compartment of a subtree — an ordinary 404
  `NotAuthorizedOrNotFound` in a large tenancy — therefore got `protectionPolicyId: null`
  for every database in every *readable* compartment too, which reads as "not protected"
  rather than "could not check". Each compartment is now scoped separately, partial
  results are kept, and skipped compartments are logged.
- **An unwritable log directory stopped the server from starting.** Logging is configured
  at import, and neither the directory creation nor the file handler was guarded, so a
  read-only filesystem, a directory owned by another user, or a full disk killed the
  process with a `PermissionError` traceback before startup could report anything. File
  logging is now best-effort: the server warns, names the path, and logs to stderr.
- **`get_recovery_service_metrics` interpolated caller input into its Monitoring query.**
  `metricName`, `resolution`, `aggregation`, and `protected_database_id` were concatenated
  into the MQL expression with no validation, despite the parameter docs promising fixed
  sets, and a quote in the database OCID could break out of the `resourceId` filter. All
  four are now validated against those sets before the query is built, and an invalid one
  is rejected with a message naming the accepted values.
- **The two summary tools advertised an output schema they did not return.** Both declared
  a counts model but returned a wrapper holding the aggregate, the per-compartment
  breakdown, and the compartments scanned, so any client trusting `outputSchema` was given
  the wrong contract. They now declare `ProtectedDatabaseHealthSummary` and
  `ProtectedDatabaseRedoSummary`, which describe what is actually sent. Wire field names
  are unchanged.
- **The in-process compartment cache grew without bound.** It expired entries by TTL but
  never removed them, and it is partitioned per tenancy and per caller — so a hosted
  deployment gained an entry, holding that caller's whole compartment listing, for every
  person who ever signed in. Entries are now swept on write and capped at
  `ORACLE_MCP_CACHE_MAX_ENTRIES` with least-recently-used eviction.
- **The in-process cache was not thread safe.** FastMCP runs synchronous tools in worker
  threads, so two tool calls reach the cache helpers at once, and both mutate rather than
  only read: the reader reinserts on a hit to maintain LRU order, and the writer sweeps
  expired entries and evicts. Concurrently that raises — `KeyError` when a reinsert races
  a sweep of the same key, `RuntimeError: dictionary keys changed during iteration` or
  `StopIteration` in the writer — surfacing as a failed tool call. Every mutation now runs
  under a module lock; the upstream OCI fetch stays outside it, so a slow Identity scan
  never serializes other tool calls.
- **Two of the four summary tools had no deadline.** `summarize_backup_space_used` reads a
  metric per protected database across every compartment in scope, and
  `summarize_protected_database_backup_destination` walks compartments, DB Homes and
  pages before making up to two more calls per database it finds -- the same unbounded
  fan-out the health and redo summaries were already budgeted for. Both now stop at
  `ORACLE_MCP_TOOL_DEADLINE_SECONDS` and report `truncated`, and the backup-space
  response distinguishes the compartments actually scanned (`compartmentIdsScanned`)
  from those in scope (`compartmentIdsInScope`), so a partial total is never presented
  as a whole-tenancy one.
- **The tenancy override did not read the name the shared library documents.**
  `oracle-mcp-common` reads `OCI_MCP_TENANCY_ID_OVERRIDE` and lists `ORACLE_MCP_TENANCY_ID`
  and `TENANCY_ID_OVERRIDE` as its legacy aliases; this server read only the aliases, so a
  deployment configured from the library's own documentation set a variable nothing here
  looked at and the HTTP transport failed to resolve a tenancy. All three are read now,
  canonical name first.
- **`check_recovery_service_limits` ignored `region` and fell back to `us-ashburn-1`.**
  The argument was accepted and discarded, and an unresolvable region silently became
  Ashburn -- so the tool reported one region's limits as another's. `region` is honored,
  the configured region is the fallback, and an unresolvable region now raises.
- **`summarize_protected_database_backup_destination`: four fixes.** `max_total_databases`
  broke out of the pagination loop only, so each further DB Home resumed appending past
  the cap. `has_backups_db_names` was declared, sorted and returned but never appended to,
  so it was empty on every response; it now names the databases a backup was returned for
  (and stays empty when `include_last_backup_time` is false, since no backup is queried
  then). The last-backup-time comparison was `str(t) > str(best)`, which orders a datetime
  below an ISO-8601 string of the same instant because `" " < "T"`; parsed instants are
  compared now. De-duplication ran at the end over `items` alone, leaving
  `total_databases`, `unconfigured_count` and `counts_by_destination_type` counting every
  occurrence, so the counts did not add up to the list beside them; the repeat is now
  skipped before anything counts it.
- **`fetch_regions_subscribed` described a parameter it does not have.** The tool
  description documented a `service` argument that is not in the signature, and annotated
  `tenancy_id` as a compartment OCID that scopes the search, which it is not and does not.
- **The compartment cache is now `cachetools.TTLCache` rather than a hand-rolled store.**
  The TTL sweep, the LRU ordering and the size bound were this server's code to get right
  and to test, and none of it was specific to this server. What is specific -- and what
  stays -- is the cache key: `cachetools.cached(key=...)` takes the partition function, so
  the tenancy and caller are still composed in one place. A failed Identity scan now raises
  out of the cached function instead of returning an empty list, because the decorator
  caches whatever is returned and a cached empty listing would have answered "you have no
  compartments" to every tool scoping through it for the rest of the TTL; the caller
  degrades to an empty list outside the cache, as before. Behaviour is otherwise unchanged,
  including both `ORACLE_MCP_COMPARTMENT_CACHE_TTL_SECONDS` and
  `ORACLE_MCP_CACHE_MAX_ENTRIES`.
- **Subscribed regions were cached across callers, answering an authorization question
  ahead of IAM.** Whether a caller may list a tenancy's region subscriptions is decided by
  their own OCI IAM policy, and the only place that decision is made is the IAM call
  itself. The cache was keyed by tenancy alone and consulted before that call, so on the
  HTTP transport a caller who had never held the permission read the list whenever another
  caller had warmed the entry, and a caller whose permission was revoked kept reading it
  until the entry expired — up to an hour by default. The cache is removed rather than
  partitioned: it served one thin tool and saved one IAM call per repeat invocation, which
  is not worth deciding authorization locally. `ORACLE_MCP_REGION_CACHE_TTL_SECONDS` is
  gone; a newly subscribed region also now appears immediately instead of up to an hour
  later. The key that let this happen was assembled at the call site, so it could leave the
  caller out; keys are now built in one place from a namespace the call site supplies, and
  the store cannot be reached with a key that skipped it.
- **HTTP deployments now refuse local profile credentials outright.** Credential selection
  was per request, so a call that somehow ran outside an authenticated request context
  would have been signed with the operator's own credentials instead of the caller's. When
  an HTTP authentication policy has been built, that path now raises rather than acting
  under the wrong identity.
- **Sign-in failed with `invalid_scope` because resource scopes were sent to IDCS
  unqualified.** IDCS names a resource application's scopes by concatenating the
  application's primary audience with the scope name, and `/authorize` accepts only that
  form, so `oci_mcp.recovery.invoke` was rejected and no login could complete. The access
  token IDCS issues carries the scope *bare*, though, and that token is re-validated on
  every request — so qualifying the configured value instead simply moved the failure to
  `401 invalid_token` on the first tool call. `IDCS_REQUIRED_SCOPES` is now bare, as
  verification requires, and the resource scopes advertised to clients are qualified with
  the audience. The two other paths that reach IDCS are qualified as well: the fallback
  used when a client sends no `scope` parameter at all, and the refresh request, which is
  built from the bare scopes stored on the refresh token and would otherwise have killed
  every session at its first refresh an hour after an apparently successful sign-in.
  Startup fails loudly if a future FastMCP release drops the hooks this relies on.
- **Compartment cache could serve one caller's compartments to another.** The compartment
  listing is fetched with `access_level="ACCESSIBLE"`, so it contains exactly what the
  calling identity may see, but it was cached per tenancy only. In a hosted deployment a
  broadly-permissioned user's compartment tree could be served to a restricted one. The
  cache is now keyed by tenancy **and** caller identity; over stdio, where the whole
  process shares one credential, the key is unchanged.
- Tenancy and region lookups now read the same OCI config file **and profile** the
  credentials were resolved from. The OCI SDK only falls back to `OCI_CONFIG_FILE` when
  `~/.oci/config` is absent, and this server resolved `ORACLE_MCP_AUTH_PROFILE` before
  `OCI_CONFIG_PROFILE` while the shared library resolves them in the opposite order, so
  these lookups could resolve a different profile than the request signer.
## Unreleased

### Security

- Updated `cryptography` to 50.0.1 to prevent PKCS#7 EnvelopedData decryption from exposing a Bleichenbacher oracle through distinguishable errors and timing (CVE-2026-69247).

## 2.1.2

### Changed

- Excluded development artifacts, local configuration, and container build files from source-distribution packages.

## 2.1.1

### Changed

- Updated dependency locks for FastMCP 3.4.5, OCI SDK 2.182.1, and refreshed authentication-related transitive packages.

## 2.1.0

### Added

- Added `list_restore` for retrieving database restore work requests, with filters, paging, and optional child-compartment aggregation.
- Added `check_recovery_service_limits` to report available protected-database backup storage and protected-database-count limits.
- Added `fetch_regions_subscribed` to list the tenancy's subscribed regions and their statuses.

### Changed

- Updated dependency locks for FastMCP 3.4.2, OCI SDK 2.179.0, and refreshed authentication-related transitive packages.
- Added optional child-compartment aggregation to existing compartment-scoped list and summary tools.
- Improved response models with explicit optional-field defaults and descriptions, including the new `WorkRequest` restore-job model.

## 2.0.0

### Breaking Changes

- HTTP transport now requires OCI IAM/IDCS authentication and no longer uses local OCI CLI profile credentials for request authentication.
- HTTP deployments must set `ORACLE_MCP_BASE_URL`, `OCI_REGION`, `IDCS_DOMAIN`, `IDCS_CLIENT_ID`, `IDCS_CLIENT_SECRET`, and `IDCS_AUDIENCE`, and register `${ORACLE_MCP_BASE_URL}/auth/callback`.
- The default required scopes are `openid profile email oci_mcp.recovery.invoke`; set `IDCS_REQUIRED_SCOPES` to override.
