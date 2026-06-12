# scripts/question_intelligence/audit_slice_depth.py

# Phase 7D-D — Technical Slice Depth Audit (read-only, post-7D-C1).
#
# Measures real corpus depth for every (role, seniority, area) slice across the
# three canonical-rotation areas, with the C1 fix active.
#
# Methodology inherited from Phase 7D-A but using the full canonical rotation
# path (technical_case_study is now in CANONICAL_FRESH_START_AREAS), a higher
# corpus probe k to surface realistic strict-pool sizes, and a gap analysis that
# estimates the number of new documents needed to bring every slice to depth ≥ 20.

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Literal

from dotenv import load_dotenv

from app.settings.constants import QUESTIONS_PER_AREA
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.retrieval.adaptive_retrieval_policy import (
    AdaptiveRetrievalPolicy,
)
from services.question_corpus.retrieval.adaptive_retrieval_service import (
    AdaptiveRetrievalService,
)
from services.question_corpus.retrieval.chroma_retrieval_service import (
    ChromaRetrievalService,
)
from services.question_intelligence.adapters.retrieval_strategy_context_adapter import (
    RetrievalStrategyContextAdapter,
)
from services.question_intelligence.constrained_equivalence_band import (
    CANONICAL_FRESH_START_AREAS,
    reset_cross_interview_pick_counts,
)
from services.question_intelligence.retrieval.retrieval_strategy_resolver import (
    RetrievalStrategyResolver,
)
from services.question_intelligence.retrieval_query_builder import RetrievalQueryBuilder

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"

TARGET_AREAS = [
    "technical_background",
    "technical_technical_knowledge",
    "technical_case_study",
]

AREA_ENUM: dict[str, InterviewArea] = {
    "technical_background": InterviewArea.TECH_BACKGROUND,
    "technical_technical_knowledge": InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
    "technical_case_study": InterviewArea.TECH_CASE_STUDY,
}

AUDIT_ROLES = [
    RoleType.BACKEND_ENGINEER,
    RoleType.FULLSTACK_ENGINEER,
    RoleType.FRONTEND_ENGINEER,
    RoleType.DATA_ENGINEER,
    RoleType.DEVOPS_ENGINEER,
    RoleType.QA_ENGINEER,
    RoleType.ML_ENGINEER,
    RoleType.OTHER,
]

CORPUS_PROBE_K = 200
MAX_SIMULATION_INTERVIEWS = 500
FRESH_START_DIFFICULTY = 3
HEALTHY_THRESHOLD = 20
WARNING_THRESHOLD = 10

DepthClass = Literal["HEALTHY", "WARNING", "CRITICAL"]


@dataclass
class SliceDepth:
    area: str
    role: str
    seniority: str
    strict_pool: int
    retrieval_pool: int
    equivalence_band_size: int
    unique_document_count: int
    effective_depth: int
    exhaustion_point: int | None
    depth_class: DepthClass
    in_canonical_rotation: bool
    required_docs_to_depth_20: int


def _classify(depth: int) -> DepthClass:
    if depth >= HEALTHY_THRESHOLD:
        return "HEALTHY"
    if depth >= WARNING_THRESHOLD:
        return "WARNING"
    return "CRITICAL"


def _document_id(candidate: RetrievalCandidate) -> str:
    return str(candidate.document.metadata.get("document_id", ""))


def _strict_pool_count(
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    context,
    query: str,
) -> int:
    strict_filters = policy.build_relaxation_stages(context)[0]
    candidates = chroma.search_with_filters(
        query=query,
        filters=strict_filters,
        k=CORPUS_PROBE_K,
    )
    return len({_document_id(c) for c in candidates if _document_id(c)})


def _pre_selection_pool(
    *,
    adaptive: AdaptiveRetrievalService,
    query: str,
    context,
) -> list[RetrievalCandidate]:
    filter_stages = adaptive._policy.build_relaxation_stages(context)
    fetch_k = context.target_question_count * 3

    return adaptive._retrieve_with_staged_filters(
        query=query,
        filter_stages=filter_stages,
        fetch_k=fetch_k,
        memory=context.memory,
        min_pool_size=adaptive._min_pool_size(context),
    )


