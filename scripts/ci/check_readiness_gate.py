#!/usr/bin/env python3
# scripts/ci/check_readiness_gate.py
#
# EPIC-08 P4/C11 — deploy/CI entrypoint for the readiness gate.
# Fails the process when GET /health/ready is not successful.

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infrastructure.health.readiness_gate import main

if __name__ == "__main__":
    raise SystemExit(main())
