# scripts/question_intelligence/audit_technical_metadata_diversity.py

# Phase 7C-T2A — Technical Metadata Diversity Audit (read-only).

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"

TECH_AREAS = [
    "technical_background",
    "technical_technical_knowledge",
    "technical_case_study",
]

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

ROLE_VALUES = [role.value for role in AUDIT_ROLES]
SENIORITY_VALUES = [level.value for level in SeniorityLevel]

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

CONCENTRATION_FLAG_PCT = 40.0
FRESH_START_MIN_DIFFICULTY = 2
FRESH_START_MAX_DIFFICULTY = 4

TECH_INTERVIEW_CONFIGS = [
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.MID),
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.JUNIOR),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.MID),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.JUNIOR),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.FRONTEND_ENGINEER, SeniorityLevel.MID),
    (RoleType.FRONTEND_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.DATA_ENGINEER, SeniorityLevel.MID),
    (RoleType.DATA_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.ML_ENGINEER, SeniorityLevel.MID),
    (RoleType.ML_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.DEVOPS_ENGINEER, SeniorityLevel.MID),
    (RoleType.DEVOPS_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.QA_ENGINEER, SeniorityLevel.MID),
    (RoleType.QA_ENGINEER, SeniorityLevel.JUNIOR),
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.MID),
    (RoleType.DATA_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.MID),
    (RoleType.ML_ENGINEER, SeniorityLevel.JUNIOR),
]

B2D_OBSERVED = {
    "technical_background": {"prompts": 20, "unique": 7, "reuse_pct": 65.0},
    "technical_technical_knowledge": {"prompts": 20, "unique": 11, "reuse_pct": 45.0},
    "technical_case_study": {"prompts": 20, "unique": 13, "reuse_pct": 35.0},
}

ROLE_SPECIFIC_PATTERNS: dict[str, list[str]] = {
    "backend_engineer": [
        r"\bbackend\b",
        r"\bapi\b",
        r"\bmicroservice",
        r"\bdatabase\b",
        r"\bserver\b",
        r"\brest\b",
        r"\bsql\b",
        r"\bkafka\b",
        r"\bcache\b",
        r"\bredis\b",
    ],
    "frontend_engineer": [
        r"\bfrontend\b",
        r"\breact\b",
        r"\bui\b",
        r"\baccessibility\b",
        r"\bcss\b",
        r"\bbrowser\b",
        r"\bdom\b",
    ],
    "fullstack_engineer": [
        r"\bfull[- ]stack\b",
        r"\bend[- ]to[- ]end\b",
    ],
    "data_engineer": [
        r"\betl\b",
        r"\bdata pipeline\b",
        r"\bwarehouse\b",
        r"\bdata engineer",
        r"\bspark\b",
        r"\bairflow\b",
    ],
    "devops_engineer": [
        r"\bdevops\b",
        r"\bon-?call\b",
        r"\bincident\b",
        r"\bsre\b",
        r"\binfrastructure\b",
        r"\bkubernetes\b",
        r"\bci/?cd\b",
        r"\bdeployment pipeline\b",
    ],
    "qa_engineer": [
        r"\bqa\b",
        r"\btest automation\b",
        r"\bquality assurance\b",
        r"\bregression\b",
        r"\bunit test",
    ],
    "ml_engineer": [
        r"\bmachine learning\b",
        r"\bml engineer",
        r"\bmodel training\b",
        r"\bneural network\b",
        r"\bfeature store\b",
    ],
}

ROLE_GENERIC_PATTERNS = [
    r"\bwhy do you want\b",
    r"\btell me about yourself\b",
    r"\b5 years\b",
    r"\bcurrent/last company\b",
    r"\bleave your\b",
    r"\bproject you\b",
    r"\bchallenge you\b",
    r"\bteam you\b",
    r"\bworked on\b",
    r"\bexperience with\b",
    r"\bfavorite\b",
    r"\bhobby\b",
    r"\bstrength",
    r"\bweakness",
]

TECH_GENERIC_PATTERNS = [
    r"\boop\b",
    r"\bobject[- ]oriented\b",
    r"\bexplain\b.+\bconcept",
    r"\bwhat is\b",
    r"\bdifference between\b",
    r"\bhow does\b.+\bwork\b",
    r"\bprogramming language\b",
    r"\bversion control\b",
    r"\bgit\b",
    r"\bagile\b",
]

