# scripts/question_intelligence/audit_case_study_retrieval_budget.py

# Phase 7D-E0 — Case Study Retrieval Budget Audit (read-only).
#
# Validates whether technical_case_study diversity is constrained by corpus depth
# or by the retrieval budget (fetch_k cap) for every (role, seniority) slice.
#
# Key question: does the 415-doc deficit from Phase 7D-D shrink once retrieval-
# constrained slices are excluded (i.e. slices where more corpus already exists
# but fetch_k=3 hides it)?

from __future__ import annotations

import builtins
import contextlib
import io
import json
import time
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
from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.retrieval.adaptive_retrieval_policy import (
    AdaptiveRetrievalPolicy,
)
from services.question_corpus.retrieval.chroma_retrieval_service import (
    ChromaRetrievalService,
)
from services.question_corpus.retrieval.coverage_penalty_engine import (
    CoveragePenaltyEngine,
)
from services.question_corpus.retrieval.question_repetition_filter import (
    QuestionRepetitionFilter,
)
from services.question_corpus.retrieval.weak_domain_boost_engine import (
    WeakDomainBoostEngine,
)
from services.question_intelligence.adapters.retrieval_strategy_context_adapter import (
    RetrievalStrategyContextAdapter,
)
from services.question_intelligence.constrained_equivalence_band import (
    CANONICAL_FRESH_START_AREAS,
    reset_cross_interview_pick_counts,
)
from services.question_intelligence.performance_responsive_candidate_selector import (
    PerformanceResponsiveCandidateSelector,
)
from services.question_intelligence.retrieval.retrieval_strategy_resolver import (
    RetrievalStrategyResolver,
)
from services.question_intelligence.retrieval_query_builder import RetrievalQueryBuilder

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"

AREA = "technical_case_study"
INTERVIEW_AREA = InterviewArea.TECH_CASE_STUDY

FETCH_K_VALUES = [3, 10, 20, 50]
CORPUS_PROBE_K = 200
MAX_SIMULATION_INTERVIEWS = 500
HEALTHY_THRESHOLD = 20

# Phase 7D-D baseline for comparison
PHASE_7D_D_CASE_STUDY_DOCS_NEEDED = 415

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

ConstraintClass = Literal["RETRIEVAL_CONSTRAINED", "CORPUS_CONSTRAINED", "MIXED"]

_ORIGINAL_PRINT = builtins.print


def _quiet_print(*args: object, **kwargs: object) -> None:
    message = " ".join(str(arg) for arg in args)
    if message.startswith(("SIMILARITY:", "EMBEDDING:", "penalty:")):
        return
    _ORIGINAL_PRINT(*args, **kwargs)


@dataclass
class SliceSweepResult:
    role: str
    seniority: str
    strict_pool: int
    retrieval_pool_k3: int
    retrieval_pool_k10: int
    retrieval_pool_k20: int
    retrieval_pool_k50: int
    effective_depth_k3: int
    effective_depth_k10: int
    effective_depth_k20: int
    effective_depth_k50: int
    hidden_corpus: int
    constraint_class: ConstraintClass
    required_docs_to_depth_20_at_k3: int
    required_docs_to_depth_20_at_k50: int
    depth_gain_k3_to_k50: int


def _document_id(candidate: RetrievalCandidate) -> str:
    return str(candidate.document.metadata.get("document_id", ""))


def _score(candidate: RetrievalCandidate) -> float:
    return float(candidate.adaptive_score or candidate.final_score)


def _search_with_rerank_cap(
    *,
    chroma: ChromaRetrievalService,
    query: str,
    filters: object,
    chroma_k: int,
) -> list[RetrievalCandidate]:
    where = chroma._filter_builder.build(filters)
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            results = chroma._vectorstore.similarity_search_with_score(
                query=query,
                k=chroma_k,
                filter=where,
            )
            break
        except Exception as exc:
            last_error = exc
            time.sleep(1 + attempt)
    else:
        raise last_error if last_error is not None else RuntimeError("Chroma search failed")

    candidates: list[RetrievalCandidate] = []
    for document, distance in results:
        candidates.append(
            chroma._scorer.score(
                document=document,
                semantic_distance=distance,
            )
        )

    candidates.sort(key=_score, reverse=True)

    with contextlib.redirect_stdout(io.StringIO()):
        return chroma._diversity_reranker.rerank(
            candidates=candidates,
            top_k=min(chroma_k, len(candidates)),
        )


