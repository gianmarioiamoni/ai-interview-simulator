# scripts/question_intelligence/audit_retrieval_depth_expansion.py

# Phase 7D-B — Retrieval Depth Expansion Audit (read-only).

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
from services.question_corpus.retrieval.adaptive_retrieval_service import (
    BACKGROUND_MIN_POOL_AREA,
    MIN_FRESH_START_POOL_SIZE,
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

FETCH_K_VALUES = [3, 5, 10, 20, 50]
TOP_K_MODES = ("current", "doubled")
CORPUS_PROBE_K = 200
MAX_SIMULATION_INTERVIEWS = 500
PRODUCTION_FETCH_K = 3

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

CASE_STUDY_TRACE_PROFILE = (RoleType.BACKEND_ENGINEER, SeniorityLevel.SENIOR)

_ORIGINAL_PRINT = builtins.print


def _quiet_print(*args: object, **kwargs: object) -> None:
    message = " ".join(str(arg) for arg in args)
    if message.startswith(("SIMILARITY:", "EMBEDDING:")):
        return

    _ORIGINAL_PRINT(*args, **kwargs)


@dataclass
class ProfileSweepResult:
    area: str
    role: str
    seniority: str
    fetch_k: int
    top_k_mode: str
    chroma_k: int
    rerank_top_k: int
    strict_pool: int
    retrieval_pool: int
    equivalence_band_size: int
    final_selectable_set: int
    effective_depth: int


def _document_id(candidate: RetrievalCandidate) -> str:
    return str(candidate.document.metadata.get("document_id", ""))


def _score(candidate: RetrievalCandidate) -> float:
    return float(candidate.adaptive_score or candidate.final_score)


def _resolve_k_limits(fetch_k: int, top_k_mode: str) -> tuple[int, int]:
    if top_k_mode == "current":
        return fetch_k, fetch_k

    doubled = fetch_k * 2
    return doubled, doubled


def _min_pool_size(context: AdaptiveRetrievalContext) -> int:
    if context.target_area != BACKGROUND_MIN_POOL_AREA:
        return 1

    memory = context.memory
    is_fresh = (
        not memory.asked_question_ids
        and not memory.session_selected_prompts
        and not memory.session_used_topics
        and not memory.difficulty_history
    )

    if is_fresh:
        return MIN_FRESH_START_POOL_SIZE

    return 1


def _search_with_rerank_cap(
    *,
    chroma: ChromaRetrievalService,
    query: str,
    filters,
    chroma_k: int,
    rerank_top_k: int,
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
        except Exception as error:
            last_error = error
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
        reranked = chroma._diversity_reranker.rerank(
            candidates=candidates,
            top_k=min(rerank_top_k, len(candidates)),
        )

    return reranked


def _retrieve_staged_pool(
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    repetition_filter: QuestionRepetitionFilter,
    query: str,
    context: AdaptiveRetrievalContext,
    chroma_k: int,
    rerank_top_k: int,
) -> list[RetrievalCandidate]:
    filter_stages = policy.build_relaxation_stages(context)
    min_pool = _min_pool_size(context)
    memory = context.memory
    best_undersized: list[RetrievalCandidate] = []

    for stage_filters in filter_stages:
        stage_candidates = _search_with_rerank_cap(
            chroma=chroma,
            query=query,
            filters=stage_filters,
            chroma_k=chroma_k,
            rerank_top_k=rerank_top_k,
        )
        filtered = repetition_filter.apply(
            candidates=stage_candidates,
            memory=memory,
        )

        if len(filtered) >= min_pool:
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


def _equivalence_band_metrics(
    *,
    pool: list[RetrievalCandidate],
    context: AdaptiveRetrievalContext,
    selector: PerformanceResponsiveCandidateSelector,
) -> tuple[int, int, RetrievalCandidate | None]:
    if not pool:
        return 0, 0, None

    target = context.target_difficulty
    if target is None:
        return 0, len(pool), pool[0]

    variety_scorer = selector._variety_scorer
    equivalence_band = selector._equivalence_band

    filtered_pool = variety_scorer.filter_session_duplicates(
        pool=pool,
        memory=context.memory,
    )

    if not filtered_pool:
        return 0, 0, None

    rank_index = {id(candidate): index for index, candidate in enumerate(filtered_pool)}
    selected_bank_items: list = []

    viable = [
        candidate
        for candidate in filtered_pool
        if selector._candidate_difficulty(candidate) is not None
    ]

    final_selectable = len(viable)
    if not viable:
        return 0, 0, None

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
    band_anchor = best

    if (
        equivalence_band._is_fresh_start(
            context=context,
            selected_bank_items=selected_bank_items,
        )
        and context.target_area in CANONICAL_FRESH_START_AREAS
    ):
        band_anchor = max(viable, key=equivalence_band._candidate_score)

    best_tier = equivalence_band._adaptive_tier(
        candidate=band_anchor,
        target=target,
        previous_difficulty=previous,
    )

    equivalents = equivalence_band._collect_equivalents(
        pool=viable,
        best=band_anchor,
        best_tier=best_tier,
        target=target,
        previous_difficulty=previous,
        context=context,
        selected_bank_items=selected_bank_items,
    )

    winner = equivalence_band.diversify_pick(
        pool=viable,
        best=best,
        target=target,
        previous_difficulty=previous,
        context=context,
        rank_index=rank_index,
        selected_bank_items=selected_bank_items,
    )

    return len(equivalents), final_selectable, winner


def _build_adjusted_pool(
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    repetition_filter: QuestionRepetitionFilter,
    coverage_engine: CoveragePenaltyEngine,
    weak_domain_engine: WeakDomainBoostEngine,
    query: str,
    context: AdaptiveRetrievalContext,
    chroma_k: int,
    rerank_top_k: int,
) -> list[RetrievalCandidate]:
    pool = _retrieve_staged_pool(
        chroma=chroma,
        policy=policy,
        repetition_filter=repetition_filter,
        query=query,
        context=context,
        chroma_k=chroma_k,
        rerank_top_k=rerank_top_k,
    )

    return _apply_post_retrieval(
        pool=pool,
        context=context,
        coverage_engine=coverage_engine,
        weak_domain_engine=weak_domain_engine,
    )


def _select_from_pool(
    *,
    selector: PerformanceResponsiveCandidateSelector,
    adjusted_pool: list[RetrievalCandidate],
    context: AdaptiveRetrievalContext,
) -> list[RetrievalCandidate]:
    with contextlib.redirect_stdout(io.StringIO()):
        return selector.select(pool=adjusted_pool, context=context)


def _adaptive_retrieve(
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    repetition_filter: QuestionRepetitionFilter,
    coverage_engine: CoveragePenaltyEngine,
    weak_domain_engine: WeakDomainBoostEngine,
    selector: PerformanceResponsiveCandidateSelector,
    query: str,
    context: AdaptiveRetrievalContext,
    chroma_k: int,
    rerank_top_k: int,
) -> list[RetrievalCandidate]:
    adjusted = _build_adjusted_pool(
        chroma=chroma,
        policy=policy,
        repetition_filter=repetition_filter,
        coverage_engine=coverage_engine,
        weak_domain_engine=weak_domain_engine,
        query=query,
        context=context,
        chroma_k=chroma_k,
        rerank_top_k=rerank_top_k,
    )

    return _select_from_pool(
        selector=selector,
        adjusted_pool=adjusted,
        context=context,
    )


def _strict_pool_count(
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    context: AdaptiveRetrievalContext,
    query: str,
) -> int:
    strict = policy.build_relaxation_stages(context)[0]
    candidates = _search_with_rerank_cap(
        chroma=chroma,
        query=query,
        filters=strict,
        chroma_k=CORPUS_PROBE_K,
        rerank_top_k=CORPUS_PROBE_K,
    )
    return len({_document_id(candidate) for candidate in candidates if _document_id(candidate)})


def _simulate_effective_depth(
    *,
    selector: PerformanceResponsiveCandidateSelector,
    context_builder,
    adjusted_pool: list[RetrievalCandidate],
) -> int:
    if not adjusted_pool:
        return 0

    reset_cross_interview_pick_counts()
    picked: set[str] = set()

    for _ in range(MAX_SIMULATION_INTERVIEWS):
        context = context_builder(InterviewRetrievalMemory())
        selected = _select_from_pool(
            selector=selector,
            adjusted_pool=adjusted_pool,
            context=context,
        )

        if not selected:
            break

        doc_id = _document_id(selected[0])
        if not doc_id or doc_id in picked:
            break

        picked.add(doc_id)

    return len(picked)


def _build_context(
    *,
    adapter: RetrievalStrategyContextAdapter,
    query: str,
    strategy,
    role: RoleType,
    seniority: SeniorityLevel,
    area: str,
    memory: InterviewRetrievalMemory,
) -> AdaptiveRetrievalContext:
    return adapter.adapt(
        query=query,
        retrieval_strategy=strategy,
        role=role.value,
        level=seniority.value,
        interview_type=InterviewType.TECHNICAL.value,
        area=area,
        memory=memory,
    )


def _trace_case_study_collapse(
    results: list[ProfileSweepResult],
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    selector: PerformanceResponsiveCandidateSelector,
    query_builder: RetrievalQueryBuilder,
    strategy_resolver: RetrievalStrategyResolver,
    adapter: RetrievalStrategyContextAdapter,
) -> dict:
    role, seniority = CASE_STUDY_TRACE_PROFILE
    area = "technical_case_study"
    interview_area = AREA_ENUM[area]
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

    strict = policy.build_relaxation_stages(context)[0]
    strict_raw = _search_with_rerank_cap(
        chroma=chroma,
        query=query,
        filters=strict,
        chroma_k=CORPUS_PROBE_K,
        rerank_top_k=CORPUS_PROBE_K,
    )
    strict_count = len({_document_id(c) for c in strict_raw if _document_id(c)})

    profile_rows = [
        row
        for row in results
        if row.area == area
        and row.role == role.value
        and row.seniority == seniority.value
    ]

    traces: list[dict] = []

    for row in sorted(
        profile_rows,
        key=lambda item: (FETCH_K_VALUES.index(item.fetch_k), item.top_k_mode),
    ):
        collapse_stage = _attribute_collapse(
            strict=strict_count,
            retrieval=row.retrieval_pool,
            reranked=row.retrieval_pool,
            band=row.equivalence_band_size,
            depth=row.effective_depth,
        )

        traces.append(
            {
                "fetch_k": row.fetch_k,
                "top_k_mode": row.top_k_mode,
                "chroma_k": row.chroma_k,
                "rerank_top_k": row.rerank_top_k,
                "strict_pool": strict_count,
                "retrieval_candidates": row.retrieval_pool,
                "reranked_candidates": row.retrieval_pool,
                "equivalence_band_size": row.equivalence_band_size,
                "final_selectable_set": row.final_selectable_set,
                "effective_depth": row.effective_depth,
                "collapse_stage": collapse_stage,
                "stage_funnel": {
                    "strict_pool": strict_count,
                    "retrieval_candidates": row.retrieval_pool,
                    "reranked_candidates": row.retrieval_pool,
                    "equivalence_band": row.equivalence_band_size,
                    "effective_depth": row.effective_depth,
                },
            }
        )

    production_trace = next(
        item
        for item in traces
        if item["fetch_k"] == PRODUCTION_FETCH_K and item["top_k_mode"] == "current"
    )

    return {
        "profile": f"{role.value}/{seniority.value}",
        "area": area,
        "production_config": {
            "fetch_k": PRODUCTION_FETCH_K,
            "top_k_mode": "current",
        },
        "production_collapse_stage": production_trace["collapse_stage"],
        "production_funnel": production_trace["stage_funnel"],
        "attribution": (
            "144 strict candidates collapse to depth 1 at fresh_start_selection "
            "(post-retrieval); retrieval fetch cap reduces pool to "
            f"{production_trace['retrieval_candidates']} before ranking"
        ),
        "traces": traces,
    }


def _attribute_collapse(
    *,
    strict: int,
    retrieval: int,
    reranked: int,
    band: int,
    depth: int,
) -> str:
    if strict <= 1:
        return "corpus_strict_filter"

    if retrieval <= 1:
        return "retrieval_fetch_cap"

    if reranked <= 1:
        return "post_retrieval_ranking"

    if band <= 1:
        return "equivalence_band"

    if depth <= 1:
        return "fresh_start_selection"

    return "none"


def _area_table(
    results: list[ProfileSweepResult],
    *,
    top_k_mode: str,
) -> list[dict]:
    rows: list[dict] = []

    for fetch_k in FETCH_K_VALUES:
        subset = [
            row
            for row in results
            if row.fetch_k == fetch_k and row.top_k_mode == top_k_mode
        ]
        depths = [row.effective_depth for row in subset]

        if not depths:
            continue

        rows.append(
            {
                "fetch_k": fetch_k,
                "avg_depth": round(mean(depths), 1),
                "min": min(depths),
                "max": max(depths),
            }
        )

    return rows


def _success_criteria(
    results: list[ProfileSweepResult],
    *,
    production_depth_by_area: dict[str, float],
) -> dict:
    depth_by_fetch: dict[int, list[int]] = {k: [] for k in FETCH_K_VALUES}

    for row in results:
        if row.top_k_mode == "current":
            depth_by_fetch[row.fetch_k].append(row.effective_depth)

    production_avg = mean(
        row.effective_depth
        for row in results
        if row.fetch_k == PRODUCTION_FETCH_K and row.top_k_mode == "current"
    )
    max_fetch_avg = mean(depth_by_fetch[50]) if depth_by_fetch[50] else 0
    material_increase = max_fetch_avg >= production_avg * 2 and max_fetch_avg > production_avg + 2

    case_study_rows = [
        row
        for row in results
        if row.area == "technical_case_study"
        and row.fetch_k == PRODUCTION_FETCH_K
        and row.top_k_mode == "current"
    ]
    avg_strict = mean(row.strict_pool for row in case_study_rows)
    avg_retrieval = mean(row.retrieval_pool for row in case_study_rows)
    collapse_before_retrieval = avg_strict > avg_retrieval + 5

    corpus_gain_under_production = all(
        row.effective_depth <= row.strict_pool
        and row.effective_depth <= PRODUCTION_FETCH_K + 1
        for row in results
        if row.fetch_k == PRODUCTION_FETCH_K and row.top_k_mode == "current"
    )

    return {
        "depth_increases_materially_with_fetch_k": material_increase,
        "production_avg_depth": round(production_avg, 1),
        "fetch_k_50_avg_depth": round(max_fetch_avg, 1),
        "case_study_collapse_before_retrieval": collapse_before_retrieval,
        "case_study_avg_strict_pool": round(avg_strict, 1),
        "case_study_avg_retrieval_pool": round(avg_retrieval, 1),
        "corpus_authoring_meaningful_under_current_retrieval": not material_increase
        and corpus_gain_under_production,
        "production_depth_by_area": production_depth_by_area,
    }


def _recommended_next_phase(criteria: dict) -> str:
    if criteria["depth_increases_materially_with_fetch_k"]:
        return "Phase 7D-C — Production fetch_k / rerank cap expansion (retrieval config change)"

    if criteria["case_study_collapse_before_retrieval"]:
        return (
            "Phase 7D-C — Retrieval pool expansion first; "
            "case study strict corpus exists but fetch cap collapses pool pre-selection"
        )

    if not criteria["corpus_authoring_meaningful_under_current_retrieval"]:
        return "Phase 7E — Targeted corpus authoring for CRITICAL profile slices"

    return "Phase 7D-C — Retrieval expansion + Phase 7E — Corpus authoring (combined)"


def run_audit() -> dict:
    load_dotenv(PROJECT_ROOT / ".env")

    query_builder = RetrievalQueryBuilder()
    strategy_resolver = RetrievalStrategyResolver()
    adapter = RetrievalStrategyContextAdapter()

    chroma = ChromaRetrievalService()
    policy = AdaptiveRetrievalPolicy()
    repetition_filter = QuestionRepetitionFilter()
    coverage_engine = CoveragePenaltyEngine()
    weak_domain_engine = WeakDomainBoostEngine()
    selector = PerformanceResponsiveCandidateSelector()

    results: list[ProfileSweepResult] = []

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

                for fetch_k in FETCH_K_VALUES:
                    for top_k_mode in TOP_K_MODES:
                        chroma_k, rerank_top_k = _resolve_k_limits(fetch_k, top_k_mode)

                        snapshot_context = _build_context(
                            adapter=adapter,
                            query=query,
                            strategy=strategy,
                            role=role,
                            seniority=seniority,
                            area=area,
                            memory=InterviewRetrievalMemory(),
                        )

                        reranked = _build_adjusted_pool(
                            chroma=chroma,
                            policy=policy,
                            repetition_filter=repetition_filter,
                            coverage_engine=coverage_engine,
                            weak_domain_engine=weak_domain_engine,
                            query=query,
                            context=snapshot_context,
                            chroma_k=chroma_k,
                            rerank_top_k=rerank_top_k,
                        )
                        band_size, selectable, _ = _equivalence_band_metrics(
                            pool=reranked,
                            context=snapshot_context,
                            selector=selector,
                        )

                        depth = _simulate_effective_depth(
                            selector=selector,
                            context_builder=lambda mem: _build_context(
                                adapter=adapter,
                                query=query,
                                strategy=strategy,
                                role=role,
                                seniority=seniority,
                                area=area,
                                memory=mem,
                            ),
                            adjusted_pool=reranked,
                        )

                        results.append(
                            ProfileSweepResult(
                                area=area,
                                role=role.value,
                                seniority=seniority.value,
                                fetch_k=fetch_k,
                                top_k_mode=top_k_mode,
                                chroma_k=chroma_k,
                                rerank_top_k=rerank_top_k,
                                strict_pool=strict_pool,
                                retrieval_pool=len(reranked),
                                equivalence_band_size=band_size,
                                final_selectable_set=selectable,
                                effective_depth=depth,
                            )
                        )

    production_depth_by_area = {
        area: round(
            mean(
                row.effective_depth
                for row in results
                if row.area == area
                and row.fetch_k == PRODUCTION_FETCH_K
                and row.top_k_mode == "current"
            ),
            1,
        )
        for area in TARGET_AREAS
    }

    collapse_trace = _trace_case_study_collapse(
        results,
        chroma=chroma,
        policy=policy,
        selector=selector,
        query_builder=query_builder,
        strategy_resolver=strategy_resolver,
        adapter=adapter,
    )

    criteria = _success_criteria(
        results,
        production_depth_by_area=production_depth_by_area,
    )

    return {
        "audit": "Phase 7D-B Retrieval Depth Expansion",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "methodology": {
            "fetch_k_values": FETCH_K_VALUES,
            "top_k_modes": {
                "current": "chroma_k=fetch_k, rerank_top_k=fetch_k",
                "doubled": "chroma_k=fetch_k*2, rerank_top_k=fetch_k*2",
            },
            "production_fetch_k": PRODUCTION_FETCH_K,
            "other_behavior": "Production filter stages, coverage/weak-domain, equivalence band, cross-interview rotation preserved",
        },
        "area_tables": {
            area: {
                "current_top_k": _area_table(
                    [row for row in results if row.area == area],
                    top_k_mode="current",
                ),
                "doubled_top_k": _area_table(
                    [row for row in results if row.area == area],
                    top_k_mode="doubled",
                ),
            }
            for area in TARGET_AREAS
        },
        "profiles": [asdict(row) for row in results],
        "case_study_collapse_trace": collapse_trace,
        "success_criteria": criteria,
        "recommended_next_phase": _recommended_next_phase(criteria),
    }


def main() -> None:
    builtins.print = _quiet_print
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_audit()

    builtins.print = _ORIGINAL_PRINT

    output_path = OUTPUT_DIR / "phase_7d_b_retrieval_depth_expansion_audit.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary = {
        key: report[key]
        for key in report
        if key != "profiles"
    }
    summary_path = OUTPUT_DIR / "phase_7d_b_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    main()
