# scripts/question_intelligence/audit_technical_metadata_t2b_validation.py

# Phase 7C-T2B — Post-redistribution validation (coverage + survival + diversity).

from __future__ import annotations

import json
import uuid
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.seniority_level import SeniorityLevel
from infrastructure.llm.llm_adapter import DefaultLLMAdapter
from scripts.question_intelligence import audit_cross_interview_diversity as diversity_audit
from scripts.question_intelligence.audit_technical_metadata_diversity import (
    AUDIT_ROLES,
    ROLE_BUCKETS,
    ROLE_TO_BUCKET,
    TechDocument,
    _classify_documents,
    _strict_filter_match,
    _survival_matrix,
)
from services.question_intelligence.question_intelligence_provider import (
    QuestionIntelligenceProvider,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"

TARGET_AREAS = [
    "technical_background",
    "technical_technical_knowledge",
]

ROLE_MAX_PCT = 20.0
SENIORITY_MAX_PCT = 40.0

TECHNICAL_CONFIGS = [
    cfg
    for cfg in diversity_audit.INTERVIEW_CONFIGS
    if cfg[0] == InterviewType.TECHNICAL
]

B2D_BASELINE = {
    "technical_background": {"prompts": 20, "unique": 7, "reuse_pct": 65.0},
    "technical_technical_knowledge": {"prompts": 20, "unique": 11, "reuse_pct": 45.0},
    "global_technical_b2d": {
        "prompts": 100,
        "unique": 63,
        "reuse_pct": 37.0,
    },
}


def _load_indexed_documents() -> list[TechDocument]:
    load_dotenv(PROJECT_ROOT / ".env")

    vectorstore = Chroma(
        collection_name="interview_questions",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=str(PROJECT_ROOT / "storage/chroma/interview_corpus"),
    )

    result = vectorstore._collection.get(include=["metadatas", "documents"])
    raw: list[dict] = []

    for metadata, content in zip(
        result.get("metadatas") or [],
        result.get("documents") or [],
    ):
        if not metadata:
            continue

        area = str(metadata.get("area", ""))

        if area not in TARGET_AREAS:
            continue

        raw.append(
            {
                "document_id": str(metadata.get("document_id", "")),
                "area": area,
                "question": content,
                "role": str(metadata.get("role", "")),
                "seniority": str(metadata.get("seniority", "")),
                "difficulty": int(metadata.get("difficulty", 3)),
            }
        )

    documents = _classify_documents(raw)

    for doc, item in zip(documents, raw):
        doc.simulated_role = item["role"]
        doc.simulated_seniority = item["seniority"]

    return documents


def _distribution(documents: list[TechDocument], area: str) -> dict:
    area_docs = [doc for doc in documents if doc.area == area]
    total = len(area_docs)

    role_counts = Counter(ROLE_TO_BUCKET.get(doc.simulated_role, "generic") for doc in area_docs)
    seniority_counts = Counter(doc.simulated_seniority for doc in area_docs)

    role_pct = {
        bucket: round((role_counts.get(bucket, 0) / total) * 100, 1)
        if total
        else 0.0
        for bucket in ROLE_BUCKETS
    }
    seniority_pct = {
        level: round((seniority_counts.get(level, 0) / total) * 100, 1)
        if total
        else 0.0
        for level in ["junior", "mid", "senior"]
    }

    return {
        "total": total,
        "role_concentration_pct": role_pct,
        "role_flags_over_20pct": [
            bucket for bucket, pct in role_pct.items() if pct > ROLE_MAX_PCT
        ],
        "seniority_concentration_pct": seniority_pct,
        "seniority_flags_over_40pct": [
            level for level, pct in seniority_pct.items() if pct > SENIORITY_MAX_PCT
        ],
    }


def _area_survival(documents: list[TechDocument], area: str) -> dict:
    zero_match = 0
    lte_3 = 0
    gte_10 = 0

    for role in AUDIT_ROLES:
        for seniority in SeniorityLevel:
            count = sum(
                1
                for doc in documents
                if _strict_filter_match(
                    doc,
                    role=role.value,
                    seniority=seniority.value,
                    area=area,
                    use_simulated=True,
                )
            )

            if count == 0:
                zero_match += 1
            elif count <= 3:
                lte_3 += 1
            elif count >= 10:
                gte_10 += 1

    return {
        "zero_match_cells": zero_match,
        "lte_3_cells": lte_3,
        "gte_10_cells": gte_10,
        "total_cells": len(AUDIT_ROLES) * len(SeniorityLevel),
    }


def _run_diversity_audit() -> dict:
    load_dotenv()
    corpus_by_prompt = diversity_audit._load_corpus_index()
    diversity_audit._instrument_equivalence_band()

    llm = DefaultLLMAdapter()
    provider = QuestionIntelligenceProvider(llm)

    batch_rows: list[diversity_audit.DeliveredQuestion] = []
    failures = 0

    for index, (interview_type, role, level) in enumerate(TECHNICAL_CONFIGS, start=1):
        interview_id = f"t2b-{index:02d}-{uuid.uuid4().hex[:8]}"

        try:
            questions = diversity_audit._run_batch_interview(
                provider,
                interview_type,
                role,
                level,
            )
        except Exception as exc:
            failures += 1
            print(f"FAILED [{index}]: {exc}", flush=True)
            continue

        batch_rows.extend(
            diversity_audit._collect_delivered(
                interview_id=interview_id,
                path="batch_generate",
                interview_type=interview_type,
                role=role,
                level=level,
                questions=questions,
                corpus_by_prompt=corpus_by_prompt,
            )
        )

    def _area_metrics(area: str) -> dict:
        rows = [row for row in batch_rows if row.area == area]
        metrics = diversity_audit._global_metrics(rows)
        top_share = metrics.top_repeated[0]["reuse_pct"] if metrics.top_repeated else 0.0

        return {
            "total_prompts": metrics.total_prompts,
            "unique_prompts": metrics.unique_prompts,
            "reuse_pct": metrics.reuse_pct,
            "top_prompt_share_pct": top_share,
        }

    area_results = {area: _area_metrics(area) for area in TARGET_AREAS}
    all_tech_rows = [
        row
        for row in batch_rows
        if row.interview_type == "technical"
    ]
    global_metrics = diversity_audit._global_metrics(all_tech_rows)

    return {
        "interviews": len(TECHNICAL_CONFIGS),
        "failures": failures,
        "completion_rate_pct": round(
            (len(TECHNICAL_CONFIGS) - failures) / len(TECHNICAL_CONFIGS) * 100,
            1,
        ),
        "target_areas": {area: area_results[area] for area in TARGET_AREAS},
        "global_technical": {
            "total_prompts": global_metrics.total_prompts,
            "unique_prompts": global_metrics.unique_prompts,
            "reuse_pct": global_metrics.reuse_pct,
        },
        "success_criteria": {
            "technical_background_reuse_lt_15": area_results["technical_background"][
                "reuse_pct"
            ]
            < 15.0,
            "technical_technical_knowledge_reuse_lt_15": area_results[
                "technical_technical_knowledge"
            ]["reuse_pct"]
            < 15.0,
            "global_reuse_lt_20": global_metrics.reuse_pct < 20.0,
            "completion_rate_100": failures == 0,
            "failures_zero": failures == 0,
        },
    }


def run_validation(*, skip_diversity: bool = False) -> dict:
    documents = _load_indexed_documents()

    chroma = Chroma(
        collection_name="interview_questions",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=str(PROJECT_ROOT / "storage/chroma/interview_corpus"),
    )
    indexed_total = chroma._collection.count()

    area_counts = {
        area: sum(1 for doc in documents if doc.area == area) for area in TARGET_AREAS
    }

    coverage = {
        area: _distribution(documents, area) for area in TARGET_AREAS
    }
    survival = {area: _area_survival(documents, area) for area in TARGET_AREAS}

    coverage_pass = all(
        not coverage[area]["role_flags_over_20pct"]
        and not coverage[area]["seniority_flags_over_40pct"]
        for area in TARGET_AREAS
    )

    survival_pass = all(
        survival[area]["zero_match_cells"] == 0 for area in TARGET_AREAS
    )

    report: dict = {
        "audit": "Phase 7C-T2B Validation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "indexed_document_count_total": indexed_total,
        "indexed_area_counts": area_counts,
        "coverage_validation": coverage,
        "coverage_pass": coverage_pass,
        "survival_validation": survival,
        "survival_pass": survival_pass,
        "b2d_baseline": B2D_BASELINE,
    }

    if not skip_diversity:
        diversity = _run_diversity_audit()
        report["diversity_reaudit"] = diversity

        comparison = {}

        for area in TARGET_AREAS:
            before = B2D_BASELINE[area]
            after = diversity["target_areas"][area]
            comparison[area] = {
                "unique_prompts": {
                    "b2d": before["unique"],
                    "t2b": after["unique_prompts"],
                    "delta": after["unique_prompts"] - before["unique"],
                },
                "reuse_pct": {
                    "b2d": before["reuse_pct"],
                    "t2b": after["reuse_pct"],
                    "delta": round(after["reuse_pct"] - before["reuse_pct"], 1),
                },
            }

        comparison["global_technical"] = {
            "unique_prompts": {
                "b2d": B2D_BASELINE["global_technical_b2d"]["unique"],
                "t2b": diversity["global_technical"]["unique_prompts"],
            },
            "reuse_pct": {
                "b2d": B2D_BASELINE["global_technical_b2d"]["reuse_pct"],
                "t2b": diversity["global_technical"]["reuse_pct"],
            },
        }

        report["before_after_comparison"] = comparison
        report["all_success_criteria_pass"] = all(
            diversity["success_criteria"].values()
        ) and coverage_pass and survival_pass

    return report


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_validation()

    output_path = OUTPUT_DIR / "phase_7c_t2b_validation.json"
    output_path.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))
    print(f"\nReport: {output_path}")


if __name__ == "__main__":
    main()
