# scripts/question_intelligence/audit_retrieval_unlock_validation.py
#
# Phase 7D-C2.1 — Retrieval Unlock Validation (read-only audit).
#
# Validates the projected ROI of two zero-corpus retrieval config changes:
#   1. technical_background  fetch_k expansion  (k=3 → k=50, depth: ~3 → ~16.7)
#   2. technical_case_study  fetch_k expansion  (k=3 → k=50, depth: ~2.7 → ~6.5)
#
# No production changes. No corpus modifications.
# Audit runs against the live Chroma vectorstore read-only.

from __future__ import annotations

import builtins
import contextlib
import io
import json
import random
import time
from collections import defaultdict
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

FETCH_K_PRODUCTION = 3
FETCH_K_UNLOCKED   = 50
CORPUS_PROBE_K     = 200
MAX_SIM_INTERVIEWS = 500
RANDOM_SEED        = 20260611

AUDIT_AREAS = [
    (InterviewArea.TECH_BACKGROUND,  "technical_background"),
    (InterviewArea.TECH_CASE_STUDY,  "technical_case_study"),
]

AUDIT_ROLES = [
    RoleType.BACKEND_ENGINEER,
    RoleType.FULLSTACK_ENGINEER,
    RoleType.FRONTEND_ENGINEER,
    RoleType.DATA_ENGINEER,
    RoleType.DEVOPS_ENGINEER,
    RoleType.QA_ENGINEER,
    RoleType.ML_ENGINEER,
]

SENIORITY_LEVELS = list(SeniorityLevel)

# Prior baselines from Phase 7D-F1B
PREDICTED_BG_DEPTH_UNLOCKED  = 16.7
PREDICTED_CS_DEPTH_UNLOCKED  = 6.5
PREDICTED_GLOBAL_PROD        = 44.7
PREDICTED_GLOBAL_UNLOCKED    = 22.9

_ORIGINAL_PRINT = builtins.print


def _quiet_print(*args: object, **kwargs: object) -> None:
    message = " ".join(str(arg) for arg in args)
    if message.startswith(("SIMILARITY:", "EMBEDDING:", "penalty:", "Coverage")):
        return
    _ORIGINAL_PRINT(*args, **kwargs)


@dataclass
class SliceDepthResult:
    area: str
    role: str
    seniority: str
    strict_pool: int
    effective_depth_k3: int
    effective_depth_k50: int
    depth_gain: int


# ─── Retrieval helpers (reused pattern from 7D-E0) ───────────────────────────

def _document_id(candidate: RetrievalCandidate) -> str:
    return str(candidate.document.metadata.get("document_id", ""))


def _score(candidate: RetrievalCandidate) -> float:
    return float(candidate.adaptive_score or candidate.final_score)


