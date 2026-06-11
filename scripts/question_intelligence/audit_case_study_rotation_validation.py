# scripts/question_intelligence/audit_case_study_rotation_validation.py

# Phase 7D-C2 — Case Study Rotation Validation (read-only).
#
# Quantifies the diversity impact of the Phase 7D-C1 fix that added
# technical_case_study to CANONICAL_FRESH_START_AREAS.
#
# Methodology:
# - Reuses the same selection-path tracing from Phase 7D-C0
# - Reuses the same diversity measurement from Phase 7C-T1B / 7C-FINAL
# - Runs 20-interview and 100-interview samples with the same role/seniority mix
# - Compares Before (effective_depth=1, deterministic hash) vs After (C1 fix)

from __future__ import annotations

import builtins
import contextlib
import io
import json
import random
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from app.settings.constants import QUESTIONS_PER_AREA
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from infrastructure.llm.llm_adapter import DefaultLLMAdapter
from scripts.question_intelligence import audit_cross_interview_diversity as diversity_audit
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
    ConstrainedEquivalenceBand,
    _CROSS_INTERVIEW_PICK_COUNTS,
    reset_cross_interview_pick_counts,
)
from services.question_intelligence.interview_theme_memory import (
    get_interview_theme_anchor,
)
from services.question_intelligence.performance_responsive_candidate_selector import (
    PerformanceResponsiveCandidateSelector,
)
from services.question_intelligence.question_intelligence_provider import (
    QuestionIntelligenceProvider,
)
from services.question_intelligence.retrieval.retrieval_strategy_resolver import (
    RetrievalStrategyResolver,
)
from services.question_intelligence.retrieval_query_builder import RetrievalQueryBuilder

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"

AREA = "technical_case_study"
INTERVIEW_AREA = InterviewArea.TECH_CASE_STUDY

CORPUS_PROBE_K = 200
SWEEP_FETCH_K = 50
SELECTION_EVENTS_PER_PROFILE = 20

RANDOM_SEED = 20260611

# Same mix as Phase 7C-FINAL _build_interview_configs()
_FINAL_ROLES = [
    RoleType.BACKEND_ENGINEER,
    RoleType.FULLSTACK_ENGINEER,
    RoleType.FRONTEND_ENGINEER,
    RoleType.DATA_ENGINEER,
    RoleType.DEVOPS_ENGINEER,
    RoleType.QA_ENGINEER,
    RoleType.ML_ENGINEER,
]

# Profiles matching Phase 7D-C0 for selection-depth comparison
SELECTION_DEPTH_PROFILES = [
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.DATA_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.MID),
    (RoleType.FRONTEND_ENGINEER, SeniorityLevel.MID),
]

# Before-state baselines from Phase 7D-C0 (effective_depth=1 for all profiles)
BEFORE_BASELINES = {
    "effective_depth": 1,
    "tie_break_strategy": "deterministic_hash_ordering",
    "selection_strategy": "non_canonical_fresh_start_equivalence",
    "technical_case_study_in_canonical": False,
    "source_phase": "7D-C0",
}

# Diversity baselines from Phase 7C-T1B and 7C-FINAL
DIVERSITY_BASELINES = {
    "t1b": {
        "interviews": 20,
        "case_study_unique": 17,
        "case_study_reuse_pct": 15.0,
        "global_reuse_pct": 18.0,
        "source": "phase_7c_t1b (pre-canonical-rotation)",
    },
    "final": {
        "interviews": 100,
        "case_study_reuse_pct": 35.0,
        "global_reuse_pct": 37.0,
        "source": "phase_7c_final t0 baseline estimate",
    },
}

_ORIGINAL_PRINT = builtins.print


def _quiet_print(*args: object, **kwargs: object) -> None:
    message = " ".join(str(arg) for arg in args)
    if message.startswith(("SIMILARITY:", "EMBEDDING:", "penalty:")):
        return
    _ORIGINAL_PRINT(*args, **kwargs)


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
    results = chroma._vectorstore.similarity_search_with_score(
        query=query,
        k=chroma_k,
        filter=where,
    )

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


