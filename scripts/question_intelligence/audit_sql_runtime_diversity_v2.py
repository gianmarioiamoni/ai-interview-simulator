# scripts/question_intelligence/audit_sql_runtime_diversity_v2.py
# Measures SQL runtime diversity after domain propagation.
# Generates 50 TECHNICAL database interviews and instruments:
#   - QuestionBankItem.domains after mapping
#   - InterviewRetrievalMemory.covered_domains evolution
#   - CoveragePenaltyEngine and WeakDomainBoostEngine ranking changes

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.retrieval.adaptive_context_builder import (
    AdaptiveContextBuilder,
)
from services.question_corpus.retrieval.adaptive_retrieval_policy import (
    AdaptiveRetrievalPolicy,
)
from services.question_corpus.retrieval.chroma_retrieval_service import (
    ChromaRetrievalService,
)
from services.question_corpus.retrieval.coverage_penalty_engine import (
    CoveragePenaltyEngine,
)
from services.question_corpus.retrieval.weak_domain_boost_engine import (
    WeakDomainBoostEngine,
)
from services.question_corpus.utils.domain_parser import parse_domains
from services.question_intelligence.adapters.retrieval_strategy_context_adapter import (
    RetrievalStrategyContextAdapter,
)
from services.question_intelligence.retrieval_query_builder import RetrievalQueryBuilder
from services.question_intelligence.retrieval.retrieval_strategy_resolver import (
    RetrievalStrategyResolver,
)
from infrastructure.llm.llm_adapter import DefaultLLMAdapter
from services.question_intelligence.question_intelligence_provider import (
    QuestionIntelligenceProvider,
)
from services.question_corpus.mappers.retrieval_candidate_mapper import (
    RetrievalCandidateMapper,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"
INTERVIEW_COUNT = 50

ROLES_SENIORITIES: list[tuple[RoleType, SeniorityLevel]] = [
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.JUNIOR),
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.MID),
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.JUNIOR),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.MID),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.DATA_ENGINEER, SeniorityLevel.MID),
    (RoleType.DATA_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.ML_ENGINEER, SeniorityLevel.MID),
    (RoleType.ML_ENGINEER, SeniorityLevel.SENIOR),
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _origin_label(q: Question) -> str:
    if q.provenance is None:
        return "generated"
    origin = q.provenance.origin_type
    if origin == QuestionOriginType.LLM_GENERATED:
        return "generated"
    if origin in (QuestionOriginType.RETRIEVAL, QuestionOriginType.HYBRID):
        return "retrieved"
    return origin.value


def _probe_retrieval_pipeline(
    role: RoleType,
    level: SeniorityLevel,
    covered_domains: list[str],
    weak_domains: list[str],
) -> dict[str, Any]:
    """
    Run the retrieval pipeline for one SQL query and capture:
    - raw candidate top-5 document_ids + domains
    - domain distribution before penalty
    - top-1 after coverage penalty
    - top-1 after weak-domain boost
    - whether penalty/boost changed the ranking
    """
    mem = InterviewRetrievalMemory(
        covered_domains=covered_domains,
        weak_domains=weak_domains,
    )
    qb = RetrievalQueryBuilder()
    sr = RetrievalStrategyResolver()
    adapter = RetrievalStrategyContextAdapter()

    query = qb.build(role=role, level=level, area=InterviewArea.TECH_DATABASE, memory=mem)
    strategy = sr.resolve(area=InterviewArea.TECH_DATABASE, level=level, questions_per_area=1)
    ctx = adapter.adapt(
        query, strategy, role.value, level.value,
        InterviewType.TECHNICAL.value, InterviewArea.TECH_DATABASE.value, mem,
    )

    policy = AdaptiveRetrievalPolicy()
    chroma_svc = ChromaRetrievalService()
    raw = []
    for stage in policy.build_relaxation_stages(ctx):
        raw = chroma_svc.search_with_filters(query=query, filters=stage, k=30)
        if raw:
            break

    if not raw:
        return {"raw_count": 0}

    raw_sorted = sorted(raw, key=lambda c: c.final_score, reverse=True)

    cpe = CoveragePenaltyEngine()
    wbe = WeakDomainBoostEngine()

    penalized = cpe.apply(raw_sorted, ctx)
    pen_sorted = sorted(penalized, key=lambda c: c.final_score, reverse=True)

    boosted = wbe.apply(pen_sorted, ctx)
    boost_sorted = sorted(boosted, key=lambda c: c.final_score, reverse=True)

    def top_doc(candidates: list) -> str:
        return candidates[0].document.metadata.get("document_id", "?") if candidates else "?"

    def top_domains(candidates: list) -> list[str]:
        if not candidates:
            return []
        return parse_domains(candidates[0].document.metadata.get("domains", ""))

    raw_domain_dist = Counter(
        d
        for c in raw_sorted
        for d in parse_domains(c.document.metadata.get("domains", ""))
    )

    mapper = RetrievalCandidateMapper()
    bank_items = mapper.map(raw_sorted[:5])
    bank_domains = [item.domains for item in bank_items]

    return {
        "raw_count": len(raw_sorted),
        "raw_top1_doc": top_doc(raw_sorted),
        "raw_top1_domains": top_domains(raw_sorted),
        "raw_domain_dist": dict(raw_domain_dist.most_common()),
        "penalty_top1_doc": top_doc(pen_sorted),
        "penalty_top1_domains": top_domains(pen_sorted),
        "penalty_changed_top1": top_doc(raw_sorted) != top_doc(pen_sorted),
        "boost_top1_doc": top_doc(boost_sorted),
        "boost_top1_domains": top_domains(boost_sorted),
        "boost_changed_top1": top_doc(pen_sorted) != top_doc(boost_sorted),
        "bank_item_domains_top5": bank_domains,
        "covered_domains_input": covered_domains,
        "weak_domains_input": weak_domains,
    }


