# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0: https://oss.oracle.com/licenses/upl.

import re
import subprocess
import sys
import tomllib
from decimal import Decimal
from pathlib import Path

import cedarpy


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, check=True)
    return result.stdout.decode("utf-8")


def coverage_floor(source: str) -> int:
    manifest = tomllib.loads(source, parse_float=Decimal)
    try:
        value = manifest["tool"]["coverage"]["report"]["fail_under"]
    except (KeyError, TypeError):
        raise ValueError("missing tool.coverage.report.fail_under") from None
    if type(value) not in (int, Decimal):
        raise ValueError("fail_under must be a number")
    if not Decimal(value).is_finite() or not 0 <= value <= 100:
        raise ValueError("fail_under must be finite and between 0 and 100")
    # Preserve the >= 90 boundary exactly, including decimals just below 90.
    return int(value)


def main() -> None:
    if len(sys.argv) != 3:
        raise ValueError("usage: check.py BASE_COMMIT CANDIDATE_COMMIT (from repo root)")
    base, candidate = sys.argv[1:]
    for revision in (base, candidate):
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
            raise ValueError("expected full, existing commit IDs")
        if git("rev-parse", "--verify", f"{revision}^{{commit}}").strip() != revision:
            raise ValueError("expected full, existing commit IDs")
    if git("rev-parse", "--show-prefix").strip():
        raise ValueError("run from the repository root")

    # Load only the approved verifier's siblings, never the candidate's policy files.
    policy_dir = Path(__file__).resolve().parent
    schema = cedarpy.Schema.from_str((policy_dir / "schema.cedarschema").read_text(encoding="utf-8"))
    source = (policy_dir / "coverage.cedar").read_text(encoding="utf-8")
    validation = cedarpy.validate_policies(source, schema)
    if not validation.validation_passed or validation.errors:
        raise ValueError(f"Cedar policy failed schema validation: {validation.errors}")
    policies = cedarpy.PolicySet.from_str(source)

    changed = git(
        "diff",
        "--name-only",
        "-z",
        "--no-renames",
        "--no-ext-diff",
        "--no-textconv",
        base,
        candidate,
        "--",
        "src/",
    )
    checked = 0
    for path in filter(None, changed.split("\0")):
        parts = path.split("/")
        if len(parts) != 3 or parts[1] == "common" or parts[2] != "pyproject.toml":
            continue
        # Read Git objects, never candidate imports, tests, or symlink targets.
        entry = git("ls-tree", "-z", candidate, "--", f":(literal){path}")
        fields = entry.split("\t", 1)[0].split()
        if len(fields) != 3 or fields[0] not in ("100644", "100755") or fields[1] != "blob":
            raise ValueError(f"{path!r}: manifest is missing or is not a regular file")
        try:
            floor = coverage_floor(git("cat-file", "blob", fields[2]))
        except (ValueError, TypeError) as error:
            raise ValueError(f"{path!r}: {error}") from error
        request = {
            "principal": {"type": "Repository::Check", "id": "coverage"},
            "action": {"type": "Repository::Action", "id": "acceptManifest"},
            "resource": {"type": "Repository::Manifest", "id": path},
            "context": {"coverageFloor": floor},
        }
        response = cedarpy.is_authorized(request, policies, [], schema=schema)
        if response.diagnostics.errors:
            raise ValueError(f"{path!r}: Cedar evaluation error: {response.diagnostics.errors}")
        if response.decision != cedarpy.Decision.Allow:
            raise ValueError(f"{path!r}: denied by python-server-coverage-floor ({floor}%)")
        print(f"PASS {path!r}: coverage floor {floor}%")
        checked += 1
    print(f"PASS base={base} candidate={candidate}: checked {checked} changed server manifests")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Escape candidate-controlled text, including GitHub workflow command syntax.
        print(f"DENY: {error!r}", file=sys.stderr)
        sys.exit(1)