def _trace_selection(
    *,
    selector: PerformanceResponsiveCandidateSelector,
    band: ConstrainedEquivalenceBand,
    reranked: list[RetrievalCandidate],
    context: AdaptiveRetrievalContext,
) -> dict:
    target = context.target_difficulty

    if target is None or not reranked:
        return {
            "selection_strategy": "score_only_no_target",
            "tie_break_strategy": "retrieval_rank",
            "equivalence_band": 0,
            "equivalence_band_ids": [],
            "final_winner": _document_id(reranked[0]) if reranked else "",
            "fresh_start": False,
            "in_canonical_fresh_start_areas": AREA in CANONICAL_FRESH_START_AREAS,
        }

    filtered_pool = selector._variety_scorer.filter_session_duplicates(
        pool=reranked,
        memory=context.memory,
    )
    rank_index = {id(candidate): index for index, candidate in enumerate(filtered_pool)}
    selected_bank_items: list = []

    viable = [
        candidate
        for candidate in filtered_pool
        if selector._candidate_difficulty(candidate) is not None
    ]

    if not viable:
        return {
            "selection_strategy": "none_no_viable_difficulty",
            "tie_break_strategy": "none",
            "equivalence_band": 0,
            "equivalence_band_ids": [],
            "final_winner": "",
            "fresh_start": False,
            "in_canonical_fresh_start_areas": AREA in CANONICAL_FRESH_START_AREAS,
        }

    previous = selector._previous_difficulty([], context)
    viable.sort(
        key=lambda candidate: selector._sort_key(
            candidate=candidate,
            rank=rank_index[id(candidate)],
            target=target,
            previous_difficulty=previous,
            context=context,
            selected_bank_items=selected_bank_items,
        )
    )

    best = viable[0]
    fresh_start = band._is_fresh_start(
        context=context,
        selected_bank_items=selected_bank_items,
    )

    band_anchor = best
    if fresh_start and context.target_area in CANONICAL_FRESH_START_AREAS:
        band_anchor = max(viable, key=band._candidate_score)

    best_tier = band._adaptive_tier(
        candidate=band_anchor,
        target=target,
        previous_difficulty=previous,
    )

    equivalents = band._collect_equivalents(
        pool=viable,
        best=band_anchor,
        best_tier=best_tier,
        target=target,
        previous_difficulty=previous,
        context=context,
        selected_bank_items=selected_bank_items,
    )

    equivalent_ids = [_document_id(c) for c in equivalents if _document_id(c)]

    production_pick = band.diversify_pick(
        pool=viable,
        best=best,
        target=target,
        previous_difficulty=previous,
        context=context,
        rank_index=rank_index,
        selected_bank_items=selected_bank_items,
    )
    winner = _document_id(production_pick)

    theme = get_interview_theme_anchor(context.memory) or ""
    query_str = context.retrieval_query or ""
    seed = f"{context.current_role}|{context.seniority}|{theme}|{query_str}"

    if fresh_start and AREA in CANONICAL_FRESH_START_AREAS:
        selection_strategy = "canonical_fresh_start_rotation"
        tie_break_strategy = "usage_count_rotation"
    elif len(equivalents) < 2:
        selection_strategy = "score_only_short_band"
        tie_break_strategy = "performance_responsive_sort_key"
    else:
        selection_strategy = "non_canonical_fresh_start_equivalence"
        tie_break_strategy = "deterministic_hash_ordering"

    return {
        "selection_strategy": selection_strategy,
        "tie_break_strategy": tie_break_strategy,
        "equivalence_band": len(equivalents),
        "equivalence_band_ids": equivalent_ids,
        "final_winner": winner,
        "fresh_start": fresh_start,
        "in_canonical_fresh_start_areas": AREA in CANONICAL_FRESH_START_AREAS,
        "seed": seed,
        "retrieval_pool": len(reranked),
    }


