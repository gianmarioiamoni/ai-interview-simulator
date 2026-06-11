# scripts/question_intelligence/audit_retrieval_saturation.py

# Phase 7C-B0 — Retrieval Saturation Audit (read-only).

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

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
from services.question_intelligence.retrieval.retrieval_strategy_resolver import (
    RetrievalStrategyResolver,
)
from services.question_intelligence.retrieval_query_builder import RetrievalQueryBuilder

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"

TOP_K_VALUES = [3, 5, 10, 20]
CORPUS_PROBE_K = 200

TARGET_AREAS = [
    InterviewArea.HR_ANALYTICAL,
    InterviewArea.HR_BRAIN_TEASER,
    InterviewArea.HR_TECHNICAL_KNOWLEDGE,
    InterviewArea.HR_SITUATIONAL,
    InterviewArea.TECH_BACKGROUND,
    InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
]

HR_PROFILES = [
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.MID),
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.MID),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.SENIOR),
]

TECH_PROFILES = [
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.MID),
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.MID),
]


@dataclass
class RetrievalRunMetrics:
    top_k: int
    candidate_count: int
    unique_document_count: int
    document_ids: list[str]
    average_score: float
    score_top1: float | None
    score_top10: float | None
    score_drop_top1_to_top10: float | None
    latency_ms: float
    filter_stage_used: int


@dataclass
class CorpusBaseline:
    strict_filter_count: int
    area_only_count: int
    strict_document_ids: list[str] = field(default_factory=list)


@dataclass
class ProfileAreaResult:
    area: str
    role: str
    seniority: str
    interview_type: str
    corpus: CorpusBaseline
    runs: list[RetrievalRunMetrics]
    union_k3: list[str]
    union_k20: list[str]
    pool_growth_pattern: str
    union_growth_pattern: str
    saturation_verdict: str


def _document_id(candidate: RetrievalCandidate) -> str:
    return str(candidate.document.metadata.get("document_id", ""))


def _score(candidate: RetrievalCandidate) -> float:
    return candidate.adaptive_score if candidate.adaptive_score is not None else candidate.final_score


def _min_pool_size(context) -> int:
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


def _retrieve_pool(
    *,
    query: str,
    context,
    top_k: int,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    repetition_filter: QuestionRepetitionFilter,
    coverage_engine: CoveragePenaltyEngine,
    weak_domain_engine: WeakDomainBoostEngine,
) -> tuple[list[RetrievalCandidate], int, float]:
    filter_stages = policy.build_relaxation_stages(context)
    min_pool = _min_pool_size(context)
    memory = context.memory

    started = time.perf_counter()
    best_undersized: list[RetrievalCandidate] = []
    stage_used = len(filter_stages)

    for stage_index, stage_filters in enumerate(filter_stages, start=1):
        stage_candidates = chroma.search_with_filters(
            query=query,
            filters=stage_filters,
            k=top_k,
        )
        filtered = repetition_filter.apply(
            candidates=stage_candidates,
            memory=memory,
        )

        if len(filtered) >= min_pool:
            pool = filtered
            stage_used = stage_index
            break

        if len(filtered) > len(best_undersized):
            best_undersized = filtered
    else:
        pool = best_undersized
        stage_used = len(filter_stages)

    if not pool:
        return [], stage_used, (time.perf_counter() - started) * 1000

    adjusted = coverage_engine.apply(candidates=pool, context=context)
    adjusted = weak_domain_engine.apply(candidates=adjusted, context=context)
    adjusted.sort(key=_score, reverse=True)

    latency_ms = (time.perf_counter() - started) * 1000
    return adjusted, stage_used, latency_ms


def _corpus_baseline(
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    context,
    query: str,
) -> CorpusBaseline:
    stages = policy.build_relaxation_stages(context)

    strict_candidates = chroma.search_with_filters(
        query=query,
        filters=stages[0],
        k=CORPUS_PROBE_K,
    )
    strict_ids = sorted(
        {
            _document_id(candidate)
            for candidate in strict_candidates
            if _document_id(candidate)
        }
    )

    area_only = chroma.search_with_filters(
        query=query,
        filters=stages[-1],
        k=CORPUS_PROBE_K,
    )
    area_ids = {
        _document_id(candidate)
        for candidate in area_only
        if _document_id(candidate)
    }

    return CorpusBaseline(
        strict_filter_count=len(strict_ids),
        area_only_count=len(area_ids),
        strict_document_ids=strict_ids,
    )


def _growth_pattern(values: dict[int, int]) -> str:
    ordered = [values[k] for k in TOP_K_VALUES]

    if ordered[0] == ordered[-1]:
        return "flat"

    if ordered == sorted(ordered) and ordered[-1] > ordered[0]:
        if ordered[0] == ordered[1] == ordered[2] and ordered[2] < ordered[3]:
            return "late_growth"
        if ordered[0] < ordered[1] < ordered[2] < ordered[3]:
            return "linear"
        return "partial"

    return "irregular"


