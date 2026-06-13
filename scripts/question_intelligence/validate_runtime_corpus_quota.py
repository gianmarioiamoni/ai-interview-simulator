"""
Phase 7E-G1 — Runtime Corpus Quota Validation

Validates that the production configuration is enforced during live interview
generation by calling the real service stack.

Configuration under test
------------------------
  Interview type : technical
  Length         : 20 questions
  Allocation     : Candidate-A practical weights
  Corpus mix     : Candidate-A area-specific fractions
  Follow-up rate : 20% (not exercised here — question-set only)

Expected area counts
--------------------
  technical_background          = 2
  technical_technical_knowledge = 4
  technical_case_study          = 5
  technical_database            = 4
  technical_coding              = 5

Expected corpus quotas (per TECHNICAL_AREA_CORPUS_FRACTION)
------------------------------------------------------------
  BG     = round(2 * 0.50) = 1
  TK     = round(4 * 0.80) = 3
  CS     = round(5 * 0.60) = 3
  DB     = round(4 * 0.80) = 3   (coding/SQL pipelines; quota passed but not enforced)
  Coding = round(5 * 0.90) = 4   (banking-rounding aware)

Success criteria
----------------
  Area counts match production spec.
  Corpus questions per area ≤ expected quota (within ±1).
  No area exceeds its configured quota.
  No unexpected fallback behaviour.

Read-only. No production, corpus, or retrieval changes.
"""

from __future__ import annotations

import json
import sys
import types
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple
from unittest.mock import MagicMock

# ── project root on path ──────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# ── stub broken native extensions (x86 PIL / jiter on arm64 host) ─────────────
# Must be done before any project import that pulls sentence_transformers or openai.

def _stub_sentence_transformers() -> None:
    class _T(float):
        def item(self) -> float:
            return float(self)

    class SentenceTransformer:
        def __init__(self, *a, **kw): pass
        def encode(self, text, convert_to_tensor=False, **kw):
            return _T(0.0) if convert_to_tensor else [0.0]

    st = types.ModuleType("sentence_transformers")
    st.SentenceTransformer = SentenceTransformer  # type: ignore
    util = types.ModuleType("sentence_transformers.util")
    util.cos_sim = lambda a, b: _T(0.0)  # type: ignore
    st.util = util  # type: ignore
    backend = types.ModuleType("sentence_transformers.backend")
    backend.load_onnx_model = MagicMock()  # type: ignore
    backend.load_openvino_model = MagicMock()  # type: ignore
    st.backend = backend  # type: ignore
    sys.modules.setdefault("sentence_transformers", st)
    sys.modules.setdefault("sentence_transformers.util", util)
    sys.modules.setdefault("sentence_transformers.backend", backend)

def _stub_jiter() -> None:
    import json as _json
    jiter = types.ModuleType("jiter")
    jiter.from_json = lambda data, **kw: _json.loads(data)  # type: ignore
    jiter.__all__ = ["from_json"]  # type: ignore
    sys.modules.setdefault("jiter", jiter)

_stub_sentence_transformers()
_stub_jiter()

# ── load .env so OPENAI_API_KEY etc. are available ────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass
OUT  = ROOT / "scripts" / "question_intelligence" / "output"
OUT.mkdir(parents=True, exist_ok=True)

# ── production constants (read-only) ─────────────────────────────────────────
from app.settings.constants import (
    TECHNICAL_AREA_QUESTION_COUNT,
    TECHNICAL_AREA_CORPUS_FRACTION,
)
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from infrastructure.llm.llm_adapter import DefaultLLMAdapter
from services.question_intelligence.corpus_quota_resolver import resolve_corpus_quota
from services.question_intelligence.question_intelligence_provider import (
    QuestionIntelligenceProvider,
)

# ── profiles under test ───────────────────────────────────────────────────────
PROFILES: list[tuple[RoleType, SeniorityLevel]] = [
    (RoleType.BACKEND_ENGINEER,   SeniorityLevel.JUNIOR),
    (RoleType.BACKEND_ENGINEER,   SeniorityLevel.MID),
    (RoleType.BACKEND_ENGINEER,   SeniorityLevel.SENIOR),
    (RoleType.FRONTEND_ENGINEER,  SeniorityLevel.MID),
    (RoleType.DATA_ENGINEER,      SeniorityLevel.SENIOR),
]

INTERVIEW_TYPE = InterviewType.TECHNICAL

# Areas ordered as they appear in the domain enum (order doesn't affect counts)
TECH_AREAS: list[InterviewArea] = [
    InterviewArea.TECH_BACKGROUND,
    InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
    InterviewArea.TECH_CASE_STUDY,
    InterviewArea.TECH_DATABASE,
    InterviewArea.TECH_CODING,
]

# Expected quotas derived from constants (mirrors resolve_corpus_quota)
EXPECTED_QUOTA: dict[str, int] = {
    area: resolve_corpus_quota(
        InterviewArea(area),
        INTERVIEW_TYPE,
        TECHNICAL_AREA_QUESTION_COUNT[area],
    )  # type: ignore[arg-type]
    for area in TECHNICAL_AREA_QUESTION_COUNT
}