def _run_selection_depth_profile(
    *,
    role: RoleType,
    seniority: SeniorityLevel,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    repetition_filter: QuestionRepetitionFilter,
    coverage_engine: CoveragePenaltyEngine,
    weak_domain_engine: WeakDomainBoostEngine,
    selector: PerformanceResponsiveCandidateSelector,
    query_builder: RetrievalQueryBuilder,
    strategy_resolver: RetrievalStrategyResolver,
    adapter: RetrievalStrategyContextAdapter,
) -> dict:
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

    strict_filters = policy.build_relaxation_stages(base_context)[0]
    strict_raw = _search_with_rerank_cap(
        chroma=chroma,
        query=query,
        filters=strict_filters,
        chroma_k=CORPUS_PROBE_K,
    )
    strict_pool = len({_document_id(c) for c in strict_raw if _document_id(c)})

    reset_cross_interview_pick_counts()
    band = selector._equivalence_band

    unique_winners: set[str] = set()
    equivalence_band_sizes: list[int] = []
    retrieval_pool_sizes: list[int] = []
    events: list[dict] = []

    for index in range(1, SELECTION_EVENTS_PER_PROFILE + 1):
        context = _build_context(
            adapter=adapter,
            query=query,
            strategy=strategy,
            role=role,
            seniority=seniority,
            memory=InterviewRetrievalMemory(),
        )

        retrieval_raw = _retrieve_staged_pool(
            chroma=chroma,
            policy=policy,
            repetition_filter=repetition_filter,
            query=query,
            context=context,
            chroma_k=SWEEP_FETCH_K,
        )
        reranked = _apply_post_retrieval(
            pool=retrieval_raw,
            context=context,
            coverage_engine=coverage_engine,
            weak_domain_engine=weak_domain_engine,
        )

        trace = _trace_selection(
            selector=selector,
            band=band,
            reranked=reranked,
            context=context,
        )

        winner = trace["final_winner"]
        unique_winners.add(winner)
        equivalence_band_sizes.append(trace["equivalence_band"])
        retrieval_pool_sizes.append(trace["retrieval_pool"])

        events.append(
            {
                "index": index,
                "final_winner": winner,
                "equivalence_band": trace["equivalence_band"],
                "retrieval_pool": trace["retrieval_pool"],
                "selection_strategy": trace["selection_strategy"],
                "tie_break_strategy": trace["tie_break_strategy"],
                "fresh_start": trace["fresh_start"],
                "in_canonical_fresh_start_areas": trace["in_canonical_fresh_start_areas"],
                "cross_interview_pick_counts_snapshot": dict(_CROSS_INTERVIEW_PICK_COUNTS),
            }
        )

    effective_depth = len(unique_winners)

    avg_band = round(
        sum(equivalence_band_sizes) / len(equivalence_band_sizes), 1
    ) if equivalence_band_sizes else 0.0
    avg_retrieval = round(
        sum(retrieval_pool_sizes) / len(retrieval_pool_sizes), 1
    ) if retrieval_pool_sizes else 0.0

    return {
        "profile": f"{role.value}/{seniority.value}",
        "strict_pool": strict_pool,
        "retrieval_pool_avg": avg_retrieval,
        "retrieval_pool_min": min(retrieval_pool_sizes) if retrieval_pool_sizes else 0,
        "retrieval_pool_max": max(retrieval_pool_sizes) if retrieval_pool_sizes else 0,
        "equivalence_band_avg": avg_band,
        "equivalence_band_min": min(equivalence_band_sizes) if equivalence_band_sizes else 0,
        "equivalence_band_max": max(equivalence_band_sizes) if equivalence_band_sizes else 0,
        "effective_depth": effective_depth,
        "unique_winners": sorted(unique_winners),
        "selection_events": SELECTION_EVENTS_PER_PROFILE,
        "selection_strategy": events[0]["selection_strategy"] if events else "",
        "tie_break_strategy": events[0]["tie_break_strategy"] if events else "",
        "events": events,
    }


def _build_interview_configs(count: int) -> list[tuple[RoleType, SeniorityLevel]]:
    seniorities = list(SeniorityLevel)
    pool = [(role, seniority) for role in _FINAL_ROLES for seniority in seniorities]
    rng = random.Random(RANDOM_SEED)
    return [rng.choice(pool) for _ in range(count)]


