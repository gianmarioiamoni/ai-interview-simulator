# scripts/question_intelligence/audit_technical_case_study_t1b_validation.py

# Phase 7C-T1B — Gap closure coverage + diversity re-audit.

from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from infrastructure.llm.llm_adapter import DefaultLLMAdapter
from scripts.question_intelligence import audit_cross_interview_diversity as diversity_audit
from services.question_intelligence.question_intelligence_provider import (
    QuestionIntelligenceProvider,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"

AREA = "technical_case_study"

TECHNICAL_CONFIGS = [
    cfg
    for cfg in diversity_audit.INTERVIEW_CONFIGS
    if cfg[0] == InterviewType.TECHNICAL
]

T1_BASELINE = {
    "indexed_docs": 224,
    "zero_match_cells": 11,
    "case_study_unique": 15,
    "case_study_reuse_pct": 25.0,
    "global_technical_unique": 83,
    "global_technical_reuse_pct": 17.0,
}

GAP_SLICES = [
    ("backend_engineer", "junior"),
    ("frontend_engineer", "junior"),
    ("fullstack_engineer", "junior"),
    ("fullstack_engineer", "senior"),
    ("devops_engineer", "junior"),
    ("data_engineer", "senior"),
    ("qa_engineer", "senior"),
    ("ml_engineer", "senior"),
    ("other", "junior"),
    ("other", "mid"),
    ("other", "senior"),
]


def _load_indexed_case_study() -> list[dict]:
    vectorstore = Chroma(
        collection_name="interview_questions",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=str(PROJECT_ROOT / "storage/chroma/interview_corpus"),
    )

    result = vectorstore._collection.get(
        where={"area": AREA},
        include=["metadatas"],
    )

    items: list[dict] = []

    for metadata in result.get("metadatas") or []:
        if not metadata:
            continue

        items.append(
            {
                "role": str(metadata.get("role", "")),
                "seniority": str(metadata.get("seniority", "")),
                "difficulty": int(metadata.get("difficulty", 3)),
            }
        )

    return items


def _coverage_audit(items: list[dict]) -> dict:
    zero_match = 0
    slice_counts: dict[str, int] = {}

    for role in RoleType:
        for seniority in SeniorityLevel:
            count = sum(
                1
                for item in items
                if item["role"] == role.value
                and item["seniority"] == seniority.value
                and 2 <= item["difficulty"] <= 4
            )
            slice_counts[f"{role.value}/{seniority.value}"] = count

            if count == 0:
                zero_match += 1

    role_counts = Counter(item["role"] for item in items)
    seniority_counts = Counter(item["seniority"] for item in items)

    gap_slice_counts = {
        f"{role}/{seniority}": slice_counts[f"{role}/{seniority}"]
        for role, seniority in GAP_SLICES
    }

    return {
        "indexed_total": len(items),
        "zero_match_cells": zero_match,
        "role_distribution": dict(role_counts),
        "seniority_distribution": dict(seniority_counts),
        "gap_slice_counts": gap_slice_counts,
        "coverage_pass": {
            "zero_match_cells_zero": zero_match == 0,
            "every_role_represented": len(role_counts) >= len(RoleType),
            "every_seniority_represented": len(seniority_counts) >= len(SeniorityLevel),
            "gap_slices_min_gte_4": min(gap_slice_counts.values()) >= 4,
        },
    }


def _diversity_audit() -> dict:
    corpus_by_prompt = diversity_audit._load_corpus_index()
    diversity_audit._instrument_equivalence_band()

    llm = DefaultLLMAdapter()
    provider = QuestionIntelligenceProvider(llm)

    batch_rows: list[diversity_audit.DeliveredQuestion] = []
    failures = 0

    for index, (interview_type, role, level) in enumerate(TECHNICAL_CONFIGS, start=1):
        interview_id = f"t1b-{index:02d}-{uuid.uuid4().hex[:8]}"

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

    case_rows = [row for row in batch_rows if row.area == AREA]
    all_tech = [row for row in batch_rows if row.interview_type == "technical"]

    case_metrics = diversity_audit._global_metrics(case_rows)
    global_metrics = diversity_audit._global_metrics(all_tech)

    return {
        "interviews": len(TECHNICAL_CONFIGS),
        "failures": failures,
        "completion_rate_pct": round(
            (len(TECHNICAL_CONFIGS) - failures) / len(TECHNICAL_CONFIGS) * 100,
            1,
        ),
        "technical_case_study": {
            "total_prompts": case_metrics.total_prompts,
            "unique_prompts": case_metrics.unique_prompts,
            "reuse_pct": case_metrics.reuse_pct,
        },
        "global_technical": {
            "total_prompts": global_metrics.total_prompts,
            "unique_prompts": global_metrics.unique_prompts,
            "reuse_pct": global_metrics.reuse_pct,
        },
        "success_criteria": {
            "case_study_reuse_lte_20": case_metrics.reuse_pct <= 20.0,
            "case_study_unique_gte_16": case_metrics.unique_prompts >= 16,
            "global_reuse_lte_15": global_metrics.reuse_pct <= 15.0,
            "global_unique_gte_85": global_metrics.unique_prompts >= 85,
            "completion_rate_100": failures == 0,
            "failures_zero": failures == 0,
        },
    }


def run_validation(*, skip_diversity: bool = False) -> dict:
    load_dotenv(PROJECT_ROOT / ".env")

    chroma = Chroma(
        collection_name="interview_questions",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=str(PROJECT_ROOT / "storage/chroma/interview_corpus"),
    )

    items = _load_indexed_case_study()
    coverage = _coverage_audit(items)

    report: dict = {
        "audit": "Phase 7C-T1B Validation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "chroma_total_documents": chroma._collection.count(),
        "baseline_t1": T1_BASELINE,
        "coverage": coverage,
    }

    if not skip_diversity:
        diversity = _diversity_audit()
        report["diversity_reaudit"] = diversity
        report["before_after"] = {
            "technical_case_study": {
                "indexed_docs": {
                    "before": T1_BASELINE["indexed_docs"],
                    "after": coverage["indexed_total"],
                },
                "zero_match_cells": {
                    "before": T1_BASELINE["zero_match_cells"],
                    "after": coverage["zero_match_cells"],
                },
                "unique_prompts": {
                    "before": T1_BASELINE["case_study_unique"],
                    "after": diversity["technical_case_study"]["unique_prompts"],
                },
                "reuse_pct": {
                    "before": T1_BASELINE["case_study_reuse_pct"],
                    "after": diversity["technical_case_study"]["reuse_pct"],
                },
            },
            "global_technical": {
                "unique_prompts": {
                    "before": T1_BASELINE["global_technical_unique"],
                    "after": diversity["global_technical"]["unique_prompts"],
                },
                "reuse_pct": {
                    "before": T1_BASELINE["global_technical_reuse_pct"],
                    "after": diversity["global_technical"]["reuse_pct"],
                },
            },
        }
        report["all_success_criteria_pass"] = (
            all(diversity["success_criteria"].values())
            and all(coverage["coverage_pass"].values())
        )

    return report


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_validation()

    output_path = OUTPUT_DIR / "phase_7c_t1b_validation.json"
    output_path.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))
    print(f"\nReport: {output_path}")


if __name__ == "__main__":
    main()
