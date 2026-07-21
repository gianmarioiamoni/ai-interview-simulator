# tests/infrastructure/architecture/epic10_pat06_allowlist.py
#
# EPIC-10 P5 / C11 — PAT-06 corollary allowlist (AR-05 / Freeze §7.1).
#
# Not violations (capability dispatch / node-invoked facades / conditional OK):
#   - ExecutionEngine: type → executor dispatch
#   - AreaQuestionBuilder: area → pipeline selection
#   - RecoveryReplanner: capability-internal retry planning; graph continuation
#     remains owned by the calling node (AR-05)
#
# Violations (forbidden in services/ outside this allowlist):
#   - Selecting interview workflow branch / lifecycle (NEXT/RETRY/GENERATE_REPORT)
#   - Importing or constructing LangGraph StateGraph / edges
#
# start.py bootstrap is out of this services/ scan scope (AR-05: OK if not
# interview workflow routing).

from __future__ import annotations

# Relative paths under repo root (posix).
PAT06_COROLLARY_ALLOWLIST: frozenset[str] = frozenset(
    {
        "services/execution_engine.py",
        "services/question_intelligence/area_question_builder.py",
        "services/replanning/recovery_replanner.py",
    }
)