def _generate_interviews(
    provider: QuestionIntelligenceProvider,
) -> tuple[list[dict], list[dict]]:
    records: list[dict] = []
    memory_snapshots: list[dict] = []
    retrieval_probes: list[dict] = []

    interview_idx = 0
    # Accumulate a shared memory across consecutive same-role batches
    # to measure covered_domains evolution within a session
    session_memory = InterviewRetrievalMemory()

    for cycle in range(5):
        for role, level in ROLES_SENIORITIES:
            interview_idx += 1
            if interview_idx > INTERVIEW_COUNT:
                break

            print(f"[{interview_idx}/{INTERVIEW_COUNT}] {role.value} {level.value}", flush=True)

            # Probe retrieval before generating (with current session_memory)
            probe = _probe_retrieval_pipeline(
                role=role,
                level=level,
                covered_domains=list(session_memory.covered_domains),
                weak_domains=list(session_memory.weak_domains),
            )
            probe["interview_id"] = interview_idx
            retrieval_probes.append(probe)

            try:
                questions = provider.generate(
                    role=role,
                    level=level,
                    interview_type=InterviewType.TECHNICAL,
                    areas=[InterviewArea.TECH_DATABASE],
                    questions_per_area=1,
                )
            except Exception as exc:
                print(f"  ERROR: {exc}", flush=True)
                continue

            for q in questions:
                provenance_domains = (
                    q.provenance.domains
                    if q.provenance and q.provenance.domains
                    else []
                )
                source = (
                    q.provenance.source_name
                    if q.provenance
                    else "unknown"
                )
                records.append({
                    "interview_id": interview_idx,
                    "role": role.value,
                    "seniority": level.value,
                    "question_id": q.id,
                    "prompt": q.prompt,
                    "prompt_normalized": _normalize(q.prompt),
                    "difficulty": q.difficulty.value,
                    "source": source,
                    "provenance_domains": provenance_domains,
                    "origin": _origin_label(q),
                })

                # Simulate memory update with provenance domains
                from services.question_corpus.retrieval.interview_memory_updater import (
                    InterviewMemoryUpdater,
                )
                # We can't call record_bank_item_selection (no bank item here),
                # but we can simulate via update_from_question_evaluation
                updater = InterviewMemoryUpdater()
                session_memory = updater.update_from_question_evaluation(
                    memory=session_memory,
                    question=q,
                    evaluation_score=0.6,  # neutral score
                )

            memory_snapshots.append({
                "interview_id": interview_idx,
                "covered_domains": list(session_memory.covered_domains),
                "weak_domains": list(session_memory.weak_domains),
                "strong_domains": list(session_memory.strong_domains),
            })

        if interview_idx >= INTERVIEW_COUNT:
            break

    return records, memory_snapshots, retrieval_probes


def _consecutive_same_domain_runs(records: list[dict]) -> int:
    domains_seq = [r["provenance_domains"] for r in records]
    runs = 0
    for i in range(1, len(domains_seq)):
        prev = set(domains_seq[i - 1])
        curr = set(domains_seq[i])
        if prev and curr and prev & curr:
            runs += 1
    return runs