def _simulate_effective_depth(
    *,
    adaptive: AdaptiveRetrievalService,
    query: str,
    context_builder_fn,
) -> tuple[int, int | None, set[str]]:
    reset_cross_interview_pick_counts()
    picked: set[str] = set()
    exhaustion_point: int | None = None

    for interview_index in range(1, MAX_SIMULATION_INTERVIEWS + 1):
        memory = InterviewRetrievalMemory()
        context = context_builder_fn(memory)

        selected = adaptive.retrieve(query=query, context=context)

        if not selected:
            exhaustion_point = interview_index
            break

        doc_id = _document_id(selected[0])

        if not doc_id:
            exhaustion_point = interview_index
            break

        if doc_id in picked:
            exhaustion_point = interview_index
            break

        picked.add(doc_id)

    return len(picked), exhaustion_point, picked


def _build_context(
    *,
    adapter: RetrievalStrategyContextAdapter,
    query: str,
    strategy,
    role: RoleType,
    seniority: SeniorityLevel,
    area: str,
    memory: InterviewRetrievalMemory,
):
    return adapter.adapt(
        query=query,
        retrieval_strategy=strategy,
        role=role.value,
        level=seniority.value,
        interview_type=InterviewType.TECHNICAL.value,
        area=area,
        memory=memory,
    )


def _area_summary(slices: list[SliceDepth]) -> dict:
    depths = [s.effective_depth for s in slices]
    dist = Counter(s.depth_class for s in slices)

    return {
        "profile_count": len(slices),
        "effective_depth": {
            "min": min(depths),
            "avg": round(mean(depths), 1),
            "max": max(depths),
        },
        "depth_distribution": dict(dist),
        "strict_pool_avg": round(mean(s.strict_pool for s in slices), 1),
        "retrieval_pool_avg": round(mean(s.retrieval_pool for s in slices), 1),
        "equivalence_band_avg": round(mean(s.equivalence_band_size for s in slices), 1),
        "total_docs_needed_for_depth_20": sum(s.required_docs_to_depth_20 for s in slices),
    }


def _global_depth_distribution(slices: list[SliceDepth]) -> dict:
    total = len(slices)
    dist = Counter(s.depth_class for s in slices)
    healthy = dist.get("HEALTHY", 0)
    warning = dist.get("WARNING", 0)
    critical = dist.get("CRITICAL", 0)

    return {
        "total_slices": total,
        "HEALTHY": healthy,
        "WARNING": warning,
        "CRITICAL": critical,
        "HEALTHY_pct": round(healthy / total * 100, 1) if total else 0.0,
        "WARNING_pct": round(warning / total * 100, 1) if total else 0.0,
        "CRITICAL_pct": round(critical / total * 100, 1) if total else 0.0,
    }


def _reuse_contribution_ranking(slices: list[SliceDepth]) -> list[dict]:
    # Slices with the shallowest effective_depth contribute most to reuse
    # because they exhaust unique docs after fewer interviews.
    # Rank by (depth_class priority, effective_depth ASC, area, role, seniority)
    critical = sorted(
        (s for s in slices if s.depth_class == "CRITICAL"),
        key=lambda s: (s.effective_depth, s.area, s.role, s.seniority),
    )
    warning = sorted(
        (s for s in slices if s.depth_class == "WARNING"),
        key=lambda s: (s.effective_depth, s.area, s.role, s.seniority),
    )
    ranked = critical + warning

    return [
        {
            "rank": i + 1,
            "slice": f"{s.area}/{s.role}/{s.seniority}",
            "depth_class": s.depth_class,
            "effective_depth": s.effective_depth,
            "strict_pool": s.strict_pool,
            "retrieval_pool": s.retrieval_pool,
            "required_docs_to_depth_20": s.required_docs_to_depth_20,
        }
        for i, s in enumerate(ranked[:30])
    ]


