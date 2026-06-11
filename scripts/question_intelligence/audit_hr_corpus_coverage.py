# scripts/question_intelligence/audit_hr_corpus_coverage.py

# Phase 7C-B2A — HR Corpus Coverage Audit (read-only).

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"
CORPUS_ROOTS = [
    PROJECT_ROOT / "datasets/curated/hf_import",
    PROJECT_ROOT / "datasets/curated/interview_seed",
    PROJECT_ROOT / "datasets/curated/local_import",
    PROJECT_ROOT / "datasets/curated",
]

HR_AREAS = [
    "hr_analytical",
    "hr_technical_knowledge",
    "hr_brain_teaser",
    "hr_situational",
    "hr_background",
]

ROLE_BUCKETS = [
    "backend",
    "fullstack",
    "frontend",
    "data",
    "devops",
    "qa",
    "mobile",
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

HEALTHY_MIN = 15
WARNING_MIN = 5
CRITICAL_MAX = 4

FRESH_START_TARGET_DIFFICULTY = 3


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
    role_seniority_matrix: dict[str, dict[str, int]]
    source_json_total: int
    indexed_gap: int


@dataclass
class SurvivalCell:
    area: str
    role: str
    seniority: str
    before_filter: int
    after_strict_filter: int
    after_relaxed_filter: int
    survival_pct: float
    risk: str


def _role_bucket(role: str) -> str:
    mapping = {
        "backend_engineer": "backend",
        "fullstack_engineer": "fullstack",
        "frontend_engineer": "frontend",
        "data_engineer": "data",
        "devops_engineer": "devops",
        "qa_engineer": "qa",
        "mobile_engineer": "mobile",
        "ml_engineer": "generic",
        "other": "generic",
    }

    return mapping.get(role, "generic")


def _classify_risk(count: int) -> str:
    if count >= HEALTHY_MIN:
        return "healthy"

    if count >= WARNING_MIN:
        return "warning"

    return "critical"


def _load_source_json_counts() -> dict[str, int]:
    counts: Counter[str] = Counter()

    for root in CORPUS_ROOTS:
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

                if area in HR_AREAS:
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

    for area in HR_AREAS:
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


def _build_area_coverage(
    area: str,
    documents: list[CorpusDocument],
    source_json_counts: dict[str, int],
) -> AreaCoverage:
    area_docs = _documents_for_area(documents, area)

    by_role = Counter(doc.role_bucket for doc in area_docs)
    by_seniority = Counter(doc.seniority for doc in area_docs)

    matrix: dict[str, dict[str, int]] = {
        bucket: {seniority: 0 for seniority in SENIORITIES}
        for bucket in ROLE_BUCKETS
    }

    for doc in area_docs:
        matrix[doc.role_bucket][doc.seniority] = (
            matrix[doc.role_bucket].get(doc.seniority, 0) + 1
        )

    role_counts = {bucket: by_role.get(bucket, 0) for bucket in ROLE_BUCKETS}
    seniority_counts = {level: by_seniority.get(level, 0) for level in SENIORITIES}

    unique_ids = {doc.document_id for doc in area_docs}
    source_total = source_json_counts.get(area, 0)

    return AreaCoverage(
        area=area,
        total_documents=len(area_docs),
        unique_documents=len(unique_ids),
        by_role=role_counts,
        by_seniority=seniority_counts,
        role_seniority_matrix=matrix,
        source_json_total=source_total,
        indexed_gap=max(source_total - len(area_docs), 0),
    )


def _matches_strict_filter(
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

    if min_difficulty is not None and doc.difficulty < min_difficulty:
        return False

    if max_difficulty is not None and doc.difficulty > max_difficulty:
        return False

    return True


def _matches_relaxed_filter(
    doc: CorpusDocument,
    *,
    seniority: str,
    min_difficulty: int | None,
    max_difficulty: int | None,
) -> bool:
    if doc.seniority != seniority:
        return False

    if min_difficulty is not None and doc.difficulty < min_difficulty:
        return False

    if max_difficulty is not None and doc.difficulty > max_difficulty:
        return False

    return True


def _filter_survival(
    area: str,
    documents: list[CorpusDocument],
) -> list[SurvivalCell]:
    area_docs = _documents_for_area(documents, area)
    policy = AdaptiveRetrievalPolicy()

    cells: list[SurvivalCell] = []

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

            stages = policy.build_relaxation_stages(context)
            strict = stages[0]
            relaxed = stages[1]

            before = len(area_docs)

            strict_matches = [
                doc
                for doc in area_docs
                if _matches_strict_filter(
                    doc,
                    role=strict.role or role.value,
                    seniority=strict.seniority or seniority.value,
                    min_difficulty=strict.min_difficulty,
                    max_difficulty=strict.max_difficulty,
                )
            ]

            relaxed_matches = [
                doc
                for doc in area_docs
                if _matches_relaxed_filter(
                    doc,
                    seniority=relaxed.seniority or seniority.value,
                    min_difficulty=relaxed.min_difficulty,
                    max_difficulty=relaxed.max_difficulty,
                )
            ]

            after_strict = len({doc.document_id for doc in strict_matches})
            after_relaxed = len({doc.document_id for doc in relaxed_matches})

            survival_pct = round((after_strict / before) * 100, 1) if before else 0.0

            cells.append(
                SurvivalCell(
                    area=area,
                    role=role.value,
                    seniority=seniority.value,
                    before_filter=before,
                    after_strict_filter=after_strict,
                    after_relaxed_filter=after_relaxed,
                    survival_pct=survival_pct,
                    risk=_classify_risk(after_strict),
                )
            )

    return cells


def _critical_slices(
    coverage: list[AreaCoverage],
    survival: dict[str, list[dict]],
) -> dict[str, list[dict]]:
    critical: dict[str, list[dict]] = {
        "zero_docs_strict_filter": [],
        "one_doc_indexed": [],
        "lte_three_docs_indexed": [],
    }

    for area_cov in coverage:
        for bucket, seniority_counts in area_cov.role_seniority_matrix.items():
            for seniority, count in seniority_counts.items():
                if count == 0:
                    continue

                label = {
                    "area": area_cov.area,
                    "slice": f"{bucket}/{seniority}",
                    "count": count,
                }

                if count <= 3:
                    critical["lte_three_docs_indexed"].append(label)

                if count == 1:
                    critical["one_doc_indexed"].append(label)

        for cell in survival.get(area_cov.area, []):
            if cell["after_strict_filter"] == 0:
                critical["zero_docs_strict_filter"].append(
                    {
                        "area": cell["area"],
                        "slice": f"{cell['role']}/{cell['seniority']}",
                        "count": 0,
                        "before_filter": cell["before_filter"],
                        "after_relaxed_filter": cell["after_relaxed_filter"],
                    }
                )

            if 0 < cell["after_strict_filter"] <= 3:
                critical["lte_three_docs_indexed"].append(
                    {
                        "area": cell["area"],
                        "slice": f"{cell['role']}/{cell['seniority']}",
                        "count": cell["after_strict_filter"],
                        "survival_pct": cell["survival_pct"],
                    }
                )

    return critical


def _expansion_targets(coverage: list[AreaCoverage]) -> list[dict]:
    targets: list[dict] = []

    for area_cov in coverage:
        deficit_to_healthy = max(HEALTHY_MIN - area_cov.unique_documents, 0)

        role_deficits: list[dict] = []

        for bucket in ROLE_BUCKETS:
            for seniority in SENIORITIES:
                current = area_cov.role_seniority_matrix[bucket][seniority]

                if current >= HEALTHY_MIN:
                    continue

                role_deficits.append(
                    {
                        "slice": f"{bucket}/{seniority}",
                        "current": current,
                        "target": HEALTHY_MIN,
                        "add": HEALTHY_MIN - current,
                    }
                )

        targets.append(
            {
                "area": area_cov.area,
                "current_total": area_cov.unique_documents,
                "target_total": max(area_cov.unique_documents, HEALTHY_MIN),
                "documents_to_add_total": deficit_to_healthy,
                "source_json_unindexed": area_cov.indexed_gap,
                "role_seniority_deficits": role_deficits[:12],
            }
        )

    return targets


def _estimate_diversity_gain(coverage: list[AreaCoverage]) -> dict:
    # Phase 7C-A HR: 13 unique / 50 prompts (74% reuse).
    hr_prompts = 50
    current_unique = 13
    current_reuse = 1 - (current_unique / hr_prompts)

    area_weights = {
        "hr_analytical": 10,
        "hr_brain_teaser": 10,
        "hr_technical_knowledge": 10,
        "hr_situational": 10,
        "hr_background": 10,
    }

    weighted_pool = 0.0
    total_weight = sum(area_weights.values())

    for area_cov in coverage:
        weight = area_weights[area_cov.area]
        effective_pool = min(area_cov.unique_documents, HEALTHY_MIN)
        weighted_pool += (weight / total_weight) * effective_pool

    # Approximate unique prompts ≈ sum of min(pool, interviews) with overlap discount.
    interviews = 10
    overlap_discount = 0.65
    projected_unique = min(
        hr_prompts,
        int(weighted_pool * overlap_discount + (hr_prompts - weighted_pool) * 0.15),
    )

    if weighted_pool >= HEALTHY_MIN * len(HR_AREAS) / len(HR_AREAS):
        projected_unique = max(projected_unique, 35)

    expanded_unique = min(
        hr_prompts,
        max(projected_unique, int(current_unique * 2.2)),
    )

    return {
        "baseline_hr_unique_prompts_7c_a": current_unique,
        "baseline_hr_reuse_pct_7c_a": round(current_reuse * 100, 1),
        "current_indexed_hr_pool_weighted_avg": round(weighted_pool, 1),
        "projected_hr_unique_after_expansion": expanded_unique,
        "projected_hr_reuse_after_expansion_pct": round(
            (1 - expanded_unique / hr_prompts) * 100,
            1,
        ),
        "estimated_gain_unique_prompts": expanded_unique - current_unique,
    }


def run_audit() -> dict:
    source_json_counts = _load_source_json_counts()
    documents = _load_chroma_documents()

    coverage = [
        _build_area_coverage(area, documents, source_json_counts)
        for area in HR_AREAS
    ]

    survival: dict[str, list[dict]] = {}

    for area in HR_AREAS:
        cells = _filter_survival(area, documents)
        survival[area] = [asdict(cell) for cell in cells]

    critical = _critical_slices(coverage, survival)
    targets = _expansion_targets(coverage)
    diversity_gain = _estimate_diversity_gain(coverage)

    area_risk_summary = {
        area_cov.area: _classify_risk(area_cov.unique_documents)
        for area_cov in coverage
    }

    return {
        "audit": "Phase 7C-B2A HR Corpus Coverage",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "storage/chroma/interview_corpus (indexed production corpus)",
        "source_json_reference": source_json_counts,
        "coverage_matrix": [asdict(item) for item in coverage],
        "survival_matrix": survival,
        "area_risk_summary": area_risk_summary,
        "critical_slices": critical,
        "expansion_targets": targets,
        "diversity_gain_estimate": diversity_gain,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_audit()

    output_path = OUTPUT_DIR / "phase_7c_b2a_hr_corpus_coverage_audit.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary = {
        key: report[key]
        for key in report
        if key not in {"survival_matrix"}
    }
    summary_path = OUTPUT_DIR / "phase_7c_b2a_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    main()