def _run_diversity_sample(
    *,
    configs: list[tuple[RoleType, SeniorityLevel]],
    provider: QuestionIntelligenceProvider,
    label: str,
) -> dict:
    corpus_by_prompt = diversity_audit._load_corpus_index()
    all_rows: list[diversity_audit.DeliveredQuestion] = []
    failures: list[dict] = []

    for index, (role, level) in enumerate(configs, start=1):
        interview_id = f"c2-{label}-{index:03d}-{uuid.uuid4().hex[:8]}"

        if index % 10 == 0 or index == 1:
            builtins.print(
                f"  [{index}/{len(configs)}] {role.value} {level.value}",
                flush=True,
            )

        try:
            questions = diversity_audit._run_batch_interview(
                provider,
                InterviewType.TECHNICAL,
                role,
                level,
            )
        except Exception as exc:
            failures.append(
                {
                    "index": index,
                    "role": role.value,
                    "seniority": level.value,
                    "error": str(exc),
                }
            )
            continue

        rows = diversity_audit._collect_delivered(
            interview_id=interview_id,
            path="batch_generate",
            interview_type=InterviewType.TECHNICAL,
            role=role,
            level=level,
            questions=questions,
            corpus_by_prompt=corpus_by_prompt,
        )
        all_rows.extend(rows)

    case_rows = [row for row in all_rows if row.area == AREA]

    case_metrics = diversity_audit._global_metrics(case_rows)
    global_metrics = diversity_audit._global_metrics(all_rows)

    case_doc_counts = Counter(
        row.document_id for row in case_rows if row.document_id is not None
    )
    top_doc_share = 0.0
    top_doc_id = None

    if case_doc_counts and case_rows:
        top_entry = case_doc_counts.most_common(1)[0]
        top_doc_id = top_entry[0]
        top_doc_share = round((top_entry[1] / len(case_rows)) * 100, 1)

    return {
        "interviews_attempted": len(configs),
        "interviews_completed": len(configs) - len(failures),
        "failures": len(failures),
        "failure_details": failures[:5],
        "technical_case_study": {
            "total_prompts": case_metrics.total_prompts,
            "unique_prompts": case_metrics.unique_prompts,
            "reuse_pct": case_metrics.reuse_pct,
            "top_document_share_pct": top_doc_share,
            "top_document_id": top_doc_id,
        },
        "global_technical": {
            "total_prompts": global_metrics.total_prompts,
            "unique_prompts": global_metrics.unique_prompts,
            "reuse_pct": global_metrics.reuse_pct,
        },
    }


def _selection_depth_summary(profile_results: list[dict]) -> dict:
    depths = [r["effective_depth"] for r in profile_results]
    band_avgs = [r["equivalence_band_avg"] for r in profile_results]
    retrieval_avgs = [r["retrieval_pool_avg"] for r in profile_results]

    return {
        "effective_depth": {
            "min": min(depths),
            "avg": round(sum(depths) / len(depths), 1),
            "max": max(depths),
        },
        "equivalence_band_avg": {
            "min": round(min(band_avgs), 1),
            "avg": round(sum(band_avgs) / len(band_avgs), 1),
            "max": round(max(band_avgs), 1),
        },
        "retrieval_pool_avg": {
            "min": round(min(retrieval_avgs), 1),
            "avg": round(sum(retrieval_avgs) / len(retrieval_avgs), 1),
            "max": round(max(retrieval_avgs), 1),
        },
        "profiles_using_canonical_rotation": sum(
            1
            for r in profile_results
            if r["selection_strategy"] == "canonical_fresh_start_rotation"
        ),
        "profiles_total": len(profile_results),
    }


def _compute_verdict(
    depth_summary: dict,
    sample_20: dict,
    sample_100: dict,
) -> dict:
    avg_depth = depth_summary["effective_depth"]["avg"]
    reuse_20 = sample_20["technical_case_study"]["reuse_pct"]
    reuse_100 = sample_100["technical_case_study"]["reuse_pct"]

    strong = avg_depth > 10 and reuse_100 < 40.0
    moderate = avg_depth > 5 and reuse_100 < 60.0

    if strong:
        verdict = "SUCCESS"
        rationale = (
            f"effective_depth={avg_depth:.1f} > 10 and "
            f"reuse@100={reuse_100}% < 40% — canonical rotation is working as intended."
        )
    elif moderate:
        verdict = "PARTIAL_SUCCESS"
        rationale = (
            f"effective_depth={avg_depth:.1f} > 5 and "
            f"reuse@100={reuse_100}% < 60% — rotation improves diversity but depth ceiling remains."
        )
    else:
        verdict = "FAILURE"
        rationale = (
            f"effective_depth={avg_depth:.1f} near 1 or "
            f"reuse@100={reuse_100}% near 80% — canonical rotation fix did not materially improve diversity."
        )

    return {
        "verdict": verdict,
        "rationale": rationale,
        "metrics": {
            "avg_effective_depth": avg_depth,
            "min_effective_depth": depth_summary["effective_depth"]["min"],
            "max_effective_depth": depth_summary["effective_depth"]["max"],
            "reuse_pct_20_interviews": reuse_20,
            "reuse_pct_100_interviews": reuse_100,
        },
        "criteria": {
            "strong_success": {
                "threshold": "effective_depth > 10 AND reuse@100 < 40%",
                "met": strong,
            },
            "moderate_success": {
                "threshold": "effective_depth > 5 AND reuse@100 < 60%",
                "met": moderate,
            },
        },
    }


