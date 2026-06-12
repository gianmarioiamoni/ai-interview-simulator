# scripts/question_intelligence/audit_tk_retrieval_sizing.py
#
# Phase 7D-TK3 — Technical Knowledge Retrieval Sizing Audit (read-only).
#
# Determines the minimum fetch_k for technical_technical_knowledge where:
#   - corpus growth becomes observable (effective_depth > production baseline)
#   - depth reaches >=80% of k=50 ceiling
#   - marginal gain from further k increase drops below 5%
#
# No corpus changes. No production code changes. No Chroma rebuild.

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

AREA_STR      = "technical_technical_knowledge"
INTERVIEW_AREA = InterviewArea.TECH_TECHNICAL_KNOWLEDGE

FETCH_K_VALUES = [3, 5, 8, 10, 20, 50]
CORPUS_PROBE_K = 200
MAX_SIM_INTERVIEWS = 500
RANDOM_SEED = 20260611

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

_ORIGINAL_PRINT = builtins.print


def _quiet_print(*args: object, **kwargs: object) -> None:
    message = " ".join(str(arg) for arg in args)
    if message.startswith(("SIMILARITY:", "EMBEDDING:", "penalty:", "Coverage")):
        return
    _ORIGINAL_PRINT(*args, **kwargs)


@dataclass
class SliceSweep:
    role: str
    seniority: str
    strict_pool: int
    effective_depth_k3: int
    effective_depth_k5: int
    effective_depth_k8: int
    effective_depth_k10: int
    effective_depth_k20: int
    effective_depth_k50: int
    min_k_corpus_visible: int   # smallest k where depth > k=3 baseline
    min_k_80pct_ceiling: int    # smallest k reaching >=80% of k=50 depth
    saturation_k: int           # smallest k where gain < 5% vs prior step


# ─── Retrieval helpers (shared pattern) ──────────────────────────────────────

def _doc_id(c: RetrievalCandidate) -> str:
    return str(c.document.metadata.get("document_id", ""))


def _score(c: RetrievalCandidate) -> float:
    return float(c.adaptive_score or c.final_score)


def _search_raw(*, chroma, query, filters, chroma_k) -> list[RetrievalCandidate]:
    where = chroma._filter_builder.build(filters)
    last_err = None
    for attempt in range(3):
        try:
            results = chroma._vectorstore.similarity_search_with_score(
                query=query, k=chroma_k, filter=where
            )
            break
        except Exception as exc:
            last_err = exc
            time.sleep(1 + attempt)
    else:
        raise last_err if last_err else RuntimeError("Chroma search failed")

    candidates = [
        chroma._scorer.score(document=doc, semantic_distance=dist)
        for doc, dist in results
    ]
    candidates.sort(key=_score, reverse=True)
    with contextlib.redirect_stdout(io.StringIO()):
        return chroma._diversity_reranker.rerank(
            candidates=candidates,
            top_k=min(chroma_k, len(candidates)),
        )


def _retrieve_staged(*, chroma, policy, repetition_filter, query, context, chroma_k):
    filter_stages = policy.build_relaxation_stages(context)
    best: list[RetrievalCandidate] = []
    for stage_filters in filter_stages:
        cands = _search_raw(chroma=chroma, query=query, filters=stage_filters, chroma_k=chroma_k)
        filtered = repetition_filter.apply(candidates=cands, memory=context.memory)
        if filtered:
            return filtered
        if len(filtered) > len(best):
            best = filtered
    return best


def _apply_post(*, pool, context, coverage_engine, weak_domain_engine):
    if not pool:
        return []
    adj = coverage_engine.apply(candidates=pool, context=context)
    adj = weak_domain_engine.apply(candidates=adj, context=context)
    adj.sort(key=_score, reverse=True)
    return adj


def _build_context(*, adapter, query, strategy, role, seniority, memory):
    return adapter.adapt(
        query=query,
        retrieval_strategy=strategy,
        role=role.value,
        level=seniority.value,
        interview_type=InterviewType.TECHNICAL.value,
        area=AREA_STR,
        memory=memory,
    )


def _strict_pool(*, chroma, policy, context, query) -> int:
    strict_filters = policy.build_relaxation_stages(context)[0]
    cands = _search_raw(chroma=chroma, query=query, filters=strict_filters, chroma_k=CORPUS_PROBE_K)
    return len({_doc_id(c) for c in cands if _doc_id(c)})