def _search_raw(
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
        candidates.append(chroma._scorer.score(document=document, semantic_distance=distance))

    candidates.sort(key=_score, reverse=True)

    with contextlib.redirect_stdout(io.StringIO()):
        return chroma._diversity_reranker.rerank(
            candidates=candidates,
            top_k=min(chroma_k, len(candidates)),
        )


def _retrieve_staged(
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
        stage_candidates = _search_raw(
            chroma=chroma,
            query=query,
            filters=stage_filters,
            chroma_k=chroma_k,
        )
        filtered = repetition_filter.apply(candidates=stage_candidates, memory=memory)

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
    area_str: str,
    memory: InterviewRetrievalMemory,
) -> AdaptiveRetrievalContext:
    return adapter.adapt(
        query=query,
        retrieval_strategy=strategy,
        role=role.value,
        level=seniority.value,
        interview_type=InterviewType.TECHNICAL.value,
        area=area_str,
        memory=memory,
    )


def _strict_pool_size(
    *,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    context: AdaptiveRetrievalContext,
    query: str,
) -> int:
    strict_filters = policy.build_relaxation_stages(context)[0]
    candidates = _search_raw(
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
    area_str: str,
    chroma_k: int,
) -> int:
    reset_cross_interview_pick_counts()
    picked: set[str] = set()

    for _ in range(MAX_SIM_INTERVIEWS):
        memory = InterviewRetrievalMemory()
        context = _build_context(
            adapter=adapter,
            query=query,
            strategy=strategy,
            role=role,
            seniority=seniority,
            area_str=area_str,
            memory=memory,
        )

        pool = _retrieve_staged(
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


# ─── Reuse simulation (from 7D-F1A methodology) ──────────────────────────────

def _simulate_reuse(
    configs: list[tuple[str, str]],
    depths: dict[str, int],
) -> dict:
    """
    Round-robin slot simulation using measured depths.
    depths: mapping of "{area}|{role}|{seniority}" → effective_depth
    """
    AREAS = ["technical_background", "technical_technical_knowledge", "technical_case_study"]
    pick_counts: dict[tuple, int] = defaultdict(int)
    area_data: dict[str, dict] = {a: {"total": 0, "repeats": 0, "slots": set()} for a in AREAS}

    for role, seniority in configs:
        for area in AREAS:
            d = max(1, depths.get(f"{area}|{role}|{seniority}", 3))
            key = (area, role, seniority)
            idx = pick_counts[key]
            slot = f"{key[0]}|{key[1]}|{key[2]}|q{idx % d}"
            is_repeat = idx >= d
            pick_counts[key] += 1
            area_data[area]["total"] += 1
            if is_repeat:
                area_data[area]["repeats"] += 1
            area_data[area]["slots"].add(slot)

    out: dict = {}
    tot = rep = 0
    all_slots: set = set()
    for area in AREAS:
        t = area_data[area]["total"]
        r = area_data[area]["repeats"]
        u = len(area_data[area]["slots"])
        out[area] = {
            "total_prompts": t,
            "unique_prompts": u,
            "reuse_pct": round(r / t * 100, 1) if t else 0.0,
        }
        tot += t
        rep += r
        all_slots |= area_data[area]["slots"]

    out["global"] = {
        "total_prompts": tot,
        "unique_prompts": len(all_slots),
        "reuse_pct": round(rep / tot * 100, 1) if tot else 0.0,
    }
    return out


def _build_configs(n: int, seed: int = RANDOM_SEED) -> list[tuple[str, str]]:
    rng = random.Random(seed)
    pool = [(r.value, s.value) for r in AUDIT_ROLES for s in SENIORITY_LEVELS]
    return [rng.choice(pool) for _ in range(n)]


# ─── Main audit ───────────────────────────────────────────────────────────────

def run_audit() -> dict:
    load_dotenv(PROJECT_ROOT / ".env")
    builtins.print = _quiet_print

    chroma           = ChromaRetrievalService()
    policy           = AdaptiveRetrievalPolicy()
    repetition_filter = QuestionRepetitionFilter()
    coverage_engine  = CoveragePenaltyEngine()
    weak_domain_engine = WeakDomainBoostEngine()
    selector         = PerformanceResponsiveCandidateSelector()
    query_builder    = RetrievalQueryBuilder()
    strategy_resolver = RetrievalStrategyResolver()
    adapter          = RetrievalStrategyContextAdapter()

    total_slices = len(AUDIT_AREAS) * len(AUDIT_ROLES) * len(SENIORITY_LEVELS)
    _ORIGINAL_PRINT(f"\nPhase 7D-C2.1: Probing {total_slices} slices (2 areas × 7 roles × 3 seniorities)...", flush=True)

    area_results: dict[str, list[SliceDepthResult]] = {}
    completed = 0

    for interview_area, area_str in AUDIT_AREAS:
        area_results[area_str] = []
        _ORIGINAL_PRINT(f"\n  === {area_str} ===", flush=True)

        for role in AUDIT_ROLES:
            for seniority in SENIORITY_LEVELS:
                completed += 1
                _ORIGINAL_PRINT(f"  [{completed}/{total_slices}] {role.value}/{seniority.value}", flush=True)

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
                base_ctx = _build_context(
                    adapter=adapter,
                    query=query,
                    strategy=strategy,
                    role=role,
                    seniority=seniority,
                    area_str=area_str,
                    memory=InterviewRetrievalMemory(),
                )

                strict_pool = _strict_pool_size(
                    chroma=chroma,
                    policy=policy,
                    context=base_ctx,
                    query=query,
                )

                _ORIGINAL_PRINT(f"    strict_pool={strict_pool}  measuring depth k=3...", flush=True)
                d_k3 = _simulate_effective_depth(
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
                    area_str=area_str,
                    chroma_k=FETCH_K_PRODUCTION,
                )
                _ORIGINAL_PRINT(f"      k=3  → depth={d_k3}", flush=True)

                _ORIGINAL_PRINT(f"    measuring depth k=50...", flush=True)
                d_k50 = _simulate_effective_depth(
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
                    area_str=area_str,
                    chroma_k=FETCH_K_UNLOCKED,
                )
                _ORIGINAL_PRINT(f"      k=50 → depth={d_k50}", flush=True)

                area_results[area_str].append(SliceDepthResult(
                    area=area_str,
                    role=role.value,
                    seniority=seniority.value,
                    strict_pool=strict_pool,
                    effective_depth_k3=d_k3,
                    effective_depth_k50=d_k50,
                    depth_gain=d_k50 - d_k3,
                ))

    builtins.print = _ORIGINAL_PRINT

    # ─── Q1: Before/after depth summaries ────────────────────────────────────
    def area_summary(slices: list[SliceDepthResult]) -> dict:
        d_k3  = [s.effective_depth_k3  for s in slices]
        d_k50 = [s.effective_depth_k50 for s in slices]
        gains = [s.depth_gain           for s in slices]
        return {
            "slice_count": len(slices),
            "depth_k3": {
                "avg": round(mean(d_k3), 1),
                "min": min(d_k3),
                "max": max(d_k3),
            },
            "depth_k50": {
                "avg": round(mean(d_k50), 1),
                "min": min(d_k50),
                "max": max(d_k50),
            },
            "avg_depth_gain": round(mean(gains), 1),
            "max_depth_gain": max(gains),
            "slices_improved": sum(1 for g in gains if g > 0),
            "slices_unchanged": sum(1 for g in gains if g == 0),
        }

    q1_before_after: dict[str, dict] = {}
    for area_str, slices in area_results.items():
        q1_before_after[area_str] = area_summary(slices)

    # ─── Build depth maps for simulation ─────────────────────────────────────
    # TK uses depth=3 (measured in 7D-D, unchanged here)
    TK_DEPTH = 3

    def build_depth_map(scenario: Literal["production", "unlocked"]) -> dict[str, int]:
        dm: dict[str, int] = {}
        for area_str, slices in area_results.items():
            for s in slices:
                key = f"{area_str}|{s.role}|{s.seniority}"
                dm[key] = s.effective_depth_k3 if scenario == "production" else s.effective_depth_k50
        # Fill TK for all roles/seniorities (not measured — same depth both scenarios)
        for role in AUDIT_ROLES:
            for seniority in SENIORITY_LEVELS:
                dm[f"technical_technical_knowledge|{role.value}|{seniority.value}"] = TK_DEPTH
        return dm

    prod_depths     = build_depth_map("production")
    unlocked_depths = build_depth_map("unlocked")
    # Partial unlocks:
    bg_only_depths  = {k: (unlocked_depths[k] if k.startswith("technical_background") else prod_depths[k]) for k in prod_depths}
    cs_only_depths  = {k: (unlocked_depths[k] if k.startswith("technical_case_study") else prod_depths[k]) for k in prod_depths}

    # ─── Q2 / Q3 / Q4: Reuse projections ─────────────────────────────────────
    AREAS_DISPLAY = ["technical_background", "technical_technical_knowledge", "technical_case_study", "global"]
    sample_sizes  = [20, 50, 100]

    reuse_results: dict[str, dict] = {}
    for n in sample_sizes:
        configs = _build_configs(n)
        reuse_results[f"n{n}"] = {
            "production":  _simulate_reuse(configs, prod_depths),
            "bg_unlocked": _simulate_reuse(configs, bg_only_depths),
            "cs_unlocked": _simulate_reuse(configs, cs_only_depths),
            "both_unlocked": _simulate_reuse(configs, unlocked_depths),
        }

    def reuse_table(n: int) -> dict:
        res = reuse_results[f"n{n}"]
        return {
            scenario: {area: res[scenario][area]["reuse_pct"] for area in AREAS_DISPLAY}
            for scenario in res
        }

    # ─── Q5: Projection accuracy vs 7D-F1B forecast ──────────────────────────
    actual_global_prod     = reuse_results["n100"]["production"]["global"]["reuse_pct"]
    actual_global_unlocked = reuse_results["n100"]["both_unlocked"]["global"]["reuse_pct"]
    actual_global_delta    = round(actual_global_prod - actual_global_unlocked, 1)
    predicted_delta        = round(PREDICTED_GLOBAL_PROD - PREDICTED_GLOBAL_UNLOCKED, 1)
    accuracy_pct           = round(actual_global_delta / predicted_delta * 100, 1) if predicted_delta else 0.0

    # Verify BG depth prediction
    bg_slices   = area_results["technical_background"]
    cs_slices   = area_results["technical_case_study"]
    actual_bg_depth_k50 = round(mean(s.effective_depth_k50 for s in bg_slices), 1)
    actual_cs_depth_k50 = round(mean(s.effective_depth_k50 for s in cs_slices), 1)

    bg_depth_accurate = abs(actual_bg_depth_k50 - PREDICTED_BG_DEPTH_UNLOCKED) <= 3.0
    cs_depth_accurate = abs(actual_cs_depth_k50 - PREDICTED_CS_DEPTH_UNLOCKED) <= 2.0

    # ─── Verdict ─────────────────────────────────────────────────────────────
    # Validated if:
    #   1. BG depth at k=50 within ±3 of predicted 16.7
    #   2. CS depth at k=50 within ±2 of predicted 6.5
    #   3. Actual global reduction ≥ 80% of predicted reduction
    global_reduction_accurate = accuracy_pct >= 80.0
    verdict = (
        "RETRIEVAL_UNLOCK_VALIDATED"
        if (bg_depth_accurate and cs_depth_accurate and global_reduction_accurate)
        else "RETRIEVAL_UNLOCK_OVERESTIMATED"
    )

    report = {
        "audit": "Phase 7D-C2.1 Retrieval Unlock Validation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "areas_audited": ["technical_background", "technical_case_study"],
            "roles": [r.value for r in AUDIT_ROLES],
            "seniorities": [s.value for s in SENIORITY_LEVELS],
            "fetch_k_production": FETCH_K_PRODUCTION,
            "fetch_k_unlocked": FETCH_K_UNLOCKED,
            "reuse_sample_sizes": sample_sizes,
            "tk_depth_assumed": TK_DEPTH,
            "note": "Read-only audit. No corpus or production changes.",
        },
        "Q1_depth_before_after": q1_before_after,
        "Q2_Q3_Q4_reuse_projections": {
            f"n{n}": reuse_table(n) for n in sample_sizes
        },
        "Q3_depth_prediction_verification": {
            "bg": {
                "predicted_depth_k50": PREDICTED_BG_DEPTH_UNLOCKED,
                "actual_depth_k50": actual_bg_depth_k50,
                "delta": round(actual_bg_depth_k50 - PREDICTED_BG_DEPTH_UNLOCKED, 1),
                "prediction_accurate": bg_depth_accurate,
            },
            "cs": {
                "predicted_depth_k50": PREDICTED_CS_DEPTH_UNLOCKED,
                "actual_depth_k50": actual_cs_depth_k50,
                "delta": round(actual_cs_depth_k50 - PREDICTED_CS_DEPTH_UNLOCKED, 1),
                "prediction_accurate": cs_depth_accurate,
            },
        },
        "Q5_global_reuse_prediction_verification": {
            "predicted_production_global": PREDICTED_GLOBAL_PROD,
            "actual_production_global": actual_global_prod,
            "predicted_unlocked_global": PREDICTED_GLOBAL_UNLOCKED,
            "actual_unlocked_global": actual_global_unlocked,
            "predicted_reduction_pp": predicted_delta,
            "actual_reduction_pp": actual_global_delta,
            "accuracy_pct": accuracy_pct,
            "target_validated": global_reduction_accurate,
        },
        "verdict": {
            "verdict": verdict,
            "bg_depth_prediction_accurate": bg_depth_accurate,
            "cs_depth_prediction_accurate": cs_depth_accurate,
            "global_reduction_prediction_accurate": global_reduction_accurate,
            "actual_global_reuse_production": actual_global_prod,
            "actual_global_reuse_after_both_unlocks": actual_global_unlocked,
            "actual_reduction_pp": actual_global_delta,
            "quantitative_summary": (
                f"Production global reuse: {actual_global_prod}% → "
                f"after both retrieval unlocks: {actual_global_unlocked}%. "
                f"Reduction: {actual_global_delta}pp "
                f"(predicted {predicted_delta}pp, accuracy={accuracy_pct}%). "
                f"BG depth k50: {actual_bg_depth_k50} (predicted {PREDICTED_BG_DEPTH_UNLOCKED}). "
                f"CS depth k50: {actual_cs_depth_k50} (predicted {PREDICTED_CS_DEPTH_UNLOCKED})."
            ),
        },
        "slices": {
            area_str: [asdict(s) for s in slices]
            for area_str, slices in area_results.items()
        },
    }

    return report


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Starting Phase 7D-C2.1 — Retrieval Unlock Validation...", flush=True)
    report = run_audit()

    full_path = OUTPUT_DIR / "phase_7d_c21_retrieval_unlock_validation.json"
    full_path.write_text(json.dumps(report, indent=2))

    summary_keys = [k for k in report if k != "slices"]
    summary = {k: report[k] for k in summary_keys}
    summary_path = OUTPUT_DIR / "phase_7d_c21_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    verdict = report["verdict"]["verdict"]
    print(f"\n=== {verdict} ===", flush=True)
    print(report["verdict"]["quantitative_summary"], flush=True)
    print(f"\nOutputs written to {OUTPUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
