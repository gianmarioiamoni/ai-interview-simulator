# scripts/question_intelligence/audit_cross_interview_diversity_b2d.py

# Phase 7C-B2D — Cross-Interview Diversity Re-Audit (read-only, 7C-A methodology).

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.question_intelligence import audit_cross_interview_diversity as audit  # noqa: E402

OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"

PHASE_7C_A_BASELINE = {
    "global": {
        "total_prompts": 150,
        "unique_prompts": 77,
        "reuse_pct": 48.7,
        "top_repeated_share_pct": 7.3,
    },
    "hr": {
        "total_prompts": 50,
        "unique_prompts": 13,
        "reuse_pct": 74.0,
        "top_repeated_share_pct": 20.0,
    },
    "technical": {
        "total_prompts": 100,
        "unique_prompts": 64,
        "reuse_pct": 36.0,
    },
    "strict_filter_zero_profiles": 22,
    "filled_profile_area_cells_hr_estimate": 6,
}

HR_AREAS = {
    "hr_background",
    "hr_situational",
    "hr_analytical",
    "hr_brain_teaser",
    "hr_technical_knowledge",
}

TECH_AREAS = {
    "technical_background",
    "technical_technical_knowledge",
    "technical_case_study",
    "technical_coding",
    "technical_database",
}


def _subset_metrics(rows: list[audit.DeliveredQuestion]) -> dict:
    global_m = audit._global_metrics(rows)
    top_share = 0.0

    if global_m.top_repeated:
        top_share = global_m.top_repeated[0]["reuse_pct"]

    return {
        "total_prompts": global_m.total_prompts,
        "unique_prompts": global_m.unique_prompts,
        "reuse_pct": global_m.reuse_pct,
        "top_prompt_share_pct": top_share,
        "by_area": audit._by_area(rows),
    }


def _strict_filter_survival(rows: list[audit.DeliveredQuestion]) -> dict:
    from domain.contracts.user.role import RoleType
    from domain.contracts.user.seniority_level import SeniorityLevel

    zero_profiles = 0
    filled_cells = 0
    profile_totals: dict[str, int] = {}

    for role in RoleType:
        for seniority in SeniorityLevel:
            key = f"{role.value}/{seniority.value}"
            total = 0

            for area in HR_AREAS | TECH_AREAS:
                count = sum(
                    1
                    for row in rows
                    if row.area == area
                    and row.role == role.value
                    and row.seniority == seniority.value
                )

                if count > 0:
                    filled_cells += 1

                total += count

            profile_totals[key] = total

            if total == 0:
                zero_profiles += 1

    duplicate_profiles = [
        p for p in audit._by_profile(rows) if p["interviews"] > 1
    ]

    return {
        "zero_match_profiles": zero_profiles,
        "filled_profile_area_cells_observed": filled_cells,
        "profile_prompt_totals": profile_totals,
        "duplicate_profile_overlap": duplicate_profiles,
    }


def _compare(before: dict, after: dict) -> dict:
    return {
        metric: {
            "before": before.get(metric),
            "after": after.get(metric),
            "delta": round(after.get(metric, 0) - before.get(metric, 0), 1)
            if isinstance(after.get(metric), (int, float))
            and isinstance(before.get(metric), (int, float))
            else None,
        }
        for metric in before
    }