EXPECTED_AREA_COUNT: dict[str, int] = dict(TECHNICAL_AREA_QUESTION_COUNT)

CORPUS_ORIGIN = {QuestionOriginType.RETRIEVAL, QuestionOriginType.RECOVERY_EXPANSION}


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────

class AreaStats(NamedTuple):
    total:  int
    corpus: int
    llm:    int


def _origin_is_corpus(origin_type: QuestionOriginType | None) -> bool:
    return origin_type in CORPUS_ORIGIN


def _generate_interview(
    provider: QuestionIntelligenceProvider,
    role: RoleType,
    level: SeniorityLevel,
) -> dict[str, AreaStats]:
    """
    Generate a full 20-question technical interview and return per-area stats.

    Strategy: call area_builder.build() for each area the required number of
    times (per TECHNICAL_AREA_QUESTION_COUNT), passing the resolved corpus_quota
    each time.  We accumulate questions across calls for the same area to
    simulate the full area budget.
    """
    area_builder = provider._area_builder
    memory = None

    stats: dict[str, AreaStats] = {}

    for area in TECH_AREAS:
        area_key   = area.value
        area_count = EXPECTED_AREA_COUNT[area_key]
        quota      = EXPECTED_QUOTA[area_key]

        corpus_questions: list = []
        llm_questions:    list = []

        # Per-area memory (independent per area, as in production)
        from services.question_corpus.contracts.interview_retrieval_memory import (
            InterviewRetrievalMemory,
        )
        area_memory = InterviewRetrievalMemory()

        fallback_errors: list[str] = []

        # ── Single build call: area_count questions, quota caps corpus ─────────
        # The WrittenQuestionPipeline.build() is designed to be called ONCE per
        # area with questions_per_area=N and corpus_quota=K.  It retrieves up to
        # K corpus questions then generates (N-K) LLM questions.  This matches
        # the production pattern (even though the lazy-adaptive service uses
        # QUESTIONS_PER_AREA=1 per call, the pipeline quota logic is the same).
        try:
            qs, area_memory = area_builder.build(
                role=role,
                level=level,
                interview_type=INTERVIEW_TYPE,
                area=area,
                questions_per_area=area_count,
                corpus_quota=quota,
                memory=area_memory,
            )
            for q in qs:
                origin = q.provenance.origin_type if q.provenance else None
                if _origin_is_corpus(origin):
                    corpus_questions.append(q)
                else:
                    llm_questions.append(q)
        except Exception as exc:
            # Pre-existing corpus metadata issue (e.g. role='other' in
            # recovery-expansion documents). Record and surface in report.
            err_msg = str(exc)
            fallback_errors.append(f"build_call: {err_msg}")

        total = len(corpus_questions) + len(llm_questions)
        stats[area_key] = AreaStats(
            total=total,
            corpus=len(corpus_questions),
            llm=len(llm_questions),
        )
        if fallback_errors:
            stats[f"{area_key}__fallback_errors"] = fallback_errors  # type: ignore[assignment]

    return stats


def _validate_profile(
    stats: dict[str, AreaStats],
    profile_label: str,
) -> dict:
    """Return a per-profile validation result dict."""
    area_results = {}
    all_pass     = True

    # Collect fallback error metadata before iterating areas
    fallback_findings: dict[str, list[str]] = {
        k.replace("__fallback_errors", ""): v
        for k, v in stats.items()
        if isinstance(v, list)
    }

    for area_key, s in stats.items():
        if not isinstance(s, AreaStats):
            continue  # skip sentinel keys
        expected_total  = EXPECTED_AREA_COUNT[area_key]
        expected_quota  = EXPECTED_QUOTA[area_key]

        count_ok   = s.total == expected_total
        # corpus ≤ expected_quota (within ±1) AND never exceeds quota
        quota_ok   = s.corpus <= expected_quota + 1
        no_excess  = s.corpus <= expected_quota

        area_pass  = count_ok and quota_ok

        if not area_pass:
            all_pass = False

        area_result: dict = {
            "expected_total":   expected_total,
            "actual_total":     s.total,
            "expected_quota":   expected_quota,
            "actual_corpus":    s.corpus,
            "actual_llm":       s.llm,
            "count_ok":         count_ok,
            "quota_ok":         quota_ok,
            "no_corpus_excess": no_excess,
            "area_pass":        area_pass,
        }
        if area_key in fallback_findings:
            area_result["fallback_errors"] = fallback_findings[area_key]
        area_results[area_key] = area_result

    total_corpus = sum(s.corpus for s in stats.values() if isinstance(s, AreaStats))
    total_llm    = sum(s.llm    for s in stats.values() if isinstance(s, AreaStats))
    total_q      = total_corpus + total_llm
    corpus_pct   = round(100.0 * total_corpus / total_q, 1) if total_q else 0.0
    llm_pct      = round(100.0 * total_llm    / total_q, 1) if total_q else 0.0

    return {
        "profile":       profile_label,
        "overall_pass":  all_pass,
        "total_questions": total_q,
        "total_corpus":  total_corpus,
        "total_llm":     total_llm,
        "corpus_pct":    corpus_pct,
        "llm_pct":       llm_pct,
        "areas":         area_results,
    }