def _saturation_verdict(
    *,
    runs: list[RetrievalRunMetrics],
    corpus: CorpusBaseline,
) -> str:
    by_k = {run.top_k: run for run in runs}
    k3 = by_k[3].candidate_count
    k20 = by_k[20].candidate_count
    union3 = len(by_k[3].document_ids)
    union20 = len(set(by_k[20].document_ids))

    pool_grows = k20 > k3 + 1
    union_grows = union20 > union3 + 1
    hits_corpus_ceiling = k20 >= corpus.strict_filter_count and corpus.strict_filter_count <= 5

    if hits_corpus_ceiling or (not pool_grows and not union_grows):
        return "corpus_limited"

    if pool_grows and union_grows:
        return "retrieval_limited"

    return "mixed"


def _profiles_for_area(area: InterviewArea) -> list[tuple[RoleType, SeniorityLevel]]:
    if area.value.startswith("hr_"):
        return HR_PROFILES

    return TECH_PROFILES


def _interview_type_for_area(area: InterviewArea) -> InterviewType:
    if area.value.startswith("hr_"):
        return InterviewType.HR

    return InterviewType.TECHNICAL


def run_audit() -> dict:
    query_builder = RetrievalQueryBuilder()
    strategy_resolver = RetrievalStrategyResolver()
    context_adapter = RetrievalStrategyContextAdapter()

    chroma = ChromaRetrievalService()
    policy = AdaptiveRetrievalPolicy()
    repetition_filter = QuestionRepetitionFilter()
    coverage_engine = CoveragePenaltyEngine()
    weak_domain_engine = WeakDomainBoostEngine()

    results: list[ProfileAreaResult] = []

    for area in TARGET_AREAS:
        for role, level in _profiles_for_area(area):
            memory = InterviewRetrievalMemory()
            interview_type = _interview_type_for_area(area)

            query = query_builder.build(
                role=role,
                level=level,
                area=area,
                memory=memory,
            )

            strategy = strategy_resolver.resolve(
                area=area,
                level=level,
                questions_per_area=QUESTIONS_PER_AREA,
            )

            context = context_adapter.adapt(
                query=query,
                retrieval_strategy=strategy,
                role=role.value,
                level=level.value,
                interview_type=interview_type.value,
                area=area.value,
                memory=memory,
            )

            corpus = _corpus_baseline(
                chroma=chroma,
                policy=policy,
                context=context,
                query=query,
            )

            runs: list[RetrievalRunMetrics] = []

            for top_k in TOP_K_VALUES:
                pool, stage_used, latency_ms = _retrieve_pool(
                    query=query,
                    context=context,
                    top_k=top_k,
                    chroma=chroma,
                    policy=policy,
                    repetition_filter=repetition_filter,
                    coverage_engine=coverage_engine,
                    weak_domain_engine=weak_domain_engine,
                )

                doc_ids = [_document_id(c) for c in pool if _document_id(c)]
                scores = [_score(c) for c in pool]
                avg_score = sum(scores) / len(scores) if scores else 0.0
                top1 = scores[0] if scores else None
                top10 = scores[9] if len(scores) >= 10 else (scores[-1] if scores else None)
                score_drop = (
                    top1 - top10
                    if top1 is not None and top10 is not None and len(scores) >= 2
                    else None
                )

                runs.append(
                    RetrievalRunMetrics(
                        top_k=top_k,
                        candidate_count=len(pool),
                        unique_document_count=len(set(doc_ids)),
                        document_ids=doc_ids,
                        average_score=round(avg_score, 4),
                        score_top1=round(top1, 4) if top1 is not None else None,
                        score_top10=round(top10, 4) if top10 is not None else None,
                        score_drop_top1_to_top10=round(score_drop, 4)
                        if score_drop is not None
                        else None,
                        latency_ms=round(latency_ms, 1),
                        filter_stage_used=stage_used,
                    )
                )

            pool_sizes = {run.top_k: run.candidate_count for run in runs}
            union_sizes = {run.top_k: run.unique_document_count for run in runs}

            results.append(
                ProfileAreaResult(
                    area=area.value,
                    role=role.value,
                    seniority=level.value,
                    interview_type=interview_type.value,
                    corpus=corpus,
                    runs=runs,
                    union_k3=runs[0].document_ids,
                    union_k20=runs[-1].document_ids,
                    pool_growth_pattern=_growth_pattern(pool_sizes),
                    union_growth_pattern=_growth_pattern(union_sizes),
                    saturation_verdict=_saturation_verdict(runs=runs, corpus=corpus),
                )
            )

    return _build_report(results)