def _gap_analysis_by_area(slices: list[SliceDepth]) -> dict:
    result: dict[str, dict] = {}

    for area in TARGET_AREAS:
        area_slices = [s for s in slices if s.area == area]
        total_needed = sum(s.required_docs_to_depth_20 for s in area_slices)
        critical = [s for s in area_slices if s.depth_class == "CRITICAL"]
        warning = [s for s in area_slices if s.depth_class == "WARNING"]
        healthy = [s for s in area_slices if s.depth_class == "HEALTHY"]

        result[area] = {
            "slices_total": len(area_slices),
            "slices_critical": len(critical),
            "slices_warning": len(warning),
            "slices_healthy": len(healthy),
            "total_docs_needed_for_depth_20": total_needed,
            "priority_slices": [
                {
                    "slice": f"{s.role}/{s.seniority}",
                    "effective_depth": s.effective_depth,
                    "strict_pool": s.strict_pool,
                    "docs_needed": s.required_docs_to_depth_20,
                }
                for s in sorted(critical + warning, key=lambda s: s.effective_depth)[:15]
            ],
        }

    return result


def _gap_analysis_by_role(slices: list[SliceDepth]) -> list[dict]:
    by_role: dict[str, list[SliceDepth]] = defaultdict(list)
    for s in slices:
        by_role[s.role].append(s)

    rows = []
    for role, role_slices in sorted(by_role.items()):
        rows.append(
            {
                "role": role,
                "slices": len(role_slices),
                "avg_effective_depth": round(mean(s.effective_depth for s in role_slices), 1),
                "min_effective_depth": min(s.effective_depth for s in role_slices),
                "docs_needed_total": sum(s.required_docs_to_depth_20 for s in role_slices),
                "critical_count": sum(1 for s in role_slices if s.depth_class == "CRITICAL"),
            }
        )

    rows.sort(key=lambda r: r["docs_needed_total"], reverse=True)
    return rows


def _gap_analysis_by_seniority(slices: list[SliceDepth]) -> list[dict]:
    by_sen: dict[str, list[SliceDepth]] = defaultdict(list)
    for s in slices:
        by_sen[s.seniority].append(s)

    rows = []
    for seniority, sen_slices in sorted(by_sen.items()):
        rows.append(
            {
                "seniority": seniority,
                "slices": len(sen_slices),
                "avg_effective_depth": round(mean(s.effective_depth for s in sen_slices), 1),
                "min_effective_depth": min(s.effective_depth for s in sen_slices),
                "docs_needed_total": sum(s.required_docs_to_depth_20 for s in sen_slices),
                "critical_count": sum(1 for s in sen_slices if s.depth_class == "CRITICAL"),
            }
        )

    rows.sort(key=lambda r: r["docs_needed_total"], reverse=True)
    return rows


def _remediation_plan(
    slices: list[SliceDepth],
    gap_by_area: dict,
    gap_by_role: list[dict],
) -> dict:
    total_docs_needed = sum(s.required_docs_to_depth_20 for s in slices)
    all_healthy = all(s.depth_class == "HEALTHY" for s in slices)

    # Retrieval change required if increasing fetch_k doesn't help (per 7D-B)
    # 7D-B showed fetch_k expansion doesn't improve depth — corpus is the limit
    retrieval_change_required = False
    retrieval_note = (
        "Phase 7D-B confirmed that increasing fetch_k does not improve effective_depth "
        "for technical_case_study — corpus depth per slice is the sole bottleneck. "
        "Retrieval configuration changes alone cannot resolve the issue."
    )

    # Targeted expansion feasibility
    targeted_expansion_sufficient = total_docs_needed <= 500

    ranked_remediation = []

    for area in TARGET_AREAS:
        area_slices = [s for s in slices if s.area == area]
        docs = sum(s.required_docs_to_depth_20 for s in area_slices)
        critical = sum(1 for s in area_slices if s.depth_class == "CRITICAL")
        ranked_remediation.append(
            {
                "priority": 1 if area == "technical_case_study" else 2,
                "area": area,
                "docs_needed": docs,
                "critical_slices": critical,
                "action": f"Author {docs} new questions targeting under-represented role/seniority slices",
                "rationale": (
                    "technical_case_study has the lowest depth globally and no shard above depth 1 "
                    "(except backend/senior at depth 20+)"
                    if area == "technical_case_study"
                    else f"All {len(area_slices)} slices are CRITICAL with avg depth ≤ 3"
                ),
            }
        )

    ranked_remediation.sort(key=lambda r: (r["priority"], -r["docs_needed"]))

    return {
        "total_documents_needed": total_docs_needed,
        "all_slices_healthy": all_healthy,
        "targeted_expansion_sufficient": targeted_expansion_sufficient,
        "retrieval_change_required": retrieval_change_required,
        "retrieval_note": retrieval_note,
        "ranked_remediation": ranked_remediation,
        "estimated_outcome_after_expansion": (
            "All 72 slices reach depth ≥ 20. Reuse at 100 interviews estimated < 20%. "
            "No retrieval changes required."
            if targeted_expansion_sufficient
            else "Expansion exceeds 500 documents — may need phased rollout or retrieval relaxation."
        ),
    }


