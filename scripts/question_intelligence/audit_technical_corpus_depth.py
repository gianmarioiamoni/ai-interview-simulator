# scripts/question_intelligence/audit_technical_corpus_depth.py

# Phase 7D-A — Technical Corpus Depth Audit (read-only).

from __future__ import annotations

import json
from collections import Counter
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

AREA_ENUM = {
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

DepthClass = Literal["CRITICAL", "WARNING", "ACCEPTABLE", "HEALTHY"]


@dataclass
class ProfileDepth:
    area: str
    role: str
    seniority: str
    strict_pool: int
    retrieval_pool: int
    unique_document_ceiling: int
    effective_depth: int
    exhaustion_point: int | None
    depth_class: str


def _classify_depth(depth: int) -> str:
    if depth < 10:
        return "CRITICAL"

    if depth <= 20:
        return "WARNING"

    if depth <= 40:
        return "ACCEPTABLE"

    return "HEALTHY"


def _document_id(candidate: RetrievalCandidate) -> str:
    return str(candidate.document.metadata.get("document_id", ""))


def _strict_pool_count(
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    context,
    query: str,
) -> int:
    strict = policy.build_relaxation_stages(context)[0]
    candidates = chroma.search_with_filters(
        query=query,
        filters=strict,
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

        selected = adaptive.retrieve(
            query=query,
            context=context,
        )

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


def _area_summary(profiles: list[ProfileDepth]) -> dict:
    depths = [profile.effective_depth for profile in profiles]

    if not depths:
        return {}

    distribution = Counter(profile.depth_class for profile in profiles)

    return {
        "profile_count": len(profiles),
        "average_depth": round(mean(depths), 1),
        "minimum_depth": min(depths),
        "maximum_depth": max(depths),
        "depth_distribution": dict(distribution),
        "average_strict_pool": round(
            mean(profile.strict_pool for profile in profiles),
            1,
        ),
        "average_retrieval_pool": round(
            mean(profile.retrieval_pool for profile in profiles),
            1,
        ),
    }


def _saturation_forecast(profiles: list[ProfileDepth]) -> dict:
    critical = [p for p in profiles if p.depth_class == "CRITICAL"]
    warning = [p for p in profiles if p.depth_class == "WARNING"]

    weighted_depth = mean(p.effective_depth for p in profiles) if profiles else 0

    return {
        "weighted_avg_effective_depth": round(weighted_depth, 1),
        "profiles_at_critical": len(critical),
        "profiles_at_warning": len(warning),
        "estimated_unique_at_20_interviews": round(min(20, weighted_depth), 1),
        "estimated_unique_at_100_interviews": round(min(100, weighted_depth), 1),
        "estimated_reuse_at_100_interviews_pct": round(
            max(0.0, (1 - min(100, weighted_depth) / 100) * 100),
            1,
        ),
        "matches_7c_final_observation": {
            "observed_unique_rate_100_interviews_pct": 38.6,
            "observed_written_area_unique_per_100": 20,
            "note": "FINAL audit showed ~20 unique/area at n=100 for written areas",
        },
    }


def _corpus_addition_recommendations(
    area_summaries: dict[str, dict],
    profiles: list[ProfileDepth],
) -> list[dict]:
    recommendations: list[dict] = []

    for area in TARGET_AREAS:
        area_profiles = [p for p in profiles if p.area == area]
        critical_slices = [
            p for p in area_profiles if p.depth_class in {"CRITICAL", "WARNING"}
        ]

        target_depth = 20
        docs_needed = sum(max(0, target_depth - p.effective_depth) for p in critical_slices)

        recommendations.append(
            {
                "area": area,
                "average_depth": area_summaries[area]["average_depth"],
                "minimum_depth": area_summaries[area]["minimum_depth"],
                "critical_warning_profiles": len(critical_slices),
                "recommended_new_documents": docs_needed,
                "priority_slices": [
                    {
                        "profile": f"{p.role}/{p.seniority}",
                        "effective_depth": p.effective_depth,
                        "strict_pool": p.strict_pool,
                        "add_to_reach_20": max(0, 20 - p.effective_depth),
                    }
                    for p in sorted(
                        critical_slices,
                        key=lambda item: item.effective_depth,
                    )[:12]
                ],
            }
        )

    recommendations.sort(
        key=lambda item: item["recommended_new_documents"],
        reverse=True,
    )

    return recommendations


def run_audit() -> dict:
    load_dotenv(PROJECT_ROOT / ".env")

    query_builder = RetrievalQueryBuilder()
    strategy_resolver = RetrievalStrategyResolver()
    adapter = RetrievalStrategyContextAdapter()
    chroma = ChromaRetrievalService()
    policy = AdaptiveRetrievalPolicy()
    adaptive = AdaptiveRetrievalService()

    profiles: list[ProfileDepth] = []

    for area in TARGET_AREAS:
        interview_area = AREA_ENUM[area]

        for role in AUDIT_ROLES:
            for seniority in SeniorityLevel:
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

                context = _build_context(
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
                    context=context,
                    query=query,
                )

                pre_pool = _pre_selection_pool(
                    adaptive=adaptive,
                    query=query,
                    context=context,
                )
                retrieval_pool = len(pre_pool)
                unique_ceiling = len({_document_id(c) for c in pre_pool if _document_id(c)})

                effective_depth, exhaustion_point, _ = _simulate_effective_depth(
                    adaptive=adaptive,
                    query=query,
                    context_builder_fn=lambda mem: _build_context(
                        adapter=adapter,
                        query=query,
                        strategy=strategy,
                        role=role,
                        seniority=seniority,
                        area=area,
                        memory=mem,
                    ),
                )

                profiles.append(
                    ProfileDepth(
                        area=area,
                        role=role.value,
                        seniority=seniority.value,
                        strict_pool=strict_pool,
                        retrieval_pool=retrieval_pool,
                        unique_document_ceiling=unique_ceiling,
                        effective_depth=effective_depth,
                        exhaustion_point=exhaustion_point,
                        depth_class=_classify_depth(effective_depth),
                    )
                )

    area_summaries = {
        area: _area_summary([p for p in profiles if p.area == area])
        for area in TARGET_AREAS
    }

    ranked = sorted(profiles, key=lambda p: p.effective_depth)

    global_ranking = {
        "shallowest_profiles": [asdict(p) for p in ranked[:15]],
        "deepest_profiles": [asdict(p) for p in ranked[-10:]],
    }

    return {
        "audit": "Phase 7D-A Technical Corpus Depth",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "methodology": {
            "strict_pool": "Chroma strict filter (role+seniority+area+difficulty[2-4]), k=200",
            "retrieval_pool": "Production staged retrieval pre-selection pool size",
            "unique_document_ceiling": "Unique document IDs in retrieval pool",
            "effective_depth": "Distinct fresh-start picks before unavoidable repetition (simulated)",
            "fresh_start_rotation": "ConstrainedEquivalenceBand cross-interview pick counts reset per profile slice",
            "target_difficulty": FRESH_START_DIFFICULTY,
        },
        "area_summaries": area_summaries,
        "profiles": [asdict(p) for p in profiles],
        "profile_ranking": global_ranking,
        "saturation_forecast": {
            area: _saturation_forecast([p for p in profiles if p.area == area])
            for area in TARGET_AREAS
        },
        "recommended_corpus_additions": _corpus_addition_recommendations(
            area_summaries,
            profiles,
        ),
        "classification_thresholds": {
            "CRITICAL": "<10",
            "WARNING": "10-20",
            "ACCEPTABLE": "20-40",
            "HEALTHY": ">40",
        },
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_audit()

    output_path = OUTPUT_DIR / "phase_7d_a_technical_corpus_depth_audit.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary = {
        key: report[key]
        for key in report
        if key != "profiles"
    }

    summary_path = OUTPUT_DIR / "phase_7d_a_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    main()