def _retrieve_staged_pool(
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    repetition_filter: QuestionRepetitionFilter,
    query: str,
    context: AdaptiveRetrievalContext,
    chroma_k: int,
) -> list[RetrievalCandidate]:
    filter_stages = policy.build_relaxation_stages(context)
    memory = context.memory
    best_undersized: list[RetrievalCandidate] = []

    for stage_filters in filter_stages:
        stage_candidates = _search_with_rerank_cap(
            chroma=chroma,
            query=query,
            filters=stage_filters,
            chroma_k=chroma_k,
        )
        filtered = repetition_filter.apply(
            candidates=stage_candidates,
            memory=memory,
        )

        if filtered:
            return filtered

        if len(filtered) > len(best_undersized):
            best_undersized = filtered

    return best_undersized


def _apply_post_retrieval(
    *,
    pool: list[RetrievalCandidate],
    context: AdaptiveRetrievalContext,
    coverage_engine: CoveragePenaltyEngine,
    weak_domain_engine: WeakDomainBoostEngine,
) -> list[RetrievalCandidate]:
    if not pool:
        return []

    adjusted = coverage_engine.apply(candidates=pool, context=context)
    adjusted = weak_domain_engine.apply(candidates=adjusted, context=context)
    adjusted.sort(key=_score, reverse=True)
    return adjusted


def _build_context(
    *,
    adapter: RetrievalStrategyContextAdapter,
    query: str,
    strategy: object,
    role: RoleType,
    seniority: SeniorityLevel,
    memory: InterviewRetrievalMemory,
) -> AdaptiveRetrievalContext:
    return adapter.adapt(
        query=query,
        retrieval_strategy=strategy,
        role=role.value,
        level=seniority.value,
        interview_type=InterviewType.TECHNICAL.value,
        area=AREA,
        memory=memory,
    )


def _strict_pool_count(
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    context: AdaptiveRetrievalContext,
    query: str,
) -> int:
    strict_filters = policy.build_relaxation_stages(context)[0]
    candidates = _search_with_rerank_cap(
        chroma=chroma,
        query=query,
        filters=strict_filters,
        chroma_k=CORPUS_PROBE_K,
    )
    return len({_document_id(c) for c in candidates if _document_id(c)})


def _simulate_effective_depth(
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    repetition_filter: QuestionRepetitionFilter,
    coverage_engine: CoveragePenaltyEngine,
    weak_domain_engine: WeakDomainBoostEngine,
    selector: PerformanceResponsiveCandidateSelector,
    adapter: RetrievalStrategyContextAdapter,
    query: str,
    strategy: object,
    role: RoleType,
    seniority: SeniorityLevel,
    chroma_k: int,
) -> int:
    reset_cross_interview_pick_counts()
    picked: set[str] = set()

    for _ in range(MAX_SIMULATION_INTERVIEWS):
        memory = InterviewRetrievalMemory()
        context = _build_context(
            adapter=adapter,
            query=query,
            strategy=strategy,
            role=role,
            seniority=seniority,
            memory=memory,
        )

        pool = _retrieve_staged_pool(
            chroma=chroma,
            policy=policy,
            repetition_filter=repetition_filter,
            query=query,
            context=context,
            chroma_k=chroma_k,
        )
        adjusted = _apply_post_retrieval(
            pool=pool,
            context=context,
            coverage_engine=coverage_engine,
            weak_domain_engine=weak_domain_engine,
        )

        with contextlib.redirect_stdout(io.StringIO()):
            selected = selector.select(pool=adjusted, context=context)

        if not selected:
            break

        doc_id = _document_id(selected[0])
        if not doc_id or doc_id in picked:
            break

        picked.add(doc_id)

    return len(picked)


def _retrieval_pool_at_k(
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    repetition_filter: QuestionRepetitionFilter,
    coverage_engine: CoveragePenaltyEngine,
    weak_domain_engine: WeakDomainBoostEngine,
    query: str,
    context: AdaptiveRetrievalContext,
    chroma_k: int,
) -> int:
    pool = _retrieve_staged_pool(
        chroma=chroma,
        policy=policy,
        repetition_filter=repetition_filter,
        query=query,
        context=context,
        chroma_k=chroma_k,
    )
    adjusted = _apply_post_retrieval(
        pool=pool,
        context=context,
        coverage_engine=coverage_engine,
        weak_domain_engine=weak_domain_engine,
    )
    return len(adjusted)


