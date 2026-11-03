# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0: https://oss.oracle.com/licenses/upl.

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

POLICY_DIR = Path(__file__).resolve().parents[1]
MANIFEST = "src/sample-mcp-server/pyproject.toml"


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "--quiet")
        self.write(MANIFEST, "[tool.coverage.report]\nfail_under = 90\n")
        self.base = self.commit()

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.repo, capture_output=True, text=True, check=True
        ).stdout.strip()

    def write(self, path, source):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")

    def commit(self):
        self.git("add", ".")
        self.git(
            "-c",
            "user.name=Policy Test",
            "-c",
            "user.email=policy@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            f"core.hooksPath={os.devnull}",
            "commit",
            "--quiet",
            "--allow-empty",
            "-m",
            "fixture",
        )
        return self.git("rev-parse", "HEAD")

    def evaluate(self, candidate, verifier=POLICY_DIR / "check.py"):
        return subprocess.run(
            [sys.executable, "-I", str(verifier), self.base, candidate],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )

    def test_permits_integer_and_fractional_floors(self):
        for value in ("90", "90.5", "100"):
            with self.subTest(value=value):
                self.write(MANIFEST, f"# updated\n[tool.coverage.report]\nfail_under = {value}\n")
                result = self.evaluate(self.commit())
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("checked 1", result.stdout)

    def test_denies_low_missing_invalid_and_malformed_floors(self):
        sources = [
            f"[tool.coverage.report]\nfail_under = {value}"
            for value in ("89", "89.999999999999999999", "-1", "101", "nan", "inf", "true", "'90'")
        ] + [
            "[tool.coverage.report]",
            "[tool.coverage.report]\nfail_under = 90\nfail_under = 0",
            "[invalid",
        ]
        for source in sources:
            with self.subTest(source=source):
                self.write(MANIFEST, source)
                result = self.evaluate(self.commit())
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("DENY", result.stderr)

    def test_denies_manifest_deletion_and_rename_out_of_scope(self):
        (self.repo / MANIFEST).rename(self.repo / "removed.toml")
        self.assertNotEqual(self.evaluate(self.commit()).returncode, 0)
        (self.repo / "removed.toml").unlink()
        self.assertNotEqual(self.evaluate(self.commit()).returncode, 0)

    def test_checks_new_manifests_and_unusual_names(self):
        path = 'src/new\t\n"[server]/pyproject.toml'
        self.write(path, "[tool.coverage.report]\nfail_under = 90")
        result = self.evaluate(self.commit())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 2)
        self.write(path, "[tool.coverage.report]\nfail_under = 0")
        self.assertNotEqual(self.evaluate(self.commit()).returncode, 0)

    @unittest.skipUnless(os.name == "posix", "requires symlinks")
    def test_denies_symlink_even_when_its_text_is_valid_toml(self):
        (self.repo / MANIFEST).unlink()
        (self.repo / MANIFEST).symlink_to("[tool.coverage.report]\nfail_under = 90")
        self.assertNotEqual(self.evaluate(self.commit()).returncode, 0)

    def test_candidate_policy_code_and_worktree_cannot_authorize_themselves(self):
        self.write(MANIFEST, "[tool.coverage.report]\nfail_under = 0")
        self.write("policy/coverage.cedar", "permit(principal, action, resource);")
        self.write("policy/check.py", "raise SystemExit(0)")
        self.write("cedarpy.py", "raise SystemExit(0)")
        self.write("sitecustomize.py", "raise SystemExit(0)")
        candidate = self.commit()
        self.write(MANIFEST, "[tool.coverage.report]\nfail_under = 100")
        result = self.evaluate(candidate)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("python-server-coverage-floor", result.stderr)

    def test_rejects_invalid_or_missing_revisions(self):
        for candidate in ("HEAD", "--help", "0" * 40):
            with self.subTest(candidate=candidate):
                self.assertNotEqual(self.evaluate(candidate).returncode, 0)

    def test_unrelated_changes_do_not_audit_unchanged_packages_or_common(self):
        self.write("src/common/pyproject.toml", "[project]\nname = 'common'")
        self.write("README.md", "Documentation update\n")
        result = self.evaluate(self.commit())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("checked 0", result.stdout)

    def test_denies_invalid_trusted_policy_or_schema(self):
        # Simulate a broken approved verifier, separate from candidate-controlled files.
        with tempfile.TemporaryDirectory() as trusted:
            trusted = Path(trusted)
            for name in ("check.py", "coverage.cedar", "schema.cedarschema"):
                shutil.copyfile(POLICY_DIR / name, trusted / name)
            original = (trusted / "coverage.cedar").read_text()
            for source in ("invalid Cedar", original.replace("coverageFloor >= 90", 'coverageFloor >= "90"')):
                with self.subTest(source=source):
                    (trusted / "coverage.cedar").write_text(source)
                    result = self.evaluate(self.base, trusted / "check.py")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("schema validation", result.stderr)
            (trusted / "coverage.cedar").write_text(original)
            (trusted / "schema.cedarschema").write_text("invalid schema")
            self.assertNotEqual(self.evaluate(self.base, trusted / "check.py").returncode, 0)

    def test_denies_evaluation_errors_even_with_an_allow_decision(self):
        with tempfile.TemporaryDirectory() as trusted:
            trusted = Path(trusted)
            shutil.copyfile(POLICY_DIR / "check.py", trusted / "check.py")
            schema = (
                (POLICY_DIR / "schema.cedarschema")
                .read_text()
                .replace("entity Manifest;", "entity Manifest { required: Long };")
            )
            policies = (
                (POLICY_DIR / "coverage.cedar").read_text()
                + """
                forbid (
                    principal == Repository::Check::"coverage",
                    action == Repository::Action::"acceptManifest",
                    resource is Repository::Manifest
                ) when { resource.required == 0 };
            """
            )
            (trusted / "schema.cedarschema").write_text(schema)
            (trusted / "coverage.cedar").write_text(policies)
            self.write(MANIFEST, "# updated\n[tool.coverage.report]\nfail_under = 90")
            result = self.evaluate(self.commit(), trusted / "check.py")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Cedar evaluation error", result.stderr)


if __name__ == "__main__":
    unittest.main()
