# scripts/performance/profile_longitudinal.py
# EPIC-V13-09 C6 — emit longitudinal_update profiling evidence (PROF-03).
# Harness-only; prints JSON evidence suitable for baseline report appendix.

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.performance.profiling_longitudinal import (  # noqa: E402
    profile_longitudinal_update,
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="epic09-c6-longitudinal-") as tmp:
        storage = Path(tmp) / "longitudinal"
        first, _ = profile_longitudinal_update(
            storage_dir=storage,
            interview_id="epic09-c6-session-0",
            interview_index=0,
        )
        second, _ = profile_longitudinal_update(
            storage_dir=storage,
            interview_id="epic09-c6-session-1",
            interview_index=1,
        )
    print(
        json.dumps(
            {
                "first_session": first.to_dict(),
                "second_session_cross_session": second.to_dict(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
