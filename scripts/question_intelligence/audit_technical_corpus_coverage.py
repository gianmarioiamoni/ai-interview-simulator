# scripts/question_intelligence/audit_technical_corpus_coverage.py

# Phase 7C-T0 — Technical Corpus Coverage & Survival Audit (read-only).

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

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
from services.question_corpus.retrieval.adaptive_retrieval_policy import (
    AdaptiveRetrievalPolicy,
)
from services.question_corpus.retrieval.chroma_retrieval_service import (
    ChromaRetrievalService,
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

SOURCE_ROOTS = [
    PROJECT_ROOT / "datasets/curated/hf_import",
    PROJECT_ROOT / "datasets/curated/interview_seed",
    PROJECT_ROOT / "datasets/curated/local_import",
]

TECH_AREAS = [
    "technical_background",
    "technical_technical_knowledge",
    "technical_case_study",
]

ROLE_BUCKETS = [
    "backend",
    "fullstack",
    "frontend",
    "data",
    "devops",
    "qa",
    "ml",
    "generic",
]

SENIORITIES = ["junior", "mid", "senior"]

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

CONCENTRATION_THRESHOLD = 0.50
FRESH_START_TARGET_DIFFICULTY = 3

# Phase 7C-B2D observed technical reuse (batch path).
B2D_BASELINE = {
    "technical_background": {"prompts": 20, "unique": 7, "reuse_pct": 65.0},
    "technical_technical_knowledge": {"prompts": 20, "unique": 11, "reuse_pct": 45.0},
    "technical_case_study": {"prompts": 20, "unique": 13, "reuse_pct": 35.0},
}

CORPUS_PROBE_K = 200


@dataclass
class CorpusDocument:
    document_id: str
    area: str
    role: str
    seniority: str
    difficulty: int
    role_bucket: str
    question_preview: str


@dataclass
class AreaCoverage:
    area: str
    total_documents: int
    unique_documents: int
    by_role: dict[str, int]
    by_seniority: dict[str, int]
    by_difficulty: dict[str, int]
    role_concentration_pct: dict[str, float]
    seniority_concentration_pct: dict[str, float]
    role_flags_over_50pct: list[str]
    seniority_flags_over_50pct: list[str]
    role_seniority_matrix: dict[str, dict[str, int]]
    source_json_total: int
    indexed_gap: int


@dataclass
class SurvivalCell:
    area: str
    role: str
    seniority: str
    strict_count: int
    bucket: str


@dataclass
class FunnelStage:
    stage: str
    document_count: int
    loss_from_previous: int
    loss_pct_from_previous: float
    loss_pct_from_area: float


@dataclass
class FilterFunnel:
    area: str
    role: str
    seniority: str
    stages: list[FunnelStage]
    strict_corpus_count: int
    chroma_retrieval_pool: int
    filter_stage_used: int
    root_cause: str


def _role_bucket(role: str) -> str:
    mapping = {
        "backend_engineer": "backend",
        "fullstack_engineer": "fullstack",
        "frontend_engineer": "frontend",
        "data_engineer": "data",
        "devops_engineer": "devops",
        "qa_engineer": "qa",
        "ml_engineer": "ml",
        "other": "generic",
    }
    return mapping.get(role, "generic")


def _load_source_json_counts() -> dict[str, int]:
    counts: Counter[str] = Counter()

    for root in SOURCE_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*.json"):
            try:
                data = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            if not isinstance(data, list):
                continue

            for item in data:
                if not isinstance(item, dict):
                    continue

                area = item.get("area")
                if area in TECH_AREAS:
                    counts[str(area)] += 1

    return dict(counts)


def _load_chroma_documents() -> list[CorpusDocument]:
    load_dotenv(PROJECT_ROOT / ".env")

    vectorstore = Chroma(
        collection_name="interview_questions",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=str(PROJECT_ROOT / "storage/chroma/interview_corpus"),
    )
    collection = vectorstore._collection

    documents: list[CorpusDocument] = []

    for area in TECH_AREAS:
        result = collection.get(
            where={"area": area},
            include=["metadatas", "documents"],
        )

        ids = result.get("ids") or []
        metas = result.get("metadatas") or []
        contents = result.get("documents") or []

        for index, metadata in enumerate(metas):
            if not metadata:
                continue

            role = str(metadata.get("role", "unknown"))
            seniority = str(metadata.get("seniority", "unknown"))

            try:
                difficulty = int(metadata.get("difficulty", 3))
            except (TypeError, ValueError):
                difficulty = 3

            document_id = str(metadata.get("document_id") or ids[index])
            preview = contents[index][:80] if index < len(contents) else ""

            documents.append(
                CorpusDocument(
                    document_id=document_id,
                    area=str(metadata.get("area", area)),
                    role=role,
                    seniority=seniority,
                    difficulty=difficulty,
                    role_bucket=_role_bucket(role),
                    question_preview=preview,
                )
            )

    return documents


def _documents_for_area(
    documents: list[CorpusDocument],
    area: str,
) -> list[CorpusDocument]:
    return [doc for doc in documents if doc.area == area]


def _concentration(counts: dict[str, int]) -> dict[str, float]:
    total = sum(counts.values())
    if total == 0:
        return {key: 0.0 for key in counts}

    return {key: round((value / total) * 100, 1) for key, value in counts.items()}


def _flags_over_threshold(
    concentration: dict[str, float],
    *,
    threshold_pct: float = CONCENTRATION_THRESHOLD * 100,
) -> list[str]:
    return [
        label
        for label, pct in concentration.items()
        if pct > threshold_pct and label != "unknown"
    ]


def _build_area_coverage(
    area: str,
    documents: list[CorpusDocument],
    source_json_counts: dict[str, int],
) -> AreaCoverage:
    area_docs = _documents_for_area(documents, area)

    by_role = Counter(doc.role_bucket for doc in area_docs)
    by_seniority = Counter(doc.seniority for doc in area_docs)
    by_difficulty = Counter(str(doc.difficulty) for doc in area_docs)

    role_counts = {bucket: by_role.get(bucket, 0) for bucket in ROLE_BUCKETS}
    seniority_counts = {level: by_seniority.get(level, 0) for level in SENIORITIES}
    difficulty_counts = {str(d): by_difficulty.get(str(d), 0) for d in range(1, 6)}

    role_conc = _concentration(role_counts)
    seniority_conc = _concentration(seniority_counts)

    matrix: dict[str, dict[str, int]] = {
        bucket: {seniority: 0 for seniority in SENIORITIES}
        for bucket in ROLE_BUCKETS
    }

    for doc in area_docs:
        matrix[doc.role_bucket][doc.seniority] = (
            matrix[doc.role_bucket].get(doc.seniority, 0) + 1
        )

    unique_ids = {doc.document_id for doc in area_docs}
    source_total = source_json_counts.get(area, 0)

    return AreaCoverage(
        area=area,
        total_documents=len(area_docs),
        unique_documents=len(unique_ids),
        by_role=role_counts,
        by_seniority=seniority_counts,
        by_difficulty=difficulty_counts,
        role_concentration_pct=role_conc,
        seniority_concentration_pct=seniority_conc,
        role_flags_over_50pct=_flags_over_threshold(role_conc),
        seniority_flags_over_50pct=_flags_over_threshold(seniority_conc),
        role_seniority_matrix=matrix,
        source_json_total=source_total,
        indexed_gap=max(source_total - len(area_docs), 0),
    )


def _matches_difficulty(
    doc: CorpusDocument,
    *,
    min_difficulty: int | None,
    max_difficulty: int | None,
) -> bool:
    if min_difficulty is not None and doc.difficulty < min_difficulty:
        return False

    if max_difficulty is not None and doc.difficulty > max_difficulty:
        return False

    return True


def _strict_matches(
    doc: CorpusDocument,
    *,
    role: str,
    seniority: str,
    min_difficulty: int | None,
    max_difficulty: int | None,
) -> bool:
    if doc.role != role:
        return False

    if doc.seniority != seniority:
        return False

    return _matches_difficulty(
        doc,
        min_difficulty=min_difficulty,
        max_difficulty=max_difficulty,
    )


def _survival_bucket(count: int) -> str:
    if count == 0:
        return "zero_match"

    if count <= 3:
        return "lte_3"

    if count >= 10:
        return "gte_10"

    return "mid_4_9"


def _build_survival_matrix(
    documents: list[CorpusDocument],
) -> dict:
    policy = AdaptiveRetrievalPolicy()
    cells: list[SurvivalCell] = []
    summary: Counter[str] = Counter()

    for area in TECH_AREAS:
        area_docs = _documents_for_area(documents, area)

        for role in AUDIT_ROLES:
            for seniority in SeniorityLevel:
                context = AdaptiveRetrievalContext(
                    current_role=role.value,
                    seniority=seniority.value,
                    target_area=area,
                    target_question_count=1,
                    already_used_domains=[],
                    weak_domains=[],
                    strong_domains=[],
                    target_difficulty=FRESH_START_TARGET_DIFFICULTY,
                    retrieval_query=None,
                    memory=InterviewRetrievalMemory(),
                )

                strict = policy.build_relaxation_stages(context)[0]
                matches = [
                    doc
                    for doc in area_docs
                    if _strict_matches(
                        doc,
                        role=strict.role or role.value,
                        seniority=strict.seniority or seniority.value,
                        min_difficulty=strict.min_difficulty,
                        max_difficulty=strict.max_difficulty,
                    )
                ]
                count = len({doc.document_id for doc in matches})
                bucket = _survival_bucket(count)
                summary[bucket] += 1

                cells.append(
                    SurvivalCell(
                        area=area,
                        role=role.value,
                        seniority=seniority.value,
                        strict_count=count,
                        bucket=bucket,
                    )
                )

    return {
        "cells": [asdict(cell) for cell in cells],
        "summary": dict(summary),
        "total_cells": len(cells),
    }


def _build_funnel_for_profile(
    *,
    area: str,
    area_docs: list[CorpusDocument],
    role: RoleType,
    seniority: SeniorityLevel,
    chroma: ChromaRetrievalService,
    policy: AdaptiveRetrievalPolicy,
    context_adapter: RetrievalStrategyContextAdapter,
    query_builder: RetrievalQueryBuilder,
    strategy_resolver: RetrievalStrategyResolver,
) -> FilterFunnel:
    interview_area = InterviewArea(area)
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

    context = context_adapter.adapt(
        query=query,
        retrieval_strategy=strategy,
        role=role.value,
        level=seniority.value,
        interview_type=InterviewType.TECHNICAL.value,
        area=area,
        memory=memory,
    )

    stages_filters = policy.build_relaxation_stages(context)
    strict = stages_filters[0]

    area_ids = {doc.document_id for doc in area_docs}
    area_count = len(area_ids)

    role_matches = {
        doc.document_id
        for doc in area_docs
        if doc.role == role.value
    }
    seniority_matches = {
        doc.document_id
        for doc in area_docs
        if doc.role == role.value and doc.seniority == seniority.value
    }
    strict_matches = {
        doc.document_id
        for doc in area_docs
        if _strict_matches(
            doc,
            role=role.value,
            seniority=seniority.value,
            min_difficulty=strict.min_difficulty,
            max_difficulty=strict.max_difficulty,
        )
    }

    counts = [
        ("1_area_corpus", area_count),
        ("2_role_filter", len(role_matches)),
        ("3_seniority_filter", len(seniority_matches)),
        ("4_difficulty_filter", len(strict_matches)),
    ]

    funnel_stages: list[FunnelStage] = []
    previous = area_count

    for stage_name, count in counts:
        loss = max(previous - count, 0)
        funnel_stages.append(
            FunnelStage(
                stage=stage_name,
                document_count=count,
                loss_from_previous=loss,
                loss_pct_from_previous=round((loss / previous) * 100, 1)
                if previous
                else 0.0,
                loss_pct_from_area=round(((area_count - count) / area_count) * 100, 1)
                if area_count
                else 0.0,
            )
        )
        previous = count

    chroma_strict = chroma.search_with_filters(
        query=query,
        filters=strict,
        k=CORPUS_PROBE_K,
    )
    retrieval_ids = {
        str(c.document.metadata.get("document_id", ""))
        for c in chroma_strict
        if c.document.metadata.get("document_id")
    }

    fetch_k = context.target_question_count * 3
    chroma_pool = chroma.search_with_filters(
        query=query,
        filters=strict,
        k=fetch_k,
    )
    pool_ids = {
        str(c.document.metadata.get("document_id", ""))
        for c in chroma_pool
        if c.document.metadata.get("document_id")
    }

    funnel_stages.append(
        FunnelStage(
            stage="5_chroma_probe_k200",
            document_count=len(retrieval_ids),
            loss_from_previous=max(len(strict_matches) - len(retrieval_ids), 0),
            loss_pct_from_previous=round(
                (
                    max(len(strict_matches) - len(retrieval_ids), 0)
                    / max(len(strict_matches), 1)
                )
                * 100,
                1,
            ),
            loss_pct_from_area=round(
                ((area_count - len(retrieval_ids)) / area_count) * 100,
                1,
            )
            if area_count
            else 0.0,
        )
    )

    funnel_stages.append(
        FunnelStage(
            stage="6_final_retrieval_pool",
            document_count=len(pool_ids),
            loss_from_previous=max(len(retrieval_ids) - len(pool_ids), 0),
            loss_pct_from_previous=round(
                (
                    max(len(retrieval_ids) - len(pool_ids), 0)
                    / max(len(retrieval_ids), 1)
                )
                * 100,
                1,
            ),
            loss_pct_from_area=round(
                ((area_count - len(pool_ids)) / area_count) * 100,
                1,
            )
            if area_count
            else 0.0,
        )
    )

    root_cause = _classify_root_cause(
        area_count=area_count,
        strict_count=len(strict_matches),
        pool_count=len(pool_ids),
        role_loss_pct=funnel_stages[1].loss_pct_from_previous,
        seniority_loss_pct=funnel_stages[2].loss_pct_from_previous,
        difficulty_loss_pct=funnel_stages[3].loss_pct_from_previous,
        coverage=area_count,
    )

    return FilterFunnel(
        area=area,
        role=role.value,
        seniority=seniority.value,
        stages=[asdict(stage) for stage in funnel_stages],
        strict_corpus_count=len(strict_matches),
        chroma_retrieval_pool=len(pool_ids),
        filter_stage_used=1,
        root_cause=root_cause,
    )


def _classify_root_cause(
    *,
    area_count: int,
    strict_count: int,
    pool_count: int,
    role_loss_pct: float,
    seniority_loss_pct: float,
    difficulty_loss_pct: float,
    coverage: int,
) -> str:
    causes: list[str] = []

    if area_count <= 15:
        causes.append("A_corpus_scarcity")

    if role_loss_pct > 40 or seniority_loss_pct > 40:
        causes.append("B_metadata_concentration")

    if strict_count <= 3 and area_count > strict_count:
        causes.append("C_filter_collapse")

    if pool_count <= 3 and strict_count > pool_count:
        causes.append("C_retrieval_ranking")

    if not causes:
        if strict_count <= 5:
            return "A_corpus_scarcity"

        return "D_healthy"

    if len(causes) > 1:
        return "D_combination"

    return causes[0]


def _aggregate_funnel_by_area(funnels: list[FilterFunnel]) -> list[dict]:
    grouped: dict[str, list[FilterFunnel]] = defaultdict(list)

    for funnel in funnels:
        grouped[funnel.area].append(funnel)

    aggregated: list[dict] = []

    for area in TECH_AREAS:
        rows = grouped.get(area, [])
        if not rows:
            continue

        stage_names = [stage["stage"] for stage in rows[0].stages]
        avg_by_stage: dict[str, float] = {}

        for stage_name in stage_names:
            values = [
                next(s["document_count"] for s in row.stages if s["stage"] == stage_name)
                for row in rows
            ]
            avg_by_stage[stage_name] = round(sum(values) / len(values), 1)

        avg_strict = round(
            sum(row.strict_corpus_count for row in rows) / len(rows),
            1,
        )
        avg_pool = round(
            sum(row.chroma_retrieval_pool for row in rows) / len(rows),
            1,
        )
        causes = Counter(row.root_cause for row in rows)

        aggregated.append(
            {
                "area": area,
                "profiles_sampled": len(rows),
                "avg_documents_by_stage": avg_by_stage,
                "avg_strict_corpus": avg_strict,
                "avg_final_pool": avg_pool,
                "dominant_root_cause": causes.most_common(1)[0][0],
                "root_cause_counts": dict(causes),
            }
        )

    return aggregated


def _estimate_unique_prompts(
    *,
    pool_size: float,
    prompts: int,
    overlap_discount: float = 0.72,
) -> int:
    if pool_size <= 0:
        return 1

    effective = min(pool_size, prompts)
    projected = int(effective * overlap_discount + (prompts - effective) * 0.12)
    return max(1, min(prompts, projected))


def _diversity_ceiling(
    coverage: list[AreaCoverage],
    survival: dict,
) -> dict:
    current: dict[str, dict] = {}
    metadata_only: dict[str, dict] = {}
    expansion: dict[str, dict] = {}

    for area_cov in coverage:
        area = area_cov.area
        baseline = B2D_BASELINE[area]
        prompts = baseline["prompts"]

        avg_strict = 0.0
        cells = [
            cell
            for cell in survival["cells"]
            if cell["area"] == area
        ]
        if cells:
            avg_strict = sum(cell["strict_count"] for cell in cells) / len(cells)

        current_unique = baseline["unique"]
        current_reuse = baseline["reuse_pct"]

        current[area] = {
            "observed_unique_prompts_b2d": current_unique,
            "observed_reuse_pct_b2d": current_reuse,
            "avg_strict_pool_per_profile": round(avg_strict, 1),
            "indexed_corpus": area_cov.unique_documents,
        }

        generic_share = area_cov.role_concentration_pct.get("generic", 0.0)
        redistributed_pool = avg_strict + (area_cov.by_role.get("generic", 0) * 0.35)

        meta_unique = _estimate_unique_prompts(
            pool_size=redistributed_pool,
            prompts=prompts,
        )
        metadata_only[area] = {
            "generic_role_docs": area_cov.by_role.get("generic", 0),
            "generic_share_pct": generic_share,
            "projected_avg_strict_pool": round(redistributed_pool, 1),
            "projected_unique_prompts": meta_unique,
            "projected_reuse_pct": round((1 - meta_unique / prompts) * 100, 1),
        }

        expansion[area] = {}
        for target_size in (15, 30, 50):
            scale = target_size / max(area_cov.unique_documents, 1)
            expanded_strict = min(target_size, avg_strict * scale)
            exp_unique = _estimate_unique_prompts(
                pool_size=expanded_strict,
                prompts=prompts,
            )
            expansion[area][f"corpus_{target_size}"] = {
                "target_indexed_docs": target_size,
                "projected_avg_strict_pool": round(expanded_strict, 1),
                "projected_unique_prompts": exp_unique,
                "projected_reuse_pct": round((1 - exp_unique / prompts) * 100, 1),
            }

    return {
        "current_ceiling": current,
        "metadata_only_remediation": metadata_only,
        "corpus_expansion_remediation": expansion,
    }


def _bottleneck_ranking(
    coverage: list[AreaCoverage],
    survival: dict,
    funnel_agg: list[dict],
) -> list[dict]:
    ranking: list[dict] = []

    for area_cov in coverage:
        area = area_cov.area
        baseline = B2D_BASELINE[area]

        zero_cells = sum(
            1
            for cell in survival["cells"]
            if cell["area"] == area and cell["bucket"] == "zero_match"
        )
        lte3_cells = sum(
            1
            for cell in survival["cells"]
            if cell["area"] == area and cell["bucket"] == "lte_3"
        )

        funnel_row = next(
            (row for row in funnel_agg if row["area"] == area),
            None,
        )
        avg_pool = funnel_row["avg_final_pool"] if funnel_row else 0.0
        root_cause = funnel_row["dominant_root_cause"] if funnel_row else "unknown"

        score = (
            baseline["reuse_pct"] * 0.4
            + lte3_cells * 3
            + zero_cells * 5
            + max(0, 15 - area_cov.unique_documents) * 2
            + max(0, 3 - avg_pool) * 8
        )

        ranking.append(
            {
                "area": area,
                "priority_score": round(score, 1),
                "b2d_reuse_pct": baseline["reuse_pct"],
                "indexed_docs": area_cov.unique_documents,
                "avg_final_pool": avg_pool,
                "zero_match_cells": zero_cells,
                "lte_3_cells": lte3_cells,
                "role_concentration_flags": area_cov.role_flags_over_50pct,
                "seniority_concentration_flags": area_cov.seniority_flags_over_50pct,
                "dominant_root_cause": root_cause,
            }
        )

    ranking.sort(key=lambda item: item["priority_score"], reverse=True)
    return ranking


def _metadata_diversity_matrix(coverage: list[AreaCoverage]) -> list[dict]:
    matrix: list[dict] = []

    for area_cov in coverage:
        matrix.append(
            {
                "area": area_cov.area,
                "by_role": area_cov.by_role,
                "role_concentration_pct": area_cov.role_concentration_pct,
                "role_flags_over_50pct": area_cov.role_flags_over_50pct,
                "by_seniority": area_cov.by_seniority,
                "seniority_concentration_pct": area_cov.seniority_concentration_pct,
                "seniority_flags_over_50pct": area_cov.seniority_flags_over_50pct,
                "by_difficulty": area_cov.by_difficulty,
            }
        )

    return matrix


def _recommended_remediation(ranking: list[dict], ceiling: dict) -> dict:
    top = ranking[0] if ranking else None

    if not top:
        return {"phase": "none", "actions": []}

    actions: list[str] = []

    if top["dominant_root_cause"] in {
        "A_corpus_scarcity",
        "D_combination",
    }:
        actions.append(
            f"Expand {top['area']} corpus to ≥30 indexed docs "
            f"(current {top['indexed_docs']})"
        )

    if top["role_concentration_flags"] or top["seniority_concentration_flags"]:
        actions.append(
            f"Re-tag metadata in {top['area']}: diversify "
            f"{', '.join(top['role_concentration_flags'] + top['seniority_concentration_flags'])}"
        )

    if top["avg_final_pool"] <= 3:
        actions.append(
            f"Strict-filter collapse in {top['area']}: "
            "corpus expansion primary; metadata redistribution secondary"
        )

    exp = ceiling["corpus_expansion_remediation"].get(top["area"], {})
    corpus_30 = exp.get("corpus_30", {})

    return {
        "primary_area": top["area"],
        "recommended_phase": "Phase 7C-T1 — Technical Corpus Expansion",
        "secondary_phase": "Phase 7C-T2 — Technical Metadata Diversification",
        "expected_gain_at_30_docs": corpus_30,
        "actions": actions,
        "metadata_only_insufficient": all(
            ceiling["metadata_only_remediation"][area]["projected_reuse_pct"]
            > 30
            for area in TECH_AREAS
        ),
    }


TECH_PROFILES = [
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.MID),
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.MID),
    (RoleType.FRONTEND_ENGINEER, SeniorityLevel.MID),
    (RoleType.DATA_ENGINEER, SeniorityLevel.MID),
    (RoleType.DEVOPS_ENGINEER, SeniorityLevel.MID),
]


