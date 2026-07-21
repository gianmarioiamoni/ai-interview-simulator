# scripts/performance/run_stub_load.py
# EPIC-V13-09 C7 — emit 50-session stub load evidence (absolute SLO gates).

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.performance.load_stub_sessions import (  # noqa: E402
    LOAD_SESSION_COUNT,
    assert_absolute_load_slos,
    run_stub_load,
)


def main() -> int:
    result = run_stub_load(session_count=LOAD_SESSION_COUNT)
    assert_absolute_load_slos(result)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