def _classify_constraint(
    *,
    strict_pool: int,
    retrieval_pool_k3: int,
    effective_depth_k50: int,
) -> ConstraintClass:
    # Retrieval constrained: large strict pool but tiny k=3 pool
    if strict_pool >= 20 and retrieval_pool_k3 <= 3:
        return "RETRIEVAL_CONSTRAINED"

    # Corpus constrained: strict pool itself is tiny
    if strict_pool < 10:
        return "CORPUS_CONSTRAINED"

    return "MIXED"


def _hidden_corpus_summary(slices: list[SliceSweepResult]) -> dict:
    hidden = [s.hidden_corpus for s in slices]
    retrieval_constrained = [s for s in slices if s.constraint_class == "RETRIEVAL_CONSTRAINED"]
    corpus_constrained = [s for s in slices if s.constraint_class == "CORPUS_CONSTRAINED"]
    mixed = [s for s in slices if s.constraint_class == "MIXED"]

    return {
        "total_hidden_corpus": sum(hidden),
        "avg_hidden_corpus": round(mean(hidden), 1) if hidden else 0.0,
        "max_hidden_corpus": max(hidden) if hidden else 0,
        "slices_retrieval_constrained": len(retrieval_constrained),
        "slices_corpus_constrained": len(corpus_constrained),
        "slices_mixed": len(mixed),
        "retrieval_constrained_profiles": [
            f"{s.role}/{s.seniority}" for s in retrieval_constrained
        ],
        "corpus_constrained_profiles": [
            f"{s.role}/{s.seniority}" for s in corpus_constrained
        ],
    }


def _depth_gain_summary(slices: list[SliceSweepResult]) -> dict:
    gains = [s.depth_gain_k3_to_k50 for s in slices]
    depths_k3 = [s.effective_depth_k3 for s in slices]
    depths_k10 = [s.effective_depth_k10 for s in slices]
    depths_k20 = [s.effective_depth_k20 for s in slices]
    depths_k50 = [s.effective_depth_k50 for s in slices]

    return {
        "avg_depth_k3": round(mean(depths_k3), 1),
        "avg_depth_k10": round(mean(depths_k10), 1),
        "avg_depth_k20": round(mean(depths_k20), 1),
        "avg_depth_k50": round(mean(depths_k50), 1),
        "min_depth_k3": min(depths_k3),
        "max_depth_k3": max(depths_k3),
        "min_depth_k50": min(depths_k50),
        "max_depth_k50": max(depths_k50),
        "avg_gain_k3_to_k50": round(mean(gains), 1),
        "max_gain": max(gains),
        "slices_reaching_depth_20_at_k50": sum(
            1 for s in slices if s.effective_depth_k50 >= HEALTHY_THRESHOLD
        ),
        "slices_remaining_critical_at_k50": sum(
            1 for s in slices if s.effective_depth_k50 < 10
        ),
    }


def _recalculated_deficit(slices: list[SliceSweepResult]) -> dict:
    # After removing retrieval-constrained slices (fetch_k increase resolves them)
    retrieval_constrained = [s for s in slices if s.constraint_class == "RETRIEVAL_CONSTRAINED"]
    truly_corpus_limited = [
        s for s in slices if s.constraint_class != "RETRIEVAL_CONSTRAINED"
    ]

    # Deficit at k=3 (current production)
    deficit_k3 = sum(s.required_docs_to_depth_20_at_k3 for s in slices)

    # Deficit at k=50 (after retrieval expansion) for corpus-limited slices only
    deficit_after_retrieval_fix = sum(s.required_docs_to_depth_20_at_k50 for s in slices)

    # Deficit for truly corpus-limited slices at k=50
    deficit_corpus_only = sum(s.required_docs_to_depth_20_at_k50 for s in truly_corpus_limited)

    savings = deficit_k3 - deficit_after_retrieval_fix
    pct_reduction = round(savings / deficit_k3 * 100, 1) if deficit_k3 else 0.0

    return {
        "phase_7d_d_estimate": PHASE_7D_D_CASE_STUDY_DOCS_NEEDED,
        "deficit_at_k3_production": deficit_k3,
        "deficit_after_retrieval_expansion_k50": deficit_after_retrieval_fix,
        "deficit_corpus_limited_slices_only": deficit_corpus_only,
        "savings_from_retrieval_expansion": savings,
        "pct_reduction_from_retrieval_fix": pct_reduction,
        "slices_resolved_by_retrieval_expansion": sum(
            1 for s in retrieval_constrained if s.effective_depth_k50 >= HEALTHY_THRESHOLD
        ),
        "estimate_is_materially_overstated": savings >= 100,
        "note": (
            f"Phase 7D-D estimated {PHASE_7D_D_CASE_STUDY_DOCS_NEEDED} new docs needed. "
            f"After accounting for retrieval budget, true corpus deficit is "
            f"{deficit_after_retrieval_fix} docs (savings={savings}, {pct_reduction}% reduction)."
        ),
    }