def _simulate_depth(
    *, chroma, policy, repetition_filter, coverage_engine, weak_domain_engine,
    selector, adapter, query, strategy, role, seniority, chroma_k
) -> int:
    reset_cross_interview_pick_counts()
    picked: set[str] = set()
    for _ in range(MAX_SIM_INTERVIEWS):
        memory = InterviewRetrievalMemory()
        ctx = _build_context(adapter=adapter, query=query, strategy=strategy,
                             role=role, seniority=seniority, memory=memory)
        pool = _retrieve_staged(chroma=chroma, policy=policy,
                                repetition_filter=repetition_filter,
                                query=query, context=ctx, chroma_k=chroma_k)
        adj = _apply_post(pool=pool, context=ctx,
                          coverage_engine=coverage_engine,
                          weak_domain_engine=weak_domain_engine)
        with contextlib.redirect_stdout(io.StringIO()):
            selected = selector.select(pool=adj, context=ctx)
        if not selected:
            break
        doc = _doc_id(selected[0])
        if not doc or doc in picked:
            break
        picked.add(doc)
    return len(picked)


# ─── Reuse simulation (round-robin, same as 7D-TK2 / 7D-F1A) ────────────────

def _simulate_reuse(
    configs: list[tuple[str, str]],
    tk_depth_map: dict[str, int],
    bg_depth: int,
    cs_depth_map: dict[str, int],
) -> dict:
    AREAS = ["technical_background", "technical_technical_knowledge", "technical_case_study"]
    pick_counts: dict = defaultdict(int)
    area_data: dict = defaultdict(lambda: {"total": 0, "repeats": 0, "slots": set()})

    for role, seniority in configs:
        for area in AREAS:
            if area == "technical_background":
                d = max(1, bg_depth)
            elif area == "technical_technical_knowledge":
                d = max(1, tk_depth_map.get(f"{role}/{seniority}", 3))
            else:
                d = max(1, cs_depth_map.get(f"{role}/{seniority}", 3))
            key = (area, role, seniority)
            idx = pick_counts[key]
            slot = f"{area}|{role}|{seniority}|q{idx % d}"
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


def _build_configs(n: int) -> list[tuple[str, str]]:
    rng = random.Random(RANDOM_SEED)
    pool = [(r.value, s.value) for r in AUDIT_ROLES for s in SENIORITY_LEVELS]
    return [rng.choice(pool) for _ in range(n)]


# ─── Main audit ───────────────────────────────────────────────────────────────