# ─────────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    started_at = datetime.now(timezone.utc).isoformat()
    print(f"\n{'='*70}")
    print("Phase 7E-G1 — Runtime Corpus Quota Validation")
    print(f"{'='*70}")
    print(f"Started : {started_at}")
    print(f"\nExpected area counts : {EXPECTED_AREA_COUNT}")
    print(f"Expected corpus quotas: {EXPECTED_QUOTA}")
    print()

    llm      = DefaultLLMAdapter()
    provider = QuestionIntelligenceProvider(llm=llm)

    all_results: list[dict] = []

    for role, level in PROFILES:
        label = f"{role.value}/{level.value}"
        print(f"  ▶  Generating interview for {label} …")

        try:
            stats  = _generate_interview(provider, role, level)
            result = _validate_profile(stats, label)
            status = "PASS" if result["overall_pass"] else "FAIL"
            print(f"     {status}  |  corpus={result['total_corpus']}Q "
                  f"({result['corpus_pct']}%)  llm={result['total_llm']}Q "
                  f"({result['llm_pct']}%)")

            for area_key, ar in result["areas"].items():
                flag = "✓" if ar["area_pass"] else "✗"
                print(
                    f"       {flag} {area_key:<38} "
                    f"total={ar['actual_total']:>2}  "
                    f"corpus={ar['actual_corpus']:>2}/{ar['expected_quota']:>2}  "
                    f"llm={ar['actual_llm']:>2}"
                )

        except Exception as exc:
            print(f"     ERROR: {exc}")
            result = {
                "profile":      label,
                "overall_pass": False,
                "error":        str(exc),
            }

        all_results.append(result)
        print()

    # ── summary ───────────────────────────────────────────────────────────────
    n_pass  = sum(1 for r in all_results if r.get("overall_pass", False))
    n_total = len(all_results)

    summary: dict = {
        "phase":      "7E-G1",
        "objective":  "Runtime corpus quota validation",
        "started_at": started_at,
        "ended_at":   datetime.now(timezone.utc).isoformat(),
        "config": {
            "interview_type":   INTERVIEW_TYPE.value,
            "expected_counts":  EXPECTED_AREA_COUNT,
            "expected_quotas":  EXPECTED_QUOTA,
        },
        "profiles_tested": n_total,
        "profiles_passed": n_pass,
        "verdict": "PASS" if n_pass == n_total else "FAIL",
    }

    # success criteria checklist
    corpus_ok = all(
        r["areas"][a]["quota_ok"]
        for r in all_results
        if "areas" in r
        for a in r["areas"]
    )
    no_excess = all(
        r["areas"][a]["no_corpus_excess"]
        for r in all_results
        if "areas" in r
        for a in r["areas"]
    )
    counts_ok = all(
        r["areas"][a]["count_ok"]
        for r in all_results
        if "areas" in r
        for a in r["areas"]
    )
    # Profiles that failed only due to corpus metadata errors are not
    # configuration failures — they expose a pre-existing data issue.
    config_failures = [
        r for r in all_results
        if not r.get("overall_pass", False) and "error" not in r
        and any(
            not ar.get("area_pass", True)
            for ar in r.get("areas", {}).values()
            if isinstance(ar, dict) and "fallback_errors" not in ar
        )
    ]
    corpus_metadata_errors = [
        r for r in all_results
        if "error" in r and "Invalid role value" in r.get("error", "")
    ]

    summary["criteria"] = {
        "area_counts_match_production_config":  counts_ok,
        "corpus_quotas_respected_within_1q":    corpus_ok,
        "no_area_exceeds_corpus_quota":         no_excess,
        "no_unexpected_fallback":               n_pass == n_total,
    }
    summary["open_issues"] = {
        "corpus_metadata_role_other_error": len(corpus_metadata_errors),
        "note": (
            "Corpus contains documents with role='other' in recovery-expansion "
            "stage metadata. This is a pre-existing data issue (not introduced "
            "by Phase 7E-G). Affects profiles where corpus depth exhaustion "
            "triggers the fallback retrieval stage."
        ) if corpus_metadata_errors else None,
    }

    print(f"{'='*70}")
    print(f"Verdict : {summary['verdict']}  ({n_pass}/{n_total} profiles passed)")
    print(f"Criteria:")
    for k, v in summary["criteria"].items():
        flag = "✓" if v else "✗"
        print(f"  {flag} {k}")
    print(f"{'='*70}\n")

    # ── write outputs ─────────────────────────────────────────────────────────
    full_report = {
        "phase":    "7E-G1",
        "summary":  summary,
        "profiles": all_results,
    }

    (OUT / "phase_7e_g1_runtime_quota_validation.json").write_text(
        json.dumps(full_report, indent=2)
    )
    (OUT / "phase_7e_g1_summary.json").write_text(
        json.dumps(summary, indent=2)
    )

    print("Output written to:")
    print(f"  {OUT / 'phase_7e_g1_runtime_quota_validation.json'}")
    print(f"  {OUT / 'phase_7e_g1_summary.json'}")


if __name__ == "__main__":
    main()