def main() -> None:
    load_dotenv()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    corpus_by_prompt = audit._load_corpus_index()
    audit._instrument_equivalence_band()

    llm = audit.DefaultLLMAdapter()
    provider = audit.QuestionIntelligenceProvider(llm)

    batch_rows: list[audit.DeliveredQuestion] = []
    failures = 0

    print(f"Running {audit.INTERVIEW_COUNT} batch interviews (7C-B2D)...", flush=True)

    for index, (interview_type, role, level) in enumerate(
        audit.INTERVIEW_CONFIGS,
        start=1,
    ):
        interview_id = f"b2d-{index:02d}-{audit.uuid.uuid4().hex[:8]}"
        print(
            f"[{index}/{audit.INTERVIEW_COUNT}] "
            f"{interview_type.value} {role.value} {level.value}",
            flush=True,
        )

        try:
            questions = audit._run_batch_interview(
                provider,
                interview_type,
                role,
                level,
            )
        except Exception as exc:
            failures += 1
            print(f"  FAILED: {exc}", flush=True)
            continue

        batch_rows.extend(
            audit._collect_delivered(
                interview_id=interview_id,
                path="batch_generate",
                interview_type=interview_type,
                role=role,
                level=level,
                questions=questions,
                corpus_by_prompt=corpus_by_prompt,
            )
        )

    hr_rows = [r for r in batch_rows if r.interview_type == "hr"]
    tech_rows = [r for r in batch_rows if r.interview_type == "technical"]

    global_metrics = _subset_metrics(batch_rows)
    hr_metrics = _subset_metrics(hr_rows)
    tech_metrics = _subset_metrics(tech_rows)

    survival = _strict_filter_survival(batch_rows)
    attribution = audit._attribution_for_repeated(batch_rows, audit._SELECTION_EVENTS)

    comparison = {
        "global": _compare(PHASE_7C_A_BASELINE["global"], global_metrics),
        "hr": _compare(PHASE_7C_A_BASELINE["hr"], hr_metrics),
        "technical": _compare(
            PHASE_7C_A_BASELINE["technical"],
            {
                k: tech_metrics[k]
                for k in ("total_prompts", "unique_prompts", "reuse_pct")
            },
        ),
    }

    success = {
        "hr_unique_gt_35": hr_metrics["unique_prompts"] > 35,
        "hr_reuse_lt_30": hr_metrics["reuse_pct"] < 30,
        "global_unique_gt_100": global_metrics["unique_prompts"] > 100,
        "global_reuse_lt_35": global_metrics["reuse_pct"] < 35,
        "technical_no_regression_unique": tech_metrics["unique_prompts"] >= 64,
        "technical_no_regression_reuse": tech_metrics["reuse_pct"] <= 36.0,
        "completion_rate_100": failures == 0 and len(batch_rows) == 150,
        "failures_zero": failures == 0,
    }

    bottlenecks = audit._by_area(batch_rows)
    bottlenecks.sort(key=lambda x: x["reuse_pct"], reverse=True)

    report = {
        "audit": "Phase 7C-B2D Cross-Interview Diversity Re-Audit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "methodology": "QuestionIntelligenceProvider.generate() batch path, 30 interviews, same configs as 7C-A",
        "interview_count": audit.INTERVIEW_COUNT,
        "failures": failures,
        "completion_rate_pct": round(
            (audit.INTERVIEW_COUNT - failures) / audit.INTERVIEW_COUNT * 100,
            1,
        ),
        "selection_events_captured": len(audit._SELECTION_EVENTS),
        "global": global_metrics,
        "hr": hr_metrics,
        "technical": tech_metrics,
        "by_position": audit._by_position(batch_rows),
        "by_profile": audit._by_profile(batch_rows),
        "profile_coverage": survival,
        "attribution": attribution,
        "comparison_7c_a_vs_7c_b2d": comparison,
        "success_criteria": success,
        "success_criteria_all_pass": all(success.values()),
        "remaining_bottlenecks_by_area": bottlenecks[:8],
        "phase_7c_closure_recommendation": (
            "close"
            if all(success.values())
            else "partial_close_with_follow_up"
        ),
        "delivered_questions": [audit.asdict(row) for row in batch_rows],
    }

    output_path = OUTPUT_DIR / "phase_7c_b2d_cross_interview_diversity_audit.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary = {k: v for k, v in report.items() if k != "delivered_questions"}
    summary_path = OUTPUT_DIR / "phase_7c_b2d_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}", flush=True)


if __name__ == "__main__":
    main()
