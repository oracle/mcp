# Shared engineering context

This document routes existing monorepo engineering sources. It introduces no required skill bundle, agent harness or new application policy. Root instructions remain in [AGENTS.md](../AGENTS.md); native READMEs, manifests, command definitions and local guides provide their owning details.

## Start here

1. Identify the requested change and owning package/shared library. Read [root instructions](../AGENTS.md) and any applicable nested guide before editing, including when following a direct source link.
2. Find the package README, implementation/interfaces, manifest and tests. Use [BEST_PRACTICES](../BEST_PRACTICES.md) for shared server requirements and [Common's README](../src/common/README.md) for Python authentication contracts. Compute is a structure/model/test reference, with a legacy-auth gap.
3. Read the relevant command sources in the validation map. Separate setup, build, package tests, aggregate coverage and runtime checks; they provide different evidence.
4. Assess interfaces/consumers, contribution requirements and local gaps before expanding a change. [CONTRIBUTING](../CONTRIBUTING.md) owns issue, signoff and PR guidance; root owns changelog rules. [SECURITY](../SECURITY.md) owns vulnerability reporting, not every runtime security constraint.
5. Report source inference and actual checks separately using the evidence routes below. A local gap does not authorize removing shared requirements or performing an unrelated migration.

## Selected component context

The user-approved expansion covers every MCP server component under `src/`: 34 server guides, including the Java toolkit, plus the existing Common library guide and root guidance. Each guide supplies the nine-area engineering profile through local answers, specific shared/native references or explicit gaps. A guide’s existence does not establish server quality or passing behavior evaluation. The [adoption summary](plans/adopt-monorepo-agent-context/adoption-summary.md) separates the original ten-case evaluation from the expanded documentation review.

| Scope | Native entry | Local guide |
| --- | --- | --- |
| Common shared library | [README](../src/common/README.md), [exports](../src/common/oracle_mcp_common/__init__.py) | [Common guide](../src/common/AGENTS.md) |
| `dbtools-mcp-server` | [README](../src/dbtools-mcp-server/README.md), [entry point](../src/dbtools-mcp-server/dbtools-mcp-server.py) | [Guide](../src/dbtools-mcp-server/AGENTS.md) |
| `mysql-mcp-server` | [README](../src/mysql-mcp-server/README.md), [entry point](../src/mysql-mcp-server/oracle/mysql_mcp_server/server.py) | [Guide](../src/mysql-mcp-server/AGENTS.md) |
| `oci-api-mcp-server` | [README](../src/oci-api-mcp-server/README.md), [entry point](../src/oci-api-mcp-server/oracle/oci_api_mcp_server/server.py) | [Guide](../src/oci-api-mcp-server/AGENTS.md) |
| `oci-cloud-guard-mcp-server` | [README](../src/oci-cloud-guard-mcp-server/README.md), [entry point](../src/oci-cloud-guard-mcp-server/oracle/oci_cloud_guard_mcp_server/server.py) | [Guide](../src/oci-cloud-guard-mcp-server/AGENTS.md) |
| `oci-cloud-mcp-server` | [README](../src/oci-cloud-mcp-server/README.md), [entry point](../src/oci-cloud-mcp-server/oracle/oci_cloud_mcp_server/server.py) | [Guide](../src/oci-cloud-mcp-server/AGENTS.md) |
| `oci-compute-instance-agent-mcp-server` | [README](../src/oci-compute-instance-agent-mcp-server/README.md), [entry point](../src/oci-compute-instance-agent-mcp-server/oracle/oci_compute_instance_agent_mcp_server/server.py) | [Guide](../src/oci-compute-instance-agent-mcp-server/AGENTS.md) |
| `oci-compute-mcp-server` | [README](../src/oci-compute-mcp-server/README.md), [entry point](../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/server.py) | [Guide](../src/oci-compute-mcp-server/AGENTS.md) |
| `oci-database-mcp-server` | [README](../src/oci-database-mcp-server/README.md), [entry point](../src/oci-database-mcp-server/oracle/oci_database_mcp_server/server.py) | [Guide](../src/oci-database-mcp-server/AGENTS.md) |
| `oci-db-observability-mcp-server` | [README](../src/oci-db-observability-mcp-server/README.md), [entry point](../src/oci-db-observability-mcp-server/oracle/oci_db_observability_mcp_server/server.py) | [Guide](../src/oci-db-observability-mcp-server/AGENTS.md) |
| `oci-document-understanding-mcp-server` | [README](../src/oci-document-understanding-mcp-server/README.md), [entry point](../src/oci-document-understanding-mcp-server/oracle/oci_document_understanding_mcp_server/server.py) | [Guide](../src/oci-document-understanding-mcp-server/AGENTS.md) |
| `oci-faaas-mcp-server` | [README](../src/oci-faaas-mcp-server/README.md), [entry point](../src/oci-faaas-mcp-server/oracle/oci_faaas_mcp_server/server.py) | [Guide](../src/oci-faaas-mcp-server/AGENTS.md) |
| `oci-full-stack-disaster-recovery-mcp-server` | [README](../src/oci-full-stack-disaster-recovery-mcp-server/README.md), [entry point](../src/oci-full-stack-disaster-recovery-mcp-server/oracle/oci_fsdr_mcp_server/server.py) | [Guide](../src/oci-full-stack-disaster-recovery-mcp-server/AGENTS.md) |
| `oci-identity-mcp-server` | [README](../src/oci-identity-mcp-server/README.md), [entry point](../src/oci-identity-mcp-server/oracle/oci_identity_mcp_server/server.py) | [Guide](../src/oci-identity-mcp-server/AGENTS.md) |
| `oci-iot-mcp-server` | [README](../src/oci-iot-mcp-server/README.md), [entry point](../src/oci-iot-mcp-server/oracle/oci_iot_mcp_server/server.py) | [Guide](../src/oci-iot-mcp-server/AGENTS.md) |
| `oci-javascript-mcp-server` | [README](../src/oci-javascript-mcp-server/README.md), [entry point](../src/oci-javascript-mcp-server/src/server.ts) | [Guide](../src/oci-javascript-mcp-server/AGENTS.md) |
| `oci-limits-mcp-server` | [README](../src/oci-limits-mcp-server/README.md), [entry point](../src/oci-limits-mcp-server/oracle/oci_limits_mcp_server/server.py) | [Guide](../src/oci-limits-mcp-server/AGENTS.md) |
| `oci-load-balancer-mcp-server` | [README](../src/oci-load-balancer-mcp-server/README.md), [entry point](../src/oci-load-balancer-mcp-server/oracle/oci_load_balancer_mcp_server/server.py) | [Guide](../src/oci-load-balancer-mcp-server/AGENTS.md) |
| `oci-logging-mcp-server` | [README](../src/oci-logging-mcp-server/README.md), [entry point](../src/oci-logging-mcp-server/oracle/oci_logging_mcp_server/server.py) | [Guide](../src/oci-logging-mcp-server/AGENTS.md) |
| `oci-migration-mcp-server` | [README](../src/oci-migration-mcp-server/README.md), [entry point](../src/oci-migration-mcp-server/oracle/oci_migration_mcp_server/server.py) | [Guide](../src/oci-migration-mcp-server/AGENTS.md) |
| `oci-monitoring-mcp-server` | [README](../src/oci-monitoring-mcp-server/README.md), [entry point](../src/oci-monitoring-mcp-server/oracle/oci_monitoring_mcp_server/server.py) | [Guide](../src/oci-monitoring-mcp-server/AGENTS.md) |
| `oci-network-load-balancer-mcp-server` | [README](../src/oci-network-load-balancer-mcp-server/README.md), [entry point](../src/oci-network-load-balancer-mcp-server/oracle/oci_network_load_balancer_mcp_server/server.py) | [Guide](../src/oci-network-load-balancer-mcp-server/AGENTS.md) |
| `oci-networking-mcp-server` | [README](../src/oci-networking-mcp-server/README.md), [entry point](../src/oci-networking-mcp-server/oracle/oci_networking_mcp_server/server.py) | [Guide](../src/oci-networking-mcp-server/AGENTS.md) |
| `oci-object-storage-mcp-server` | [README](../src/oci-object-storage-mcp-server/README.md), [entry point](../src/oci-object-storage-mcp-server/oracle/oci_object_storage_mcp_server/server.py) | [Guide](../src/oci-object-storage-mcp-server/AGENTS.md) |
| `oci-opensearch-mcp-server` | [README](../src/oci-opensearch-mcp-server/README.md), [entry point](../src/oci-opensearch-mcp-server/oracle/oci_opensearch_mcp_server/server.py) | [Guide](../src/oci-opensearch-mcp-server/AGENTS.md) |
| `oci-pricing-mcp-server` | [README](../src/oci-pricing-mcp-server/README.md), [entry point](../src/oci-pricing-mcp-server/oci-pricing-mcp-server.py) | [Guide](../src/oci-pricing-mcp-server/AGENTS.md) |
| `oci-recovery-mcp-server` | [README](../src/oci-recovery-mcp-server/README.md), [entry point](../src/oci-recovery-mcp-server/oracle/oci_recovery_mcp_server/server.py) | [Guide](../src/oci-recovery-mcp-server/AGENTS.md) |
| `oci-registry-mcp-server` | [README](../src/oci-registry-mcp-server/README.md), [entry point](../src/oci-registry-mcp-server/oracle/oci_registry_mcp_server/server.py) | [Guide](../src/oci-registry-mcp-server/AGENTS.md) |
| `oci-resource-search-mcp-server` | [README](../src/oci-resource-search-mcp-server/README.md), [entry point](../src/oci-resource-search-mcp-server/oracle/oci_resource_search_mcp_server/server.py) | [Guide](../src/oci-resource-search-mcp-server/AGENTS.md) |
| `oci-support-mcp-server` | [README](../src/oci-support-mcp-server/README.md), [entry point](../src/oci-support-mcp-server/oracle/oci_support_mcp_server/server.py) | [Guide](../src/oci-support-mcp-server/AGENTS.md) |
| `oci-usage-mcp-server` | [README](../src/oci-usage-mcp-server/README.md), [entry point](../src/oci-usage-mcp-server/oracle/oci_usage_mcp_server/server.py) | [Guide](../src/oci-usage-mcp-server/AGENTS.md) |
| `oracle-data-studio-mcp-server` | [README](../src/oracle-data-studio-mcp-server/README.md), [entry point](../src/oracle-data-studio-mcp-server/oracle/data_studio_mcp_server/server.py) | [Guide](../src/oracle-data-studio-mcp-server/AGENTS.md) |
| `oracle-db-doc-mcp-server` | [README](../src/oracle-db-doc-mcp-server/README.md), [entry point](../src/oracle-db-doc-mcp-server/oracle-db-doc-mcp-server.py) | [Guide](../src/oracle-db-doc-mcp-server/AGENTS.md) |
| `oracle-db-mcp-java-toolkit` | [README](../src/oracle-db-mcp-java-toolkit/README.md), [entry point](../src/oracle-db-mcp-java-toolkit/src/main/java/com/oracle/database/mcptoolkit/OracleDatabaseMCPToolkit.java) | [Guide](../src/oracle-db-mcp-java-toolkit/AGENTS.md) |
| `oracle-goldengate-mcp-server` | [README](../src/oracle-goldengate-mcp-server/README.md), [entry point](../src/oracle-goldengate-mcp-server/oracle/oracle_goldengate_mcp_server/server.py) | [Guide](../src/oracle-goldengate-mcp-server/AGENTS.md) |

## Validation map

These commands are **source-verified**, not executed results. Choose the setup/checks appropriate to the change. Documentation-only changes need path/link, command-source, scope/instruction and diff review; running a server or installing dependencies is unnecessary for those checks.

| Scope | Working directory | Existing setup/build/check routes |
| --- | --- | --- |
| Common | Repository root | `proto install` for pinned tools; `moon run common:build` for packaging; `moon run common:test` for package tests |
| Compute | Repository root | `proto install`; `moon run oci-compute-mcp-server:build`; `moon run oci-compute-mcp-server:test` |
| Cloud | Repository root | `proto install`; `moon run oci-cloud-mcp-server:build`; `moon run oci-cloud-mcp-server:test` |
| Other Moon-managed Python servers | Repository root | `proto install`; `moon run <directory-name>:build` and `moon run <directory-name>:test`, with exact targets in local guides. Python minima, dependencies and thresholds come from each manifest; check package-specific test/live prerequisites. |
| Moon-excluded Python servers | Owning package directory | [DBTools](../src/dbtools-mcp-server/AGENTS.md), [MySQL](../src/mysql-mcp-server/AGENTS.md), [Pricing](../src/oci-pricing-mcp-server/AGENTS.md) and [DB Doc](../src/oracle-db-doc-mcp-server/AGENTS.md) own native routes and explicit gaps. Do not substitute a nonexistent Moon package task. |
| Python source/shared behavior | Repository root | `moon run root:lint` after Python source changes; shared changes require `moon run :test` then `moon run root:combine-coverage`. Package-only checks do not establish shared coverage. Root README gives broader lock/install/type/build gates. |
| JavaScript | Repository root | `proto install`; `moon run oci-javascript-mcp-server:compile`, `moon run oci-javascript-mcp-server:test`, `moon run oci-javascript-mcp-server:check`, `moon run oci-javascript-mcp-server:build`. Moon installs locked npm dependencies; test/check/build depend on compile. Native npm scripts expose startup only. |
| Java toolkit | `src/oracle-db-mcp-java-toolkit` | JDK 17+, Maven 3.9+ per README; `mvn clean package`. Check actual test discovery/reports when executed; no configured 90% enforcement is established. |
| Documentation only | Repository root | Resolve changed links/anchors and source paths, compare command definitions, review scope/instructions and run `git diff --check`. Report these separately from server quality. |

Command sources: [Moon Python tasks](../.moon/tasks/python.yml), [root tasks](../moon.yml), [JavaScript tasks](../src/oci-javascript-mcp-server/moon.yml), [workspace discovery](../.moon/workspace.yml), [toolchains](../.moon/toolchains.yml), [tool pins](../.prototools) and native manifests. Python locks/manifests define each environment; direct `uv sync --directory src/<package> --locked --all-extras --dev` is also a source-backed setup route. Do not silently upgrade dependencies while synchronizing an existing environment.

### Check scope and coverage

- `moon run <package>:test` runs the inherited Python package test task and writes `.coverage.<package>` plus its HTML report. It does not run aggregate coverage.
- `moon run :test` selects test tasks across discovered projects, including JavaScript. `moon run root:combine-coverage` separately combines Python workspace reports and enforces a 90% aggregate threshold; it does not combine JavaScript or Java coverage. Check which reports belong to the current run rather than inferring consumer coverage from stale files or one package's success.
- [Workspace discovery](../.moon/workspace.yml) excludes dbtools, MySQL, Pricing, DB Doc and the Java toolkit. Follow each excluded package's native validation route; exclusion does not waive quality requirements. Java has no discovered Moon project. JavaScript owns explicit package tasks, with generated protobuf bindings compiled before tests, type checks or packaging.
- Python package manifests configure their own thresholds; root requires at least 90% for server quality checks. JavaScript c8 enforces 90% **line** coverage with explicit exclusions. Java's POM provides no JaCoCo enforcement; build success or zero discovered tests is insufficient evidence.
- Server startup, OCI operations, database access and real Podman deployment are distinct from mocked unit checks. Use each native README for runtime setup; this adoption performs none of those operations.

## Known gaps

These observations describe application sources at `52ea016` and the approved documentation expansion from `838d82b`; recheck implementation and instruction identities for a later engineering task. Local guides record additional package-specific differences. They do not approve exceptions or prove compliance.

| Area | Observed source difference or evidence limit | Relevant sources |
| --- | --- | --- |
| Common consumers | API, Cloud, Database, DB Observability and Document Understanding declare Common; only the first three have explicit package Moon dependency edges | [Common guide](../src/common/AGENTS.md#architecture-and-dependencies), consumer manifests/Moon files; inspect declarations, graph edges and call sites separately |
| Common package requirements | README lists OCI SDK 2.179.0+ and optional FastMCP 3.4.2; manifest declares OCI 2.185.0+ and FastMCP `>=3.2.4,<4.0.0` | [README](../src/common/README.md#package-requirements), [manifest](../src/common/pyproject.toml); use manifest for install definitions and flag the discrepancy |
| Compute auth | Client/HTTP helpers resolve credentials locally; manifest has no Common dependency | [server](../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/server.py), [manifest](../src/oci-compute-mcp-server/pyproject.toml); root Common requirement remains applicable |
| JavaScript subprocess policy | Existing Podman provider invokes a process, while root names API alone as a subprocess exception | [provider](../src/oci-javascript-mcp-server/src/isolation/podman.ts), [root quality rules](../AGENTS.md#mcp-server-quality-validation); record conflict without authorizing another backend/exception |
| JavaScript isolation evidence | Fake-control-plane tests cover protocol and command construction; shared-kernel containers are not VM boundaries | [README security/development](../src/oci-javascript-mcp-server/README.md), [tests](../src/oci-javascript-mcp-server/test); real deployment isolation not established |
| Java validation | JUnit dependency exists; no explicit Surefire pin or JaCoCo coverage enforcement; discovery/results unexecuted here | [POM](../src/oracle-db-mcp-java-toolkit/pom.xml), [tests](../src/oracle-db-mcp-java-toolkit/src/test/java/com/oracle/database/mcptoolkit) |
| Ownership and coverage | Guides describe technical scope, not a verified named-maintainer roster; all current server components and Common have guides, while other repository directories are outside this component pass | [contribution process](../CONTRIBUTING.md), [adoption summary](plans/adopt-monorepo-agent-context/adoption-summary.md) |
| Wider OCI auth adoption | Many SDK-backed servers still construct credentials locally. IoT/OpenSearch also have token-failure fallback behavior that differs from Common; a local implementation is not a shared-policy exception | [All server guides](#selected-component-context), especially [IoT](../src/oci-iot-mcp-server/AGENTS.md) and [OpenSearch](../src/oci-opensearch-mcp-server/AGENTS.md); root/Common requirements remain authoritative |
| DB Observability setup | README development instructions use removed Make tooling; manifest OCI 2.182.1 conflicts with Common OCI >=2.185.0 | [DB Observability guide](../src/oci-db-observability-mcp-server/AGENTS.md), native manifests and inherited Moon tasks; dependency remediation is separate work |
| Data Studio coverage | Native manifest sets 75%, below the root 90% server-quality requirement | [Data Studio guide](../src/oracle-data-studio-mcp-server/AGENTS.md), manifest and unit definitions; no threshold changed or coverage executed |
| Excluded Python validation | DBTools has live OCI tests; MySQL lacks a native test/coverage procedure; Pricing mixes mocks/network and has a console-package layout gap; DB Doc lacks tests and references absent requirements.txt | [DBTools](../src/dbtools-mcp-server/AGENTS.md), [MySQL](../src/mysql-mcp-server/AGENTS.md), [Pricing](../src/oci-pricing-mcp-server/AGENTS.md), [DB Doc](../src/oracle-db-doc-mcp-server/AGENTS.md); each guide records prerequisites and limits |
| Native/source mismatches | Instance Agent and Usage README tool tables differ from registration; Recovery README claims Common use while implementation resolves credentials locally | [Instance Agent](../src/oci-compute-instance-agent-mcp-server/AGENTS.md), [Usage](../src/oci-usage-mcp-server/AGENTS.md), [Recovery](../src/oci-recovery-mcp-server/AGENTS.md); inspect current native sources before edits |

## Evidence and context routes

| Read when | Context | Depends on | Evidence |
| --- | --- | --- | --- |
| **Know:** Investigating implementation, constraints or shared/local differences | [Server and library native entries](#selected-component-context), [Common contract](../src/common/README.md), [quality guidance](../BEST_PRACTICES.md) | Root and applicable local instructions, target manifest | Owning implementation/test definitions; [known gaps](#known-gaps) |
| **Do:** Selecting setup/build/validation | [Validation map](#validation-map) | Runtime/toolchain and native command definitions | Actual exit status, test discovery, current-run coverage and blocked-check reports in the owning change |
| **Now:** Reviewing this adoption | [Design](plans/adopt-monorepo-agent-context/design.md), [implementation plan](plans/adopt-monorepo-agent-context/implementation-plan.md) | [Pinned reuse assessment](plans/adopt-monorepo-agent-context/reuse-assessment.md) | [Adoption summary](plans/adopt-monorepo-agent-context/adoption-summary.md) |
| **Proof:** Interpreting an engineering completion claim | Owning tests and native run reports; this pass's [summary](plans/adopt-monorepo-agent-context/adoption-summary.md) | Source/guidance identity, exact command/directory and scope | Label source-verified, executed/pass, executed/fail, or unverified; distinguish retrieval/structural review from runtime behavior |

Keep long contracts/procedures in their owning docs and executable definitions. Guides provide orientation and task mappings. This root bundle covers all current server components and Common; other repository directories are not independently claimed as component-guide scopes. No Done/archive directory or evidence placeholder is required. The original guide revision has a separately recorded ten-case read-only evaluation. This expansion launches no additional trial; file/link checks do not establish effective agent use for the newly added guides.