def run_audit() -> dict:
    load_dotenv(PROJECT_ROOT / ".env")

    # Load prior context
    prior_c21 = json.loads(
        (OUTPUT_DIR / "phase_7d_c21_retrieval_unlock_validation.json").read_text()
    )
    prior_d_d = json.loads(
        (OUTPUT_DIR / "phase_7d_d_slice_depth_audit.json").read_text()
    )

    # BG live depth (corpus-constrained ~2.1, from 7D-C2.1)
    bg_live_depth = round(mean(
        s["effective_depth_k3"]
        for s in prior_c21["slices"]["technical_background"]
    ))

    # CS k50 depths (from 7D-C2.1)
    cs_k50 = {
        f"{s['role']}/{s['seniority']}": s["effective_depth_k50"]
        for s in prior_c21["slices"]["technical_case_study"]
    }

    builtins.print = _quiet_print

    chroma            = ChromaRetrievalService()
    policy            = AdaptiveRetrievalPolicy()
    rep_filter        = QuestionRepetitionFilter()
    cov_engine        = CoveragePenaltyEngine()
    wk_engine         = WeakDomainBoostEngine()
    selector          = PerformanceResponsiveCandidateSelector()
    query_builder     = RetrievalQueryBuilder()
    strat_resolver    = RetrievalStrategyResolver()
    adapter           = RetrievalStrategyContextAdapter()

    total = len(AUDIT_ROLES) * len(SENIORITY_LEVELS)
    _ORIGINAL_PRINT(
        f"\nPhase 7D-TK3: Probing {total} TK slices × {len(FETCH_K_VALUES)} fetch_k values...",
        flush=True,
    )

    slices: list[SliceSweep] = []
    completed = 0

    for role in AUDIT_ROLES:
        for seniority in SENIORITY_LEVELS:
            completed += 1
            _ORIGINAL_PRINT(f"  [{completed}/{total}] {role.value}/{seniority.value}", flush=True)

            memory = InterviewRetrievalMemory()
            query = query_builder.build(
                role=role, level=seniority, area=INTERVIEW_AREA, memory=memory
            )
            strategy = strat_resolver.resolve(
                area=INTERVIEW_AREA, level=seniority, questions_per_area=QUESTIONS_PER_AREA
            )
            base_ctx = _build_context(
                adapter=adapter, query=query, strategy=strategy,
                role=role, seniority=seniority, memory=InterviewRetrievalMemory()
            )

            sp = _strict_pool(chroma=chroma, policy=policy, context=base_ctx, query=query)

            depths: dict[int, int] = {}
            for k in FETCH_K_VALUES:
                _ORIGINAL_PRINT(f"    fetch_k={k}...", flush=True)
                d = _simulate_depth(
                    chroma=chroma, policy=policy, repetition_filter=rep_filter,
                    coverage_engine=cov_engine, weak_domain_engine=wk_engine,
                    selector=selector, adapter=adapter,
                    query=query, strategy=strategy, role=role, seniority=seniority,
                    chroma_k=k,
                )
                depths[k] = d
                _ORIGINAL_PRINT(f"      → depth={d}", flush=True)

            d_k50 = depths[50]
            d_k3  = depths[3]
            ceiling_80 = max(1, round(d_k50 * 0.80))

            # min k where depth > k3 baseline
            min_k_visible = next((k for k in FETCH_K_VALUES if depths[k] > d_k3), 50)

            # min k where depth >= 80% of ceiling
            min_k_80pct = next(
                (k for k in FETCH_K_VALUES if depths[k] >= ceiling_80), 50
            )

            # saturation k: smallest k where incremental gain < 5% of prev depth
            sat_k = 50
            prev_d = d_k3
            for k in FETCH_K_VALUES[1:]:
                gain_pct = (depths[k] - prev_d) / max(1, prev_d) * 100
                if gain_pct < 5.0 and depths[k] >= ceiling_80:
                    sat_k = k
                    break
                prev_d = depths[k]

            slices.append(SliceSweep(
                role=role.value, seniority=seniority.value, strict_pool=sp,
                effective_depth_k3=depths[3], effective_depth_k5=depths[5],
                effective_depth_k8=depths[8], effective_depth_k10=depths[10],
                effective_depth_k20=depths[20], effective_depth_k50=depths[50],
                min_k_corpus_visible=min_k_visible,
                min_k_80pct_ceiling=min_k_80pct,
                saturation_k=sat_k,
            ))

    builtins.print = _ORIGINAL_PRINT

    # ─── Q1: Per-slice depth table ────────────────────────────────────────────
    q1 = {
        "slices": [asdict(s) for s in slices],
        "aggregate": {
            str(k): {
                "avg_depth": round(mean(getattr(s, f"effective_depth_k{k}") for s in slices), 2),
                "min_depth": min(getattr(s, f"effective_depth_k{k}") for s in slices),
                "max_depth": max(getattr(s, f"effective_depth_k{k}") for s in slices),
            }
            for k in FETCH_K_VALUES
        },
    }

    # ─── Q2: Thresholds ──────────────────────────────────────────────────────
    def mode(values):
        from collections import Counter
        return Counter(values).most_common(1)[0][0]

    min_k_visible_values = [s.min_k_corpus_visible for s in slices]
    min_k_80_values      = [s.min_k_80pct_ceiling  for s in slices]
    sat_k_values         = [s.saturation_k          for s in slices]

    q2 = {
        "min_k_corpus_growth_visible": {
            "per_slice": sorted(set(min_k_visible_values)),
            "modal_k": mode(min_k_visible_values),
            "all_slices_at_k": {
                str(k): sum(1 for v in min_k_visible_values if v <= k)
                for k in FETCH_K_VALUES
            },
        },
        "min_k_80pct_ceiling": {
            "per_slice": sorted(set(min_k_80_values)),
            "modal_k": mode(min_k_80_values),
            "all_slices_at_k": {
                str(k): sum(1 for v in min_k_80_values if v <= k)
                for k in FETCH_K_VALUES
            },
        },
        "saturation_k": {
            "per_slice": sorted(set(sat_k_values)),
            "modal_k": mode(sat_k_values),
        },
    }

    # ─── Q3: Reuse projections ────────────────────────────────────────────────
    configs = {n: _build_configs(n) for n in [20, 50, 100]}

    def make_tk_depth_map(k: int) -> dict[str, int]:
        return {
            f"{s.role}/{s.seniority}": getattr(s, f"effective_depth_k{k}")
            for s in slices
        }

    q3: dict = {}
    for k in FETCH_K_VALUES:
        tk_dm = make_tk_depth_map(k)
        q3[str(k)] = {
            f"n{n}": {
                area: _simulate_reuse(configs[n], tk_dm, bg_live_depth, cs_k50)[area]["reuse_pct"]
                for area in ["technical_background", "technical_technical_knowledge",
                             "technical_case_study", "global"]
            }
            for n in [20, 50, 100]
        }

    # ─── Q4: Retrieval cost model ─────────────────────────────────────────────
    # Cost = candidates fetched from Chroma + rerank ops
    # At fetch_k=k: chroma fetches k docs per stage (up to 2 relaxation stages in worst case)
    # Rerank: O(k) MMR passes
    # Normalise to k=3 baseline
    BASE_K = 3
    q4 = {
        str(k): {
            "candidate_count": k,
            "rerank_count": k,
            "relative_cost_multiplier": round(k / BASE_K, 2),
            "stages_worst_case": 2,
            "total_chroma_calls_worst_case": 2,
            "total_candidates_worst_case": k * 2,
        }
        for k in FETCH_K_VALUES
    }

    # ─── Q5: Best diversity/cost ratio ───────────────────────────────────────
    # For each k: diversity gain (global reuse reduction @100) vs cost multiplier
    base_global_k3 = q3["3"]["n100"]["global"]
    diversity_cost_ratios = []
    for k in FETCH_K_VALUES:
        global_reuse = q3[str(k)]["n100"]["global"]
        reduction = round(base_global_k3 - global_reuse, 1)
        cost_mult = round(k / BASE_K, 2)
        roi_per_cost = round(reduction / cost_mult, 2) if cost_mult else 0
        diversity_cost_ratios.append({
            "fetch_k": k,
            "global_reuse_n100": global_reuse,
            "global_reduction_pp": reduction,
            "cost_multiplier": cost_mult,
            "diversity_per_cost_unit": roi_per_cost,
        })

    best = max(diversity_cost_ratios, key=lambda x: x["diversity_per_cost_unit"])
    recommendation = f"FETCH_K_{best['fetch_k']}"

    # ─── Verdict ─────────────────────────────────────────────────────────────
    # Validated if:
    # 1. There exists a fetch_k ≤ 10 where >50% of slices show visible depth gain
    # 2. Recommendation fetch_k ≤ 20 (operationally feasible)
    # 3. Global reuse reduction >= 5pp at recommended k
    slices_visible_at_k5 = q2["min_k_corpus_growth_visible"]["all_slices_at_k"]["5"]
    pct_visible_k5 = round(slices_visible_at_k5 / len(slices) * 100, 1)
    rec_reduction = best["global_reduction_pp"]

    validated = (
        pct_visible_k5 >= 50.0
        and int(best["fetch_k"]) <= 20
        and rec_reduction >= 5.0
    )
    verdict_str = (
        "TK_RETRIEVAL_SIZING_VALIDATED"
        if validated
        else "TK_RETRIEVAL_SIZING_REQUIRES_FURTHER_ANALYSIS"
    )

    report = {
        "audit": "Phase 7D-TK3 Technical Knowledge Retrieval Sizing Audit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "area": AREA_STR,
            "roles": [r.value for r in AUDIT_ROLES],
            "seniorities": [s.value for s in SENIORITY_LEVELS],
            "fetch_k_values": FETCH_K_VALUES,
            "corpus_probe_k": CORPUS_PROBE_K,
            "bg_live_depth_assumed": bg_live_depth,
            "cs_source": "7D-C2.1 live k=50 depths",
            "note": "Read-only. No corpus or production changes.",
        },
        "Q1_depth_by_fetch_k": q1,
        "Q2_minimum_fetch_k_thresholds": q2,
        "Q3_reuse_projections": q3,
        "Q4_retrieval_cost_model": q4,
        "Q5_diversity_cost_analysis": {
            "ratios": diversity_cost_ratios,
            "recommendation": recommendation,
            "best_fetch_k": best["fetch_k"],
            "best_global_reduction_pp": best["global_reduction_pp"],
            "best_cost_multiplier": best["cost_multiplier"],
            "best_diversity_per_cost": best["diversity_per_cost_unit"],
        },
        "verdict": {
            "verdict": verdict_str,
            "recommendation": recommendation,
            "slices_showing_gain_at_k5": f"{slices_visible_at_k5}/{len(slices)} ({pct_visible_k5}%)",
            "global_reduction_at_recommended_k": rec_reduction,
            "quantitative_justification": (
                f"At fetch_k={best['fetch_k']}: global reuse drops "
                f"from {base_global_k3}% → {best['global_reuse_n100']}% "
                f"(−{rec_reduction}pp) at cost multiplier {best['cost_multiplier']}x. "
                f"Diversity/cost ratio: {best['diversity_per_cost_unit']} pp per cost unit. "
                f"{slices_visible_at_k5}/{len(slices)} slices show depth gain at k=5."
            ),
        },
    }

    return report


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Starting Phase 7D-TK3 — Retrieval Sizing Audit...", flush=True)

    report = run_audit()

    full_path = OUTPUT_DIR / "phase_7d_tk3_retrieval_sizing.json"
    full_path.write_text(json.dumps(report, indent=2))

    summary_keys = [k for k in report if k not in ("Q1_depth_by_fetch_k",)]
    summary = {k: report[k] for k in summary_keys}
    (OUTPUT_DIR / "phase_7d_tk3_summary.json").write_text(json.dumps(summary, indent=2))

    v = report["verdict"]["verdict"]
    rec = report["verdict"]["recommendation"]
    print(f"\n=== {v} ===", flush=True)
    print(f"Recommendation: {rec}", flush=True)
    print(report["verdict"]["quantitative_justification"], flush=True)


if __name__ == "__main__":
    main()