JUNIOR_PATTERNS = [
    r"\bintern\b",
    r"\bentry[- ]level\b",
    r"\bfirst job\b",
    r"\bgraduate\b",
    r"\bjunior\b",
    r"\blearning curve\b",
]

MID_PATTERNS = [
    r"\bmid[- ]level\b",
    r"\b2[- ]3 years\b",
    r"\b3[- ]5 years\b",
]

SENIOR_PATTERNS = [
    r"\bled\b",
    r"\bmentor",
    r"\barchitect",
    r"\bstaff\b",
    r"\bprincipal\b",
    r"\bcross[- ]team\b",
    r"\bstrategic\b",
    r"\bscale to\b",
    r"\bdesign a\b.+\bsystem\b",
    r"\bhigh availability\b",
    r"\bdistributed system\b",
    r"\btrade[- ]off",
    r"\bproduction incident\b",
]

ROLE_TO_BUCKET = {
    "backend_engineer": "backend",
    "fullstack_engineer": "fullstack",
    "frontend_engineer": "frontend",
    "data_engineer": "data",
    "devops_engineer": "devops",
    "qa_engineer": "qa",
    "ml_engineer": "ml",
    "other": "generic",
}


@dataclass
class TechDocument:
    document_id: str
    area: str
    question: str
    role: str
    seniority: str
    difficulty: int
    role_class: str
    compatible_roles: list[str]
    seniority_class: str
    simulated_role: str = ""
    simulated_seniority: str = ""
    flexibility_score: int = 0


def _matches(patterns: list[str], text: str) -> bool:
    lower = text.lower()
    return any(re.search(pattern, lower) for pattern in patterns)


def _matched_roles(question: str) -> list[str]:
    matched = [
        role
        for role, patterns in ROLE_SPECIFIC_PATTERNS.items()
        if _matches(patterns, question)
    ]
    return matched


def _classify_role(question: str, area: str) -> tuple[str, list[str]]:
    matched = _matched_roles(question)

    if len(matched) == 1:
        return "ROLE_SPECIFIC", matched

    if len(matched) >= 2:
        return "ROLE_MULTI_ROLE", matched

    if _matches(ROLE_GENERIC_PATTERNS, question):
        return "ROLE_GENERIC", list(ROLE_VALUES)

    if area == "technical_background" and not _matches(
        TECH_GENERIC_PATTERNS + list(sum(ROLE_SPECIFIC_PATTERNS.values(), [])),
        question,
    ):
        return "ROLE_GENERIC", list(ROLE_VALUES)

    if _matches(TECH_GENERIC_PATTERNS, question):
        if area == "technical_case_study":
            return "ROLE_MULTI_ROLE", ["backend_engineer", "fullstack_engineer"]
        return "ROLE_GENERIC", list(ROLE_VALUES)

    if area == "technical_case_study":
        return "ROLE_MULTI_ROLE", [
            "backend_engineer",
            "fullstack_engineer",
            "devops_engineer",
        ]

    return "ROLE_GENERIC", list(ROLE_VALUES)


def _classify_seniority(question: str, area: str) -> str:
    if _matches(JUNIOR_PATTERNS, question):
        return "JUNIOR_ONLY"

    if _matches(SENIOR_PATTERNS, question):
        return "SENIOR_ONLY"

    if _matches(MID_PATTERNS, question):
        return "MID_ONLY"

    if area == "technical_case_study":
        if _matches(
            [
                r"\bdesign\b",
                r"\barchitect",
                r"\bscale\b",
                r"\bmillion\b",
                r"\bavailability\b",
            ],
            question,
        ):
            return "SENIOR_ONLY"

        return "MULTI_LEVEL"

    if area == "technical_background":
        return "MULTI_LEVEL"

    return "MULTI_LEVEL"


def _allowed_seniorities(seniority_class: str) -> list[str]:
    if seniority_class == "JUNIOR_ONLY":
        return ["junior"]

    if seniority_class == "MID_ONLY":
        return ["mid"]

    if seniority_class == "SENIOR_ONLY":
        return ["senior"]

    return list(SENIORITY_VALUES)


