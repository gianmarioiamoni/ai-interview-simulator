# scripts/performance/profile_reasoner_kp.py
# EPIC-V13-09 C5 — emit reasoner + KP profiling evidence (PROF-01/02/05).
# Harness-only; prints JSON evidence suitable for baseline report appendix.

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.performance.profiling_reasoner_kp import (  # noqa: E402
    profile_reasoner_kp_under_written_cycle,
)


def main() -> int:
    evidence, _state, _stub = profile_reasoner_kp_under_written_cycle()
    print(json.dumps(evidence.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