def _five_questions(
    slices: list[SliceSweepResult],
    hidden_summary: dict,
    depth_gain: dict,
    recalc: dict,
) -> dict:
    return {
        "Q1_retrieval_constrained_slices": hidden_summary["slices_retrieval_constrained"],
        "Q2_corpus_constrained_slices": hidden_summary["slices_corpus_constrained"],
        "Q3_effective_depth_unlocked_by_fetch_k_expansion": {
            "avg_depth_gain_k3_to_k50": depth_gain["avg_gain_k3_to_k50"],
            "max_gain": depth_gain["max_gain"],
            "slices_reaching_depth_20_at_k50": depth_gain["slices_reaching_depth_20_at_k50"],
        },
        "Q4_corpus_authoring_still_required": recalc["deficit_after_retrieval_expansion_k50"] > 0,
        "Q5_recalculated_document_deficit": {
            "original_estimate": recalc["phase_7d_d_estimate"],
            "after_retrieval_fix": recalc["deficit_after_retrieval_expansion_k50"],
            "savings": recalc["savings_from_retrieval_expansion"],
            "estimate_is_materially_overstated": recalc["estimate_is_materially_overstated"],
        },
    }


def run_audit() -> dict:
    load_dotenv(PROJECT_ROOT / ".env")

    builtins.print = _quiet_print

    chroma = ChromaRetrievalService()
    policy = AdaptiveRetrievalPolicy()
    repetition_filter = QuestionRepetitionFilter()
    coverage_engine = CoveragePenaltyEngine()
    weak_domain_engine = WeakDomainBoostEngine()
    selector = PerformanceResponsiveCandidateSelector()
    query_builder = RetrievalQueryBuilder()
    strategy_resolver = RetrievalStrategyResolver()
    adapter = RetrievalStrategyContextAdapter()

    total = len(AUDIT_ROLES) * len(list(SeniorityLevel))
    completed = 0

    _ORIGINAL_PRINT(f"Phase 7D-E0: Auditing {total} case-study slices × {len(FETCH_K_VALUES)} fetch_k values...", flush=True)

    slices: list[SliceSweepResult] = []

    for role in AUDIT_ROLES:
        for seniority in SeniorityLevel:
            completed += 1
            _ORIGINAL_PRINT(f"  [{completed}/{total}] {role.value}/{seniority.value}", flush=True)

            memory = InterviewRetrievalMemory()
            query = query_builder.build(
                role=role,
                level=seniority,
                area=INTERVIEW_AREA,
                memory=memory,
            )
            strategy = strategy_resolver.resolve(
                area=INTERVIEW_AREA,
                level=seniority,
                questions_per_area=QUESTIONS_PER_AREA,
            )

            base_context = _build_context(
                adapter=adapter,
                query=query,
                strategy=strategy,
                role=role,
                seniority=seniority,
                memory=InterviewRetrievalMemory(),
            )

            strict_pool = _strict_pool_count(
                chroma=chroma,
                policy=policy,
                context=base_context,
                query=query,
            )

            # Retrieval pool sizes at each fetch_k
            pool_sizes: dict[int, int] = {}
            for k in FETCH_K_VALUES:
                ctx = _build_context(
                    adapter=adapter,
                    query=query,
                    strategy=strategy,
                    role=role,
                    seniority=seniority,
                    memory=InterviewRetrievalMemory(),
                )
                pool_sizes[k] = _retrieval_pool_at_k(
                    chroma=chroma,
                    policy=policy,
                    repetition_filter=repetition_filter,
                    coverage_engine=coverage_engine,
                    weak_domain_engine=weak_domain_engine,
                    query=query,
                    context=ctx,
                    chroma_k=k,
                )

            # Effective depth at each fetch_k
            depths: dict[int, int] = {}
            for k in FETCH_K_VALUES:
                _ORIGINAL_PRINT(f"    fetch_k={k}...", flush=True)
                depths[k] = _simulate_effective_depth(
                    chroma=chroma,
                    policy=policy,
                    repetition_filter=repetition_filter,
                    coverage_engine=coverage_engine,
                    weak_domain_engine=weak_domain_engine,
                    selector=selector,
                    adapter=adapter,
                    query=query,
                    strategy=strategy,
                    role=role,
                    seniority=seniority,
                    chroma_k=k,
                )
                _ORIGINAL_PRINT(f"      → depth={depths[k]}", flush=True)

            hidden = max(0, strict_pool - pool_sizes[3])
            constraint = _classify_constraint(
                strict_pool=strict_pool,
                retrieval_pool_k3=pool_sizes[3],
                effective_depth_k50=depths[50],
            )

            slices.append(
                SliceSweepResult(
                    role=role.value,
                    seniority=seniority.value,
                    strict_pool=strict_pool,
                    retrieval_pool_k3=pool_sizes[3],
                    retrieval_pool_k10=pool_sizes[10],
                    retrieval_pool_k20=pool_sizes[20],
                    retrieval_pool_k50=pool_sizes[50],
                    effective_depth_k3=depths[3],
                    effective_depth_k10=depths[10],
                    effective_depth_k20=depths[20],
                    effective_depth_k50=depths[50],
                    hidden_corpus=hidden,
                    constraint_class=constraint,
                    required_docs_to_depth_20_at_k3=max(0, HEALTHY_THRESHOLD - depths[3]),
                    required_docs_to_depth_20_at_k50=max(0, HEALTHY_THRESHOLD - depths[50]),
                    depth_gain_k3_to_k50=depths[50] - depths[3],
                )
            )

    builtins.print = _ORIGINAL_PRINT

    hidden_summary = _hidden_corpus_summary(slices)
    depth_gain = _depth_gain_summary(slices)
    recalc = _recalculated_deficit(slices)
    five_q = _five_questions(slices, hidden_summary, depth_gain, recalc)

    print(
        f"\nDone. Retrieval-constrained={hidden_summary['slices_retrieval_constrained']} "
        f"Corpus-constrained={hidden_summary['slices_corpus_constrained']} "
        f"Mixed={hidden_summary['slices_mixed']}",
        flush=True,
    )
    print(f"Original 7D-D deficit: {PHASE_7D_D_CASE_STUDY_DOCS_NEEDED}  After retrieval fix: {recalc['deficit_after_retrieval_expansion_k50']}", flush=True)

    return {
        "audit": "Phase 7D-E0 Case Study Retrieval Budget Audit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "area": AREA,
            "roles": [r.value for r in AUDIT_ROLES],
            "seniorities": [s.value for s in SeniorityLevel],
            "total_slices": len(slices),
            "fetch_k_values": FETCH_K_VALUES,
            "corpus_probe_k": CORPUS_PROBE_K,
            "max_simulation_interviews": MAX_SIMULATION_INTERVIEWS,
            "healthy_threshold": HEALTHY_THRESHOLD,
            "context": "Post-7D-C1: technical_case_study in CANONICAL_FRESH_START_AREAS",
            "phase_7d_d_baseline_docs_needed": PHASE_7D_D_CASE_STUDY_DOCS_NEEDED,
        },
        "canonical_rotation_active": AREA in CANONICAL_FRESH_START_AREAS,
        "classification_criteria": {
            "RETRIEVAL_CONSTRAINED": "strict_pool >= 20 AND retrieval_pool(k=3) <= 3",
            "CORPUS_CONSTRAINED": "strict_pool < 10",
            "MIXED": "everything else",
        },
        "hidden_corpus_summary": hidden_summary,
        "depth_gain_summary": depth_gain,
        "recalculated_deficit": recalc,
        "five_questions": five_q,
        "slices": [asdict(s) for s in slices],
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_audit()

    output_path = OUTPUT_DIR / "phase_7d_e0_case_study_retrieval_budget_audit.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary = {key: report[key] for key in report if key != "slices"}
    summary_path = OUTPUT_DIR / "phase_7d_e0_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    main()