def _flexibility_score(doc: TechDocument) -> int:
    role_flex = {
        "ROLE_SPECIFIC": 0,
        "ROLE_MULTI_ROLE": len(doc.compatible_roles),
        "ROLE_GENERIC": len(ROLE_VALUES),
    }[doc.role_class]

    seniority_flex = len(_allowed_seniorities(doc.seniority_class))
    return role_flex + seniority_flex


def _load_technical_documents() -> list[dict]:
    load_dotenv(PROJECT_ROOT / ".env")

    vectorstore = Chroma(
        collection_name="interview_questions",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=str(PROJECT_ROOT / "storage/chroma/interview_corpus"),
    )

    result = vectorstore._collection.get(include=["metadatas", "documents"])
    documents: list[dict] = []

    for metadata, content in zip(
        result.get("metadatas") or [],
        result.get("documents") or [],
    ):
        if not metadata:
            continue

        area = str(metadata.get("area", ""))

        if area not in TECH_AREAS:
            continue

        documents.append(
            {
                "document_id": str(metadata.get("document_id", "")),
                "area": area,
                "question": content,
                "role": str(metadata.get("role", "")),
                "seniority": str(metadata.get("seniority", "")),
                "difficulty": int(metadata.get("difficulty", 3)),
            }
        )

    return documents


def _classify_documents(raw_docs: list[dict]) -> list[TechDocument]:
    classified: list[TechDocument] = []

    for item in raw_docs:
        role_class, compatible_roles = _classify_role(item["question"], item["area"])
        seniority_class = _classify_seniority(item["question"], item["area"])

        doc = TechDocument(
            document_id=item["document_id"],
            area=item["area"],
            question=item["question"],
            role=item["role"],
            seniority=item["seniority"],
            difficulty=item["difficulty"],
            role_class=role_class,
            compatible_roles=compatible_roles,
            seniority_class=seniority_class,
        )
        doc.flexibility_score = _flexibility_score(doc)
        classified.append(doc)

    return classified


def _simulate_optimal_redistribution(documents: list[TechDocument]) -> None:
    slice_counts: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)

    for area in TECH_AREAS:
        area_docs = sorted(
            [doc for doc in documents if doc.area == area],
            key=lambda doc: doc.flexibility_score,
        )

        for doc in area_docs:
            if doc.role_class == "ROLE_SPECIFIC":
                allowed_roles = doc.compatible_roles
            else:
                allowed_roles = doc.compatible_roles

            allowed_seniorities = _allowed_seniorities(doc.seniority_class)

            best_role = ""
            best_seniority = ""
            best_count = 10**9

            for role in allowed_roles:
                for seniority in allowed_seniorities:
                    count = slice_counts[area][(role, seniority)]

                    if count < best_count:
                        best_count = count
                        best_role = role
                        best_seniority = seniority

            doc.simulated_role = best_role
            doc.simulated_seniority = best_seniority
            slice_counts[area][(best_role, best_seniority)] += 1


def _role_bucket(role: str) -> str:
    return ROLE_TO_BUCKET.get(role, "generic")


def _distribution_by_bucket(documents: list[TechDocument], *, simulated: bool) -> dict:
    by_area: dict[str, dict] = {}

    for area in TECH_AREAS:
        area_docs = [doc for doc in documents if doc.area == area]
        total = len(area_docs)

        role_counts = Counter(
            _role_bucket(doc.simulated_role if simulated else doc.role)
            for doc in area_docs
        )
        seniority_counts = Counter(
            doc.simulated_seniority if simulated else doc.seniority for doc in area_docs
        )

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
            for level in SENIORITY_VALUES
        }

        by_area[area] = {
            "total": total,
            "by_role": {bucket: role_counts.get(bucket, 0) for bucket in ROLE_BUCKETS},
            "role_concentration_pct": role_pct,
            "role_flags_over_40pct": [
                bucket for bucket, pct in role_pct.items() if pct > CONCENTRATION_FLAG_PCT
            ],
            "by_seniority": {
                level: seniority_counts.get(level, 0) for level in SENIORITY_VALUES
            },
            "seniority_concentration_pct": seniority_pct,
            "seniority_flags_over_40pct": [
                level
                for level, pct in seniority_pct.items()
                if pct > CONCENTRATION_FLAG_PCT
            ],
        }

    return by_area


