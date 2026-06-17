# scripts/question_intelligence/audit_question_reuse.py
# Question Reuse Audit — root cause analysis for duplicate-rate inflation.
# Tracks document_ids, text hashes, and candidate spread across 100 interviews.

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
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
from services.question_corpus.retrieval.interview_memory_updater import (
    InterviewMemoryUpdater,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"
INTERVIEW_COUNT = int(os.environ.get("INTERVIEW_COUNT", "100"))

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

_N_ROLES = len(ROLES_SENIORITIES)


def _normalize(text: str) -> str:
    import re
    return re.sub(r"\s+", " ", text.strip().lower())


def _text_hash(text: str) -> str:
    return hashlib.md5(_normalize(text).encode()).hexdigest()[:12]


def _jaccard(a: str, b: str) -> float:
    wa = set(a.split())
    wb = set(b.split())
    if not wa and not wb:
        return 1.0
    return len(wa & wb) / len(wa | wb)


def _probe_retrieval_pipeline(
    role: RoleType,
    level: SeniorityLevel,
    covered_domains: list[str],
    weak_domains: list[str],
    seen_doc_ids: set[str],
) -> dict[str, Any]:
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
        return {"raw_count": 0, "top10_doc_ids": [], "top10_previously_seen": 0}

    raw_sorted = sorted(raw, key=lambda c: c.final_score, reverse=True)

    cpe = CoveragePenaltyEngine()
    wbe = WeakDomainBoostEngine()
    pen_sorted = sorted(cpe.apply(raw_sorted, ctx), key=lambda c: c.final_score, reverse=True)
    boost_sorted = sorted(wbe.apply(pen_sorted, ctx), key=lambda c: c.final_score, reverse=True)

    top10 = boost_sorted[:10]
    top10_ids = [c.document.metadata.get("document_id", "?") for c in top10]
    top10_previously_seen = sum(1 for d in top10_ids if d in seen_doc_ids)

    mapper = RetrievalCandidateMapper()
    bank_items = mapper.map(raw_sorted[:5])
    bank_domains = [item.domains for item in bank_items]

    final_top1_id = top10_ids[0] if top10_ids else "?"
    final_top1_source = top10[0].document.metadata.get("source", "?") if top10 else "?"
    final_top1_domains = parse_domains(top10[0].document.metadata.get("domains", "")) if top10 else []
    final_top1_text = top10[0].document.page_content if top10 else ""

    return {
        "raw_count": len(raw_sorted),
        "top10_doc_ids": top10_ids,
        "top10_unique_count": len(set(top10_ids)),
        "top10_previously_seen": top10_previously_seen,
        "final_top1_doc": final_top1_id,
        "final_top1_source": final_top1_source,
        "final_top1_domains": final_top1_domains,
        "final_top1_text_hash": _text_hash(final_top1_text),
        "bank_item_domains_top5": bank_domains,
        "penalty_changed_top1": (
            raw_sorted[0].document.metadata.get("document_id") != pen_sorted[0].document.metadata.get("document_id")
            if raw_sorted and pen_sorted else False
        ),
        "boost_changed_top1": (
            pen_sorted[0].document.metadata.get("document_id") != boost_sorted[0].document.metadata.get("document_id")
            if pen_sorted and boost_sorted else False
        ),
    }


def _generate_interviews(
    provider: QuestionIntelligenceProvider,
) -> tuple[list[dict], list[dict], list[dict]]:
    records: list[dict] = []
    memory_snapshots: list[dict] = []
    retrieval_probes: list[dict] = []
    session_memory = InterviewRetrievalMemory()
    updater = InterviewMemoryUpdater()
    seen_doc_ids: set[str] = set()

    interview_idx = 0
    cycle = 0
    while interview_idx < INTERVIEW_COUNT:
        role, level = ROLES_SENIORITIES[interview_idx % _N_ROLES]
        interview_idx += 1

        print(f"[{interview_idx}/{INTERVIEW_COUNT}] {role.value} {level.value}", flush=True)

        probe = _probe_retrieval_pipeline(
            role=role,
            level=level,
            covered_domains=list(session_memory.covered_domains),
            weak_domains=list(session_memory.weak_domains),
            seen_doc_ids=seen_doc_ids,
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

        # The corpus document_id selected by retrieval comes from the probe
        probe_doc_id = probe.get("final_top1_doc", "?")
        probe_source = probe.get("final_top1_source", "?")

        for q in questions:
            provenance_domains = (
                q.provenance.domains if q.provenance and q.provenance.domains else []
            )
            source = q.provenance.source_name if q.provenance else probe_source

            records.append({
                "interview_id": interview_idx,
                "role": role.value,
                "seniority": level.value,
                "question_id": str(q.id),
                "corpus_document_id": probe_doc_id,
                "prompt": q.prompt,
                "prompt_normalized": _normalize(q.prompt),
                "text_hash": _text_hash(q.prompt),
                "difficulty": q.difficulty.value,
                "source": source,
                "provenance_domains": provenance_domains,
            })

            if probe_doc_id != "?":
                seen_doc_ids.add(probe_doc_id)

            session_memory = updater.update_from_question_evaluation(
                memory=session_memory,
                question=q,
                evaluation_score=0.6,
            )

        memory_snapshots.append({
            "interview_id": interview_idx,
            "covered_domains": list(session_memory.covered_domains),
            "weak_domains": list(session_memory.weak_domains),
            "strong_domains": list(session_memory.strong_domains),
        })

    return records, memory_snapshots, retrieval_probes


def _semantic_clusters(records: list[dict], threshold: float = 0.90) -> list[dict]:
    texts = [(r["prompt_normalized"], r["text_hash"], r["source"]) for r in records]
    hash_groups: dict[str, list[int]] = defaultdict(list)
    for i, (_, h, _) in enumerate(texts):
        hash_groups[h].append(i)

    # Exact duplicates
    clusters: list[dict] = []
    for h, idxs in hash_groups.items():
        if len(idxs) > 1:
            clusters.append({
                "type": "exact",
                "hash": h,
                "count": len(idxs),
                "sources": list({texts[i][2] for i in idxs}),
                "preview": texts[idxs[0]][0][:120],
            })

    # Near-duplicates (jaccard >= threshold, across different hashes)
    sampled = list(hash_groups.keys())
    hash_rep: dict[str, str] = {h: texts[idxs[0]][0] for h, idxs in hash_groups.items()}
    near: list[dict] = []
    checked = 0
    for ha, hb in combinations(sampled, 2):
        if checked > 5000:
            break
        checked += 1
        sim = _jaccard(hash_rep[ha], hash_rep[hb])
        if sim >= threshold:
            idxs_a = hash_groups[ha]
            idxs_b = hash_groups[hb]
            near.append({
                "type": "near_duplicate",
                "similarity": round(sim, 3),
                "count": len(idxs_a) + len(idxs_b),
                "sources": list({texts[i][2] for i in idxs_a + idxs_b}),
                "preview_a": hash_rep[ha][:100],
                "preview_b": hash_rep[hb][:100],
            })

    near.sort(key=lambda x: (-x["similarity"], -x["count"]))
    return sorted(clusters, key=lambda x: -x["count"]) + near[:20]


def _candidate_spread(retrieval_probes: list[dict]) -> dict:
    all_top10_ids = [p.get("top10_doc_ids", []) for p in retrieval_probes if p.get("top10_doc_ids")]
    if not all_top10_ids:
        return {}

    avg_unique = sum(p.get("top10_unique_count", 0) for p in retrieval_probes) / max(len(retrieval_probes), 1)
    avg_previously_seen = sum(p.get("top10_previously_seen", 0) for p in retrieval_probes) / max(len(retrieval_probes), 1)

    # Recurring candidate sets (frozenset top-5)
    candidate_set_counts: Counter = Counter(
        frozenset(ids[:5]) for ids in all_top10_ids if ids
    )
    top_recurring = [
        {"set": sorted(list(s)), "count": c}
        for s, c in candidate_set_counts.most_common(5)
    ]

    # Global doc_id frequency across all top-10 lists
    all_candidate_ids = [did for ids in all_top10_ids for did in ids]
    doc_id_freq = Counter(all_candidate_ids)

    return {
        "avg_unique_doc_ids_in_top10": round(avg_unique, 2),
        "avg_previously_seen_in_top10": round(avg_previously_seen, 2),
        "top_recurring_candidate_sets": top_recurring,
        "top10_most_frequent_candidates": [
            {"document_id": did, "appearances": cnt}
            for did, cnt in doc_id_freq.most_common(10)
        ],
    }


def _document_reuse_report(records: list[dict], retrieval_probes: list[dict]) -> list[dict]:
    # Count corpus document_id selections from retrieval probes
    retrieval_doc_counts: Counter = Counter(
        p.get("final_top1_doc", "?")
        for p in retrieval_probes
        if p.get("final_top1_doc") and p.get("final_top1_doc") != "?"
    )
    # Also count from records' corpus_document_id
    record_doc_counts: Counter = Counter(
        r.get("corpus_document_id", "?")
        for r in records
        if r.get("corpus_document_id") and r.get("corpus_document_id") != "?"
    )
    doc_meta: dict[str, dict] = {}
    for p in retrieval_probes:
        did = p.get("final_top1_doc")
        if did and did != "?":
            doc_meta[did] = {
                "source": p.get("final_top1_source", "?"),
                "domains": p.get("final_top1_domains", []),
            }

    combined = retrieval_doc_counts + record_doc_counts

    return [
        {
            "document_id": did,
            "retrieval_selections": retrieval_doc_counts.get(did, 0),
            "record_count": record_doc_counts.get(did, 0),
            "source": doc_meta.get(did, {}).get("source", "?"),
            "domains": doc_meta.get(did, {}).get("domains", []),
        }
        for did, _ in combined.most_common(20)
        if combined[did] > 1
    ]


def _report(
    records: list[dict],
    memory_snapshots: list[dict],
    retrieval_probes: list[dict],
) -> dict:
    total = len(records)
    prompt_counts = Counter(r["prompt_normalized"] for r in records)
    unique_prompts = len(prompt_counts)
    dup_rate = round((total - unique_prompts) / total * 100, 1) if total else 0.0

    hash_counts = Counter(r["text_hash"] for r in records)

    source_counts = Counter(r["source"] for r in records)
    domain_counts = Counter(d for r in records for d in r["provenance_domains"])

    top_repeated = [
        {"preview": p[:120], "count": c, "rate_pct": round(c / total * 100, 1)}
        for p, c in prompt_counts.most_common(10)
        if c > 1
    ]

    return {
        "summary": {
            "total_questions": total,
            "unique_prompts": unique_prompts,
            "duplicate_rate_pct": dup_rate,
            "unique_text_hashes": len(hash_counts),
        },
        "document_reuse_report": _document_reuse_report(records, retrieval_probes),
        "semantic_duplicate_report": _semantic_clusters(records),
        "candidate_spread": _candidate_spread(retrieval_probes),
        "source_distribution": dict(source_counts.most_common()),
        "domain_frequency": dict(domain_counts.most_common()),
        "top_repeated_questions": top_repeated,
    }


def main() -> None:
    load_dotenv()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"QUESTION REUSE AUDIT — {INTERVIEW_COUNT} interviews", flush=True)
    print("=" * 60, flush=True)

    llm = DefaultLLMAdapter()
    provider = QuestionIntelligenceProvider(llm)

    records, memory_snapshots, retrieval_probes = _generate_interviews(provider)
    report = _report(records, memory_snapshots, retrieval_probes)
    report["audit"] = "Question Reuse Audit"
    report["timestamp"] = datetime.now(timezone.utc).isoformat()
    report["interview_count"] = INTERVIEW_COUNT

    output_path = OUTPUT_DIR / "audit_question_reuse.json"
    full_report = {**report, "raw_records": records, "retrieval_probes": retrieval_probes}
    output_path.write_text(json.dumps(full_report, indent=2))

    summary = {k: v for k, v in report.items() if k != "raw_records"}
    print("\n" + json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}", flush=True)


if __name__ == "__main__":
    main()