def _before_after_delta(
    *,
    sample_20: dict,
    sample_100: dict,
    depth_summary: dict,
) -> dict:
    cs_20 = sample_20["technical_case_study"]
    cs_100 = sample_100["technical_case_study"]

    # Before baselines from 7D-C0 + 7C-T1B
    before_unique_20 = DIVERSITY_BASELINES["t1b"]["case_study_unique"]
    before_reuse_20 = DIVERSITY_BASELINES["t1b"]["case_study_reuse_pct"]
    before_reuse_100 = DIVERSITY_BASELINES["final"]["case_study_reuse_pct"]
    before_depth = BEFORE_BASELINES["effective_depth"]

    return {
        "unique_prompts_20": {
            "before": before_unique_20,
            "after": cs_20["unique_prompts"],
            "delta": cs_20["unique_prompts"] - before_unique_20,
        },
        "reuse_pct_20": {
            "before": before_reuse_20,
            "after": cs_20["reuse_pct"],
            "delta": round(cs_20["reuse_pct"] - before_reuse_20, 1),
        },
        "reuse_pct_100": {
            "before": before_reuse_100,
            "after": cs_100["reuse_pct"],
            "delta": round(cs_100["reuse_pct"] - before_reuse_100, 1),
        },
        "top_document_share_20": {
            "before": "unknown",
            "after": cs_20["top_document_share_pct"],
        },
        "top_document_share_100": {
            "before": "unknown",
            "after": cs_100["top_document_share_pct"],
        },
        "effective_depth": {
            "before": before_depth,
            "after_avg": depth_summary["effective_depth"]["avg"],
            "after_min": depth_summary["effective_depth"]["min"],
            "after_max": depth_summary["effective_depth"]["max"],
            "delta_avg": round(depth_summary["effective_depth"]["avg"] - before_depth, 1),
        },
    }