def _build_report(results: list[ProfileAreaResult]) -> dict:
    area_summary: dict[str, dict] = {}

    for area in TARGET_AREAS:
        area_rows = [row for row in results if row.area == area.value]

        if not area_rows:
            continue

        pool_at_k = {
            k: round(
                sum(row.runs[i].candidate_count for row in area_rows) / len(area_rows),
                1,
            )
            for i, k in enumerate(TOP_K_VALUES)
        }
        union_at_k = {
            k: round(
                sum(row.runs[i].unique_document_count for row in area_rows)
                / len(area_rows),
                1,
            )
            for i, k in enumerate(TOP_K_VALUES)
        }
        avg_strict_corpus = round(
            sum(row.corpus.strict_filter_count for row in area_rows) / len(area_rows),
            1,
        )
        avg_area_corpus = round(
            sum(row.corpus.area_only_count for row in area_rows) / len(area_rows),
            1,
        )

        verdicts = Counter(row.saturation_verdict for row in area_rows)
        dominant = verdicts.most_common(1)[0][0]

        area_summary[area.value] = {
            "avg_pool_by_k": pool_at_k,
            "avg_union_by_k": union_at_k,
            "avg_strict_corpus_size": avg_strict_corpus,
            "avg_area_only_corpus_size": avg_area_corpus,
            "dominant_verdict": dominant,
            "verdict_counts": dict(verdicts),
        }

    global_verdicts = Counter(row.saturation_verdict for row in results)
    retrieval_limited = global_verdicts.get("retrieval_limited", 0)
    corpus_limited = global_verdicts.get("corpus_limited", 0)

    if corpus_limited > retrieval_limited:
        recommendation = "Phase 7C-B2 — HR Corpus Expansion"
    elif retrieval_limited > corpus_limited:
        recommendation = "Phase 7C-B1 — Pool Expansion"
    else:
        recommendation = "Phase 7C-B2 — HR Corpus Expansion (HR areas) + Phase 7C-B1 — Pool Expansion (technical areas)"

    current_ceiling = 0.513
    pool_expansion_ceiling = _estimate_ceiling(results, assume_corpus_multiplier=1.0)
    corpus_expansion_ceiling = _estimate_ceiling(results, assume_corpus_multiplier=3.0)

    return {
        "audit": "Phase 7C-B0 Retrieval Saturation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "top_k_values": TOP_K_VALUES,
        "configurations_tested": len(results),
        "area_summary": area_summary,
        "global_verdict_counts": dict(global_verdicts),
        "growth_curves": {
            area: {
                "pool": summary["avg_pool_by_k"],
                "union": summary["avg_union_by_k"],
            }
            for area, summary in area_summary.items()
        },
        "diversity_ceiling": {
            "current_observed_pct": round(current_ceiling * 100, 1),
            "if_top_k_expanded_pct": round(pool_expansion_ceiling * 100, 1),
            "if_corpus_expanded_pct": round(corpus_expansion_ceiling * 100, 1),
        },
        "recommended_phase": recommendation,
        "profile_results": [
            {
                **{k: v for k, v in asdict(row).items() if k not in {"runs", "corpus"}},
                "corpus": asdict(row.corpus),
                "runs": [asdict(run) for run in row.runs],
            }
            for row in results
        ],
    }


def _estimate_ceiling(
    results: list[ProfileAreaResult],
    *,
    assume_corpus_multiplier: float,
) -> float:
    # Weighted by Phase 7C-A area prompt share (approximate).
    area_weights = {
        "hr_analytical": 10,
        "hr_brain_teaser": 10,
        "hr_technical_knowledge": 10,
        "hr_situational": 10,
        "technical_background": 20,
        "technical_technical_knowledge": 20,
    }

    total_weight = sum(area_weights.values())
    weighted_unique_rate = 0.0

    for area, weight in area_weights.items():
        area_rows = [row for row in results if row.area == area]

        if not area_rows:
            continue

        if assume_corpus_multiplier > 1.0:
            effective = min(
                0.95,
                sum(row.corpus.area_only_count for row in area_rows)
                / len(area_rows)
                / 20
                * assume_corpus_multiplier
                * 0.35
                + 0.55,
            )
        else:
            k20_pool = sum(row.runs[-1].candidate_count for row in area_rows) / len(
                area_rows
            )
            k3_pool = sum(row.runs[0].candidate_count for row in area_rows) / len(
                area_rows
            )
            growth_factor = k20_pool / max(k3_pool, 1)
            base_reuse = {
                "hr_analytical": 0.90,
                "hr_brain_teaser": 0.80,
                "hr_technical_knowledge": 0.80,
                "hr_situational": 0.70,
                "technical_background": 0.65,
                "technical_technical_knowledge": 0.65,
            }[area]
            effective = min(0.95, (1 - base_reuse) * min(growth_factor, 2.5))

        weighted_unique_rate += (weight / total_weight) * effective

    return weighted_unique_rate


def main() -> None:
    load_dotenv()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_audit()

    output_path = OUTPUT_DIR / "phase_7c_b0_retrieval_saturation_audit.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary = {
        key: report[key]
        for key in report
        if key != "profile_results"
    }
    summary_path = OUTPUT_DIR / "phase_7c_b0_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    main()