def _strict_filter_match(
    doc: TechDocument,
    *,
    role: str,
    seniority: str,
    area: str,
    use_simulated: bool,
) -> bool:
    if doc.area != area:
        return False

    doc_role = doc.simulated_role if use_simulated else doc.role
    doc_seniority = doc.simulated_seniority if use_simulated else doc.seniority

    if doc_role != role or doc_seniority != seniority:
        return False

    return FRESH_START_MIN_DIFFICULTY <= doc.difficulty <= FRESH_START_MAX_DIFFICULTY


def _survival_matrix(documents: list[TechDocument], *, use_simulated: bool) -> dict:
    cells: list[dict] = []
    bucket_summary: Counter[str] = Counter()

    for area in TECH_AREAS:
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
                        use_simulated=use_simulated,
                    )
                )

                if count == 0:
                    bucket = "zero_match"
                elif count <= 3:
                    bucket = "lte_3"
                elif count >= 10:
                    bucket = "gte_10"
                else:
                    bucket = "mid_4_9"

                bucket_summary[bucket] += 1
                cells.append(
                    {
                        "area": area,
                        "role": role.value,
                        "seniority": seniority.value,
                        "strict_count": count,
                        "bucket": bucket,
                    }
                )

    return {
        "cells": cells,
        "summary": dict(bucket_summary),
        "total_cells": len(cells),
    }


def _area_pool_sizes(
    documents: list[TechDocument],
    *,
    use_simulated: bool,
) -> dict[str, dict[str, int]]:
    pools: dict[str, dict[str, int]] = {}

    for area in TECH_AREAS:
        profile_pools: dict[str, int] = {}

        for role in AUDIT_ROLES:
            for seniority in SeniorityLevel:
                key = f"{role.value}/{seniority.value}"
                profile_pools[key] = sum(
                    1
                    for doc in documents
                    if _strict_filter_match(
                        doc,
                        role=role.value,
                        seniority=seniority.value,
                        area=area,
                        use_simulated=use_simulated,
                    )
                )

        pools[area] = profile_pools

    return pools


def _simulate_interview_prompts(
    documents: list[TechDocument],
    *,
    use_simulated: bool,
) -> tuple[list[str], dict[str, list[str]]]:
    prompts: list[str] = []
    by_area: dict[str, list[str]] = {area: [] for area in TECH_AREAS}

    for interview_index, (role, seniority) in enumerate(TECH_INTERVIEW_CONFIGS):
        for area in TECH_AREAS:
            pool = [
                doc
                for doc in documents
                if _strict_filter_match(
                    doc,
                    role=role.value,
                    seniority=seniority.value,
                    area=area,
                    use_simulated=use_simulated,
                )
            ]

            if not pool:
                continue

            pick_index = (interview_index + hash(area)) % len(pool)
            normalized = pool[pick_index].question.strip().lower()
            prompts.append(normalized)
            by_area[area].append(normalized)

    return prompts, by_area


def _estimate_unique_from_pools(
    area_pools: dict[str, dict[str, int]],
    interview_configs: list[tuple[RoleType, SeniorityLevel]],
    *,
    overlap_discount: float = 0.72,
) -> dict[str, int]:
    estimates: dict[str, int] = {}

    for area in TECH_AREAS:
        picks: list[int] = []

        for role, seniority in interview_configs:
            pool_size = area_pools[area].get(f"{role.value}/{seniority.value}", 0)

            if pool_size == 0:
                picks.append(0)
            else:
                picks.append(min(pool_size, 5))

        non_zero = [size for size in picks if size > 0]
        interviews_with_pool = len(non_zero)

        if interviews_with_pool == 0:
            estimates[area] = 1
            continue

        avg_pool = sum(non_zero) / len(non_zero)
        projected = int(
            min(
                len(interview_configs),
                avg_pool * overlap_discount * interviews_with_pool * 0.35
                + interviews_with_pool * 0.4,
            )
        )
        estimates[area] = max(1, projected)

    return estimates