def _report(
    records: list[dict],
    memory_snapshots: list[dict],
    retrieval_probes: list[dict],
) -> dict:
    total = len(records)
    all_prompts = [r["prompt_normalized"] for r in records]
    prompt_counts = Counter(all_prompts)
    unique_prompts = len(prompt_counts)
    dup_rate = round((total - unique_prompts) / total * 100, 1) if total else 0.0

    # Domain stats from provenance
    resolved = [r for r in records if r["provenance_domains"]]
    unresolved = [r for r in records if not r["provenance_domains"]]
    all_domains_flat = [d for r in resolved for d in r["provenance_domains"]]
    domain_counts = Counter(all_domains_flat)

    combo_counts = Counter(
        tuple(sorted(r["provenance_domains"])) for r in resolved
    )
    unique_domain_combos = len(combo_counts)
    consecutive = _consecutive_same_domain_runs(records)

    # Coverage penalty / boost effectiveness
    penalty_changes = sum(1 for p in retrieval_probes if p.get("penalty_changed_top1"))
    boost_changes = sum(1 for p in retrieval_probes if p.get("boost_changed_top1"))
    probes_with_data = sum(1 for p in retrieval_probes if p.get("raw_count", 0) > 0)

    # Memory evolution
    final_memory = memory_snapshots[-1] if memory_snapshots else {}
    covered_evolution = [
        {"interview_id": s["interview_id"], "covered_count": len(s["covered_domains"])}
        for s in memory_snapshots
    ]

    # Bank item domain propagation (from probes)
    bank_items_with_domains = sum(
        1 for p in retrieval_probes
        for domains in p.get("bank_item_domains_top5", [])
        if domains
    )
    bank_items_total = sum(
        len(p.get("bank_item_domains_top5", []))
        for p in retrieval_probes
    )

    source_counts = Counter(r["source"] for r in records)
    difficulty_counts = Counter(r["difficulty"] for r in records)

    top_repeated = [
        {"prompt_preview": p[:100], "count": c, "rate_pct": round(c / total * 100, 1)}
        for p, c in prompt_counts.most_common(10)
        if c > 1
    ]

    return {
        "question_statistics": {
            "total": total,
            "unique_prompts": unique_prompts,
            "duplicate_rate_pct": dup_rate,
            "resolved_domains_count": len(resolved),
            "unresolved_domains_count": len(unresolved),
        },
        "domain_statistics": {
            "domain_frequency": dict(domain_counts.most_common()),
            "unique_domain_combos": unique_domain_combos,
            "consecutive_same_domain_runs": consecutive,
            "top_combos": [
                {"combo": list(k), "count": v, "pct": round(v / len(resolved) * 100, 1)}
                for k, v in combo_counts.most_common(10)
            ] if resolved else [],
        },
        "memory_effectiveness": {
            "final_covered_domains": final_memory.get("covered_domains", []),
            "final_covered_count": len(final_memory.get("covered_domains", [])),
            "final_weak_domains": final_memory.get("weak_domains", []),
            "final_strong_domains": final_memory.get("strong_domains", []),
            "covered_evolution_sample": covered_evolution[::5],
        },
        "retrieval_behavior": {
            "probes_with_data": probes_with_data,
            "coverage_penalty_changed_top1": penalty_changes,
            "coverage_penalty_change_rate_pct": round(
                penalty_changes / max(probes_with_data, 1) * 100, 1
            ),
            "weak_boost_changed_top1": boost_changes,
            "weak_boost_change_rate_pct": round(
                boost_changes / max(probes_with_data, 1) * 100, 1
            ),
            "bank_items_with_domains": bank_items_with_domains,
            "bank_items_total": bank_items_total,
            "bank_item_domain_propagation_pct": round(
                bank_items_with_domains / max(bank_items_total, 1) * 100, 1
            ),
        },
        "diversity_comparison": {
            "baseline_duplicate_rate_pct": 3.3,
            "current_duplicate_rate_pct": dup_rate,
            "baseline_unique_domain_combos": 2,
            "current_unique_domain_combos": unique_domain_combos,
            "baseline_interviews": 30,
            "current_interviews": total,
        },
        "source_distribution": dict(source_counts.most_common()),
        "difficulty_distribution": dict(sorted(difficulty_counts.items())),
        "top_repeated_questions": top_repeated,
    }


def main() -> None:
    load_dotenv()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("SQL RUNTIME DIVERSITY AUDIT v2 — post domain propagation", flush=True)
    print("=" * 60, flush=True)

    llm = DefaultLLMAdapter()
    provider = QuestionIntelligenceProvider(llm)

    records, memory_snapshots, retrieval_probes = _generate_interviews(provider)

    report = _report(records, memory_snapshots, retrieval_probes)
    report["audit"] = "SQL Runtime Diversity v2 — post domain propagation"
    report["timestamp"] = datetime.now(timezone.utc).isoformat()
    report["raw_records"] = records
    report["retrieval_probes"] = retrieval_probes
    report["memory_snapshots"] = memory_snapshots

    output_path = OUTPUT_DIR / "audit_sql_runtime_diversity_v2.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary = {k: v for k, v in report.items() if k not in {"raw_records", "retrieval_probes", "memory_snapshots"}}
    print("\n" + json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}", flush=True)


if __name__ == "__main__":
    main()