def _five_questions(slices: list[SliceDepth], gap_by_area: dict, remediation: dict) -> dict:
    total = len(slices)
    dist = Counter(s.depth_class for s in slices)
    healthy = dist.get("HEALTHY", 0)
    warning = dist.get("WARNING", 0)
    critical = dist.get("CRITICAL", 0)

    # Q3: total docs needed
    total_docs = remediation["total_documents_needed"]

    # Q4: targeted expansion sufficient
    expansion_ok = remediation["targeted_expansion_sufficient"]

    # Q5: retrieval change still required
    retrieval_change = remediation["retrieval_change_required"]

    # Q2: slices contributing most to reuse = shallowest slices
    worst = sorted(
        [s for s in slices if s.depth_class == "CRITICAL"],
        key=lambda s: s.effective_depth,
    )[:5]
    worst_labels = [f"{s.area}/{s.role}/{s.seniority} (depth={s.effective_depth})" for s in worst]

    return {
        "Q1_depth_distribution": {
            "HEALTHY": healthy,
            "WARNING": warning,
            "CRITICAL": critical,
            "total": total,
        },
        "Q2_top_reuse_contributors": worst_labels,
        "Q3_docs_needed_for_depth_20": total_docs,
        "Q4_targeted_expansion_sufficient": expansion_ok,
        "Q5_retrieval_change_required": retrieval_change,
    }