def run_audit() -> dict:
    source_json_counts = _load_source_json_counts()
    documents = _load_chroma_documents()

    coverage = [
        _build_area_coverage(area, documents, source_json_counts)
        for area in TECH_AREAS
    ]

    survival = _build_survival_matrix(documents)

    load_dotenv(PROJECT_ROOT / ".env")
    chroma = ChromaRetrievalService()
    policy = AdaptiveRetrievalPolicy()
    query_builder = RetrievalQueryBuilder()
    strategy_resolver = RetrievalStrategyResolver()
    context_adapter = RetrievalStrategyContextAdapter()

    funnels: list[FilterFunnel] = []

    for area in TECH_AREAS:
        area_docs = _documents_for_area(documents, area)

        for role, seniority in TECH_PROFILES:
            funnels.append(
                _build_funnel_for_profile(
                    area=area,
                    area_docs=area_docs,
                    role=role,
                    seniority=seniority,
                    chroma=chroma,
                    policy=policy,
                    context_adapter=context_adapter,
                    query_builder=query_builder,
                    strategy_resolver=strategy_resolver,
                )
            )

    funnel_agg = _aggregate_funnel_by_area(funnels)
    ceiling = _diversity_ceiling(coverage, survival)
    ranking = _bottleneck_ranking(coverage, survival, funnel_agg)
    remediation = _recommended_remediation(ranking, ceiling)

    coverage_matrix = [
        {
            "area": item.area,
            "total_docs": item.total_documents,
            "unique_docs": item.unique_documents,
            "source_json_total": item.source_json_total,
            "indexed_gap": item.indexed_gap,
        }
        for item in coverage
    ]

    return {
        "audit": "Phase 7C-T0 Technical Corpus Coverage & Survival",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "storage/chroma/interview_corpus (indexed production corpus)",
        "areas": TECH_AREAS,
        "coverage_matrix": coverage_matrix,
        "metadata_diversity_matrix": _metadata_diversity_matrix(coverage),
        "survival_matrix": survival,
        "filter_funnel": {
            "by_profile": [asdict(f) for f in funnels],
            "aggregated_by_area": funnel_agg,
        },
        "diversity_ceiling": ceiling,
        "bottleneck_ranking": ranking,
        "recommended_remediation": remediation,
        "coverage_detail": [asdict(item) for item in coverage],
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_audit()

    output_path = OUTPUT_DIR / "phase_7c_t0_technical_corpus_coverage_audit.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary = {
        key: report[key]
        for key in report
        if key not in {"filter_funnel", "coverage_detail"}
    }
    summary["filter_funnel"] = report["filter_funnel"]["aggregated_by_area"]

    summary_path = OUTPUT_DIR / "phase_7c_t0_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    main()
