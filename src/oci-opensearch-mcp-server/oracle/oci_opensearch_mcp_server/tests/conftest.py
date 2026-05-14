"""Pytest configuration for preferring this repository's local package imports.

This repo can coexist on a workstation with other checkouts that expose the same
package name. Insert the current repository root at the front of ``sys.path`` so
tests validate the source tree being edited rather than an unrelated local install.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

repo_root_str = str(REPO_ROOT)
if sys.path[0] != repo_root_str:
    sys.path.insert(0, repo_root_str)