def run_audit() -> dict:
    load_dotenv(PROJECT_ROOT / ".env")

    builtins.print("Phase 7D-C2: Case Study Rotation Validation", flush=True)
    builtins.print("=" * 60, flush=True)

    # ── Selection depth measurement ──────────────────────────────
    builtins.print(
        "\n[1/3] Selection depth audit "
        f"({len(SELECTION_DEPTH_PROFILES)} profiles × {SELECTION_EVENTS_PER_PROFILE} events)...",
        flush=True,
    )

    chroma = ChromaRetrievalService()
    policy = AdaptiveRetrievalPolicy()
    repetition_filter = QuestionRepetitionFilter()
    coverage_engine = CoveragePenaltyEngine()
    weak_domain_engine = WeakDomainBoostEngine()
    selector = PerformanceResponsiveCandidateSelector()
    query_builder = RetrievalQueryBuilder()
    strategy_resolver = RetrievalStrategyResolver()
    adapter = RetrievalStrategyContextAdapter()

    profile_results: list[dict] = []

    for role, seniority in SELECTION_DEPTH_PROFILES:
        builtins.print(f"  {role.value}/{seniority.value}...", flush=True)
        result = _run_selection_depth_profile(
            role=role,
            seniority=seniority,
            chroma=chroma,
            policy=policy,
            repetition_filter=repetition_filter,
            coverage_engine=coverage_engine,
            weak_domain_engine=weak_domain_engine,
            selector=selector,
            query_builder=query_builder,
            strategy_resolver=strategy_resolver,
            adapter=adapter,
        )
        profile_results.append(result)
        builtins.print(
            f"    → effective_depth={result['effective_depth']} "
            f"band_avg={result['equivalence_band_avg']} "
            f"strategy={result['selection_strategy']}",
            flush=True,
        )

    depth_summary = _selection_depth_summary(profile_results)

    # ── Diversity sample: 20 interviews ──────────────────────────
    builtins.print("\n[2/3] Diversity sample: 20 interviews...", flush=True)

    configs_20 = _build_interview_configs(20)
    llm = DefaultLLMAdapter()
    provider = QuestionIntelligenceProvider(llm)

    sample_20 = _run_diversity_sample(
        configs=configs_20,
        provider=provider,
        label="20",
    )
    builtins.print(
        f"  → case_study reuse={sample_20['technical_case_study']['reuse_pct']}% "
        f"unique={sample_20['technical_case_study']['unique_prompts']}",
        flush=True,
    )

    # ── Diversity sample: 100 interviews ─────────────────────────
    builtins.print("\n[3/3] Diversity sample: 100 interviews...", flush=True)

    configs_100 = _build_interview_configs(100)
    sample_100 = _run_diversity_sample(
        configs=configs_100,
        provider=provider,
        label="100",
    )
    builtins.print(
        f"  → case_study reuse={sample_100['technical_case_study']['reuse_pct']}% "
        f"unique={sample_100['technical_case_study']['unique_prompts']}",
        flush=True,
    )

    # ── Verdict & deltas ─────────────────────────────────────────
    verdict = _compute_verdict(
        depth_summary=depth_summary,
        sample_20=sample_20,
        sample_100=sample_100,
    )
    before_after = _before_after_delta(
        sample_20=sample_20,
        sample_100=sample_100,
        depth_summary=depth_summary,
    )

    builtins.print(f"\nVerdict: {verdict['verdict']}", flush=True)
    builtins.print(f"  {verdict['rationale']}", flush=True)

    return {
        "audit": "Phase 7D-C2 Case Study Rotation Validation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "area": AREA,
            "fix_phase": "7D-C1",
            "fix_description": "technical_case_study added to CANONICAL_FRESH_START_AREAS",
            "random_seed": RANDOM_SEED,
            "selection_depth_profiles": [
                f"{role.value}/{sen.value}" for role, sen in SELECTION_DEPTH_PROFILES
            ],
            "selection_events_per_profile": SELECTION_EVENTS_PER_PROFILE,
            "diversity_sample_sizes": [20, 100],
        },
        "canonical_state": {
            "technical_case_study_in_canonical": AREA in CANONICAL_FRESH_START_AREAS,
            "canonical_fresh_start_areas": sorted(CANONICAL_FRESH_START_AREAS),
        },
        "selection_depth": {
            "summary": depth_summary,
            "profiles": [
                {
                    "profile": r["profile"],
                    "strict_pool": r["strict_pool"],
                    "retrieval_pool_avg": r["retrieval_pool_avg"],
                    "equivalence_band_avg": r["equivalence_band_avg"],
                    "equivalence_band_min": r["equivalence_band_min"],
                    "equivalence_band_max": r["equivalence_band_max"],
                    "effective_depth": r["effective_depth"],
                    "selection_strategy": r["selection_strategy"],
                    "tie_break_strategy": r["tie_break_strategy"],
                }
                for r in profile_results
            ],
            "full_profile_results": profile_results,
        },
        "diversity_20": sample_20,
        "diversity_100": sample_100,
        "before_after": before_after,
        "before_baselines": BEFORE_BASELINES,
        "diversity_baselines": DIVERSITY_BASELINES,
        "verdict": verdict,
    }


def main() -> None:
    builtins.print = _quiet_print
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_audit()

    builtins.print = _ORIGINAL_PRINT

    output_path = OUTPUT_DIR / "phase_7d_c2_case_study_rotation_validation.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary: dict = {
        key: report[key]
        for key in report
        if key != "selection_depth"
    }
    summary["selection_depth_summary"] = report["selection_depth"]["summary"]
    summary["selection_depth_profiles"] = report["selection_depth"]["profiles"]

    summary_path = OUTPUT_DIR / "phase_7d_c2_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    main()