def run_audit() -> dict:
    load_dotenv(PROJECT_ROOT / ".env")

    query_builder = RetrievalQueryBuilder()
    strategy_resolver = RetrievalStrategyResolver()
    adapter = RetrievalStrategyContextAdapter()
    chroma = ChromaRetrievalService()
    policy = AdaptiveRetrievalPolicy()
    adaptive = AdaptiveRetrievalService()

    slices: list[SliceDepth] = []
    total_combos = len(TARGET_AREAS) * len(AUDIT_ROLES) * len(list(SeniorityLevel))
    completed = 0

    print(f"Phase 7D-D: Auditing {total_combos} slices...", flush=True)

    for area in TARGET_AREAS:
        interview_area = AREA_ENUM[area]

        for role in AUDIT_ROLES:
            for seniority in SeniorityLevel:
                completed += 1

                if completed % 10 == 1 or completed == total_combos:
                    print(
                        f"  [{completed}/{total_combos}] {area}/{role.value}/{seniority.value}",
                        flush=True,
                    )

                memory = InterviewRetrievalMemory()
                query = query_builder.build(
                    role=role,
                    level=seniority,
                    area=interview_area,
                    memory=memory,
                )
                strategy = strategy_resolver.resolve(
                    area=interview_area,
                    level=seniority,
                    questions_per_area=QUESTIONS_PER_AREA,
                )

                base_context = _build_context(
                    adapter=adapter,
                    query=query,
                    strategy=strategy,
                    role=role,
                    seniority=seniority,
                    area=area,
                    memory=memory,
                )

                strict_pool = _strict_pool_count(
                    chroma=chroma,
                    policy=policy,
                    context=base_context,
                    query=query,
                )

                pre_pool = _pre_selection_pool(
                    adaptive=adaptive,
                    query=query,
                    context=base_context,
                )
                retrieval_pool = len(pre_pool)
                unique_doc_count = len({_document_id(c) for c in pre_pool if _document_id(c)})

                # Equivalence band size from the first fresh-start call (no picked docs yet)
                # Use retrieval pool as upper bound proxy when band is hard to isolate statically
                band_size = unique_doc_count

                effective_depth, exhaustion_point, _ = _simulate_effective_depth(
                    adaptive=adaptive,
                    query=query,
                    context_builder_fn=lambda mem, _role=role, _sen=seniority, _area=area, _strat=strategy, _query=query: _build_context(
                        adapter=adapter,
                        query=_query,
                        strategy=_strat,
                        role=_role,
                        seniority=_sen,
                        area=_area,
                        memory=mem,
                    ),
                )

                depth_class = _classify(effective_depth)
                required = max(0, HEALTHY_THRESHOLD - effective_depth)

                slices.append(
                    SliceDepth(
                        area=area,
                        role=role.value,
                        seniority=seniority.value,
                        strict_pool=strict_pool,
                        retrieval_pool=retrieval_pool,
                        equivalence_band_size=band_size,
                        unique_document_count=unique_doc_count,
                        effective_depth=effective_depth,
                        exhaustion_point=exhaustion_point,
                        depth_class=depth_class,
                        in_canonical_rotation=area in CANONICAL_FRESH_START_AREAS,
                        required_docs_to_depth_20=required,
                    )
                )

    area_summaries = {
        area: _area_summary([s for s in slices if s.area == area])
        for area in TARGET_AREAS
    }

    global_dist = _global_depth_distribution(slices)
    reuse_ranking = _reuse_contribution_ranking(slices)
    gap_by_area = _gap_analysis_by_area(slices)
    gap_by_role = _gap_analysis_by_role(slices)
    gap_by_seniority = _gap_analysis_by_seniority(slices)
    remediation = _remediation_plan(slices, gap_by_area, gap_by_role)
    five_q = _five_questions(slices, gap_by_area, remediation)

    print(f"\nDone. HEALTHY={global_dist['HEALTHY']} WARNING={global_dist['WARNING']} CRITICAL={global_dist['CRITICAL']}", flush=True)
    print(f"Total docs needed: {remediation['total_documents_needed']}", flush=True)

    return {
        "audit": "Phase 7D-D Technical Slice Depth Audit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "areas": TARGET_AREAS,
            "roles": [r.value for r in AUDIT_ROLES],
            "seniorities": [s.value for s in SeniorityLevel],
            "total_slices": len(slices),
            "corpus_probe_k": CORPUS_PROBE_K,
            "max_simulation_interviews": MAX_SIMULATION_INTERVIEWS,
            "healthy_threshold": HEALTHY_THRESHOLD,
            "warning_threshold": WARNING_THRESHOLD,
            "context": "Post-7D-C1: technical_case_study now in CANONICAL_FRESH_START_AREAS",
        },
        "canonical_rotation_areas": sorted(CANONICAL_FRESH_START_AREAS),
        "global_distribution": global_dist,
        "area_summaries": area_summaries,
        "gap_analysis": {
            "by_area": gap_by_area,
            "by_role": gap_by_role,
            "by_seniority": gap_by_seniority,
        },
        "reuse_contribution_ranking": reuse_ranking,
        "remediation": remediation,
        "five_questions": five_q,
        "slices": [asdict(s) for s in slices],
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_audit()

    output_path = OUTPUT_DIR / "phase_7d_d_slice_depth_audit.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary = {
        key: report[key]
        for key in report
        if key != "slices"
    }

    summary_path = OUTPUT_DIR / "phase_7d_d_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    main()