def _classification_by_area(documents: list[TechDocument]) -> dict:
    matrix: dict[str, dict] = {}

    for area in TECH_AREAS:
        area_docs = [doc for doc in documents if doc.area == area]
        total = len(area_docs)

        role_class = Counter(doc.role_class for doc in area_docs)
        seniority_class = Counter(doc.seniority_class for doc in area_docs)

        matrix[area] = {
            "total_documents": total,
            "role_suitability": {
                label: {
                    "count": role_class.get(label, 0),
                    "pct": round(role_class.get(label, 0) / total * 100, 1)
                    if total
                    else 0.0,
                }
                for label in [
                    "ROLE_SPECIFIC",
                    "ROLE_MULTI_ROLE",
                    "ROLE_GENERIC",
                ]
            },
            "seniority_suitability": {
                label: {
                    "count": seniority_class.get(label, 0),
                    "pct": round(seniority_class.get(label, 0) / total * 100, 1)
                    if total
                    else 0.0,
                }
                for label in [
                    "JUNIOR_ONLY",
                    "MID_ONLY",
                    "SENIOR_ONLY",
                    "MULTI_LEVEL",
                ]
            },
        }

    return matrix


def _redistribution_summary(documents: list[TechDocument]) -> dict:
    summary: dict[str, dict] = {}

    for area in TECH_AREAS:
        area_docs = [doc for doc in documents if doc.area == area]
        reassigned = sum(
            1
            for doc in area_docs
            if doc.simulated_role != doc.role or doc.simulated_seniority != doc.seniority
        )

        slice_counts = Counter(
            (doc.simulated_role, doc.simulated_seniority) for doc in area_docs
        )
        min_slice = min(slice_counts.values()) if slice_counts else 0
        max_slice = max(slice_counts.values()) if slice_counts else 0
        zero_slices = sum(1 for count in slice_counts.values() if count == 0)

        all_slices = len(AUDIT_ROLES) * len(SeniorityLevel)
        filled_slices = len(slice_counts)

        summary[area] = {
            "documents_reassigned": reassigned,
            "reassignment_pct": round(reassigned / len(area_docs) * 100, 1)
            if area_docs
            else 0.0,
            "filled_role_seniority_slices": filled_slices,
            "total_role_seniority_slices": all_slices,
            "min_slice_count": min_slice,
            "max_slice_count": max_slice,
            "empty_slices_remaining": all_slices - filled_slices,
        }

    return summary


