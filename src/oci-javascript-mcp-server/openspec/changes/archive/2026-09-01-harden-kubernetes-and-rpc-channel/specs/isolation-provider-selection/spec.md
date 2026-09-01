## MODIFIED Requirements

### Requirement: Explicit assurance posture
The trusted provider descriptor and operator diagnostics SHALL identify the active provider and profile, credential mode, runtime policy, image policy, namespace topology, completed preflights, and unverified external controls without disclosing credentials, endpoints, raw Kubernetes errors, guest data, pod names, or resource details. Admission dry-run evidence SHALL be described only as `reviewed-variants-rejected` or `unverified`, not as general admission enforcement. A standard-runtime profile MUST NOT claim a per-execution VM boundary, and a Kata profile MUST NOT claim production approval solely from RuntimeClass lookup, reviewed-variant rejection, or pod creation.

#### Scenario: Standard profile descriptor
- **WHEN** either standard-runtime profile starts successfully
- **THEN** its descriptor SHALL report container isolation and the nested `isolated-vm` boundary
- **AND** it SHALL explicitly report that a Kata guest-kernel boundary was not requested or verified

#### Scenario: Kata profile descriptor
- **WHEN** `kata-in-cluster` starts successfully after exact RuntimeClass and admission-variant preflight
- **THEN** its descriptor SHALL record the selected RuntimeClass and handler and report only that reviewed variants were rejected
- **AND** it SHALL retain explicit unverified flags for real-node, guest-kernel, CRI, CNI, PID, overhead, provenance, and exact deployed admission-policy evidence

#### Scenario: Local admission gap
- **WHEN** `local-development` accepts a reviewed unsafe variant
- **THEN** its descriptor SHALL report admission preflight as `unverified`
- **AND** no operator diagnostic SHALL summarize the cluster admission path as enforced