def run_audit() -> dict:
    raw_docs = _load_technical_documents()
    documents = _classify_documents(raw_docs)
    _simulate_optimal_redistribution(documents)

    current_distribution = _distribution_by_bucket(documents, simulated=False)
    simulated_distribution = _distribution_by_bucket(documents, simulated=True)

    current_survival = _survival_matrix(documents, use_simulated=False)
    simulated_survival = _survival_matrix(documents, use_simulated=True)

    current_prompts, current_by_area = _simulate_interview_prompts(
        documents,
        use_simulated=False,
    )
    simulated_prompts, simulated_by_area = _simulate_interview_prompts(
        documents,
        use_simulated=True,
    )

    current_pools = _area_pool_sizes(documents, use_simulated=False)
    simulated_pools = _area_pool_sizes(documents, use_simulated=True)

    current_area_unique = {
        area: len(set(prompts)) for area, prompts in current_by_area.items()
    }
    simulated_area_unique = {
        area: len(set(prompts)) for area, prompts in simulated_by_area.items()
    }

    current_total_unique = len(set(current_prompts))
    simulated_total_unique = len(set(simulated_prompts))
    total_prompts = len(current_prompts)

    pool_estimates = _estimate_unique_from_pools(
        simulated_pools,
        TECH_INTERVIEW_CONFIGS,
    )

    global_reuse_current = round(
        (1 - current_total_unique / total_prompts) * 100,
        1,
    ) if total_prompts else 0.0

    global_reuse_simulated = round(
        (1 - simulated_total_unique / total_prompts) * 100,
        1,
    ) if total_prompts else 0.0

    area_projection: dict[str, dict] = {}

    for area in TECH_AREAS:
        baseline = B2D_OBSERVED[area]
        prompts_in_area = len(current_by_area[area])
        sim_prompts_in_area = len(simulated_by_area[area])

        current_unique = current_area_unique.get(area, 0)
        simulated_unique = simulated_area_unique.get(area, 0)

        if sim_prompts_in_area:
            sim_reuse = round(
                (1 - simulated_unique / sim_prompts_in_area) * 100,
                1,
            )
        else:
            sim_reuse = 100.0

        pool_estimate = pool_estimates[area]

        area_projection[area] = {
            "b2d_observed_unique": baseline["unique"],
            "b2d_observed_reuse_pct": baseline["reuse_pct"],
            "simulated_interview_unique_current": current_unique,
            "simulated_interview_unique_after_retag": simulated_unique,
            "simulated_interview_reuse_after_retag_pct": sim_reuse,
            "pool_based_unique_estimate": pool_estimate,
            "meets_reuse_lt_35": sim_reuse < 35.0,
            "meets_unique_gt_70pct_of_prompts": simulated_unique
            > sim_prompts_in_area * 0.7
            if sim_prompts_in_area
            else False,
        }

    global_unique_target = 70
    global_reuse_target = 35.0

    metadata_sufficient = (
        global_reuse_simulated < global_reuse_target
        and simulated_total_unique > global_unique_target
    )

    remaining_zero = simulated_survival["summary"].get("zero_match", 0)
    remaining_lte3 = simulated_survival["summary"].get("lte_3", 0)

    corpus_still_required = (
        not metadata_sufficient
        or remaining_zero > 0
        or remaining_lte3 > 20
    )

    return {
        "audit": "Phase 7C-T2A Technical Metadata Diversity",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "corpus_size": len(documents),
        "metadata_suitability_matrix": _classification_by_area(documents),
        "current_metadata_constraints": current_distribution,
        "simulated_metadata_constraints": simulated_distribution,
        "redistribution_simulation": _redistribution_summary(documents),
        "survival_comparison": {
            "current": current_survival["summary"],
            "simulated": simulated_survival["summary"],
            "table": {
                "zero_match_cells": {
                    "current": current_survival["summary"].get("zero_match", 0),
                    "simulated": simulated_survival["summary"].get("zero_match", 0),
                },
                "lte_3_doc_cells": {
                    "current": current_survival["summary"].get("lte_3", 0),
                    "simulated": simulated_survival["summary"].get("lte_3", 0),
                },
                "gte_10_doc_cells": {
                    "current": current_survival["summary"].get("gte_10", 0),
                    "simulated": simulated_survival["summary"].get("gte_10", 0),
                },
            },
        },
        "diversity_projection": {
            "interview_simulation": {
                "configs": len(TECH_INTERVIEW_CONFIGS),
                "total_prompts_simulated": total_prompts,
                "current_unique_prompts": current_total_unique,
                "simulated_unique_prompts": simulated_total_unique,
                "current_reuse_pct": global_reuse_current,
                "simulated_reuse_pct": global_reuse_simulated,
                "unique_gain": simulated_total_unique - current_total_unique,
            },
            "by_area": area_projection,
            "targets": {
                "reuse_lt_35_pct": global_reuse_target,
                "unique_prompts_gt_70": global_unique_target,
            },
            "targets_met_after_retag": metadata_sufficient,
        },
        "recommendation": {
            "targeted_corpus_authoring_still_required": corpus_still_required,
            "answer": (
                "Yes — targeted corpus authoring is still required after optimal "
                "metadata redistribution."
                if corpus_still_required
                else "No — metadata redistribution alone is sufficient."
            ),
            "primary_reason": (
                "Simulated retagging cannot eliminate zero-match cells or raise "
                "per-profile strict pools enough to reach reuse <35% and unique >70."
                if corpus_still_required
                else "Optimal redistribution fills all profile-area cells adequately."
            ),
            "suggested_next_phase": (
                "Phase 7C-T1 — Targeted Technical Corpus Expansion"
                if corpus_still_required
                else "Phase 7C-T3 — Re-Audit only"
            ),
        },
        "documents": [asdict(doc) for doc in documents],
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_audit()

    output_path = OUTPUT_DIR / "phase_7c_t2a_technical_metadata_diversity_audit.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary = {key: report[key] for key in report if key != "documents"}
    summary_path = OUTPUT_DIR / "phase_7c_t2a_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    main()
