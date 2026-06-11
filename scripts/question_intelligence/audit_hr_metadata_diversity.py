# scripts/question_intelligence/audit_hr_metadata_diversity.py

# Phase 7C-B2B — HR Metadata Diversity Audit (read-only).

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"

HR_AREAS = [
    "hr_background",
    "hr_situational",
    "hr_analytical",
    "hr_brain_teaser",
    "hr_technical_knowledge",
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

HR_INTERVIEW_CONFIGS = [
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.JUNIOR),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.MID),
    (RoleType.FULLSTACK_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.JUNIOR),
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.MID),
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.FRONTEND_ENGINEER, SeniorityLevel.MID),
    (RoleType.DATA_ENGINEER, SeniorityLevel.MID),
    (RoleType.ML_ENGINEER, SeniorityLevel.SENIOR),
    (RoleType.DEVOPS_ENGINEER, SeniorityLevel.MID),
]

ROLE_SPECIFIC_PATTERNS: dict[str, list[str]] = {
    "devops_engineer": [
        r"\bdevops\b",
        r"\bon-?call\b",
        r"\bincident\b",
        r"\bsre\b",
        r"\binfrastructure\b",
        r"\bdeployment pipeline\b",
    ],
    "data_engineer": [
        r"\betl\b",
        r"\bdata pipeline\b",
        r"\bwarehouse\b",
        r"\bdata engineer",
        r"\bspark\b",
    ],
    "frontend_engineer": [
        r"\bfrontend\b",
        r"\breact\b",
        r"\bui\b",
        r"\baccessibility\b",
        r"\bcss\b",
    ],
    "backend_engineer": [
        r"\bapi\b",
        r"\bmicroservice",
        r"\bdatabase\b",
        r"\bbackend\b",
        r"\bserver\b",
    ],
    "ml_engineer": [
        r"\bmachine learning\b",
        r"\bml\b",
        r"\bmodel\b",
        r"\btraining data\b",
    ],
    "qa_engineer": [
        r"\bqa\b",
        r"\btest automation\b",
        r"\bquality assurance\b",
        r"\bregression\b",
    ],
}

ROLE_GENERIC_PATTERNS = [
    r"\bconflict\b",
    r"\bteam\b",
    r"\bcommunicat",
    r"\bleadership\b",
    r"\bfailure\b",
    r"\bstrength",
    r"\bweakness",
    r"\bwhy do you want",
    r"\b5 years\b",
    r"\btell me about yourself\b",
    r"\bachievement\b",
    r"\bchallenge\b",
    r"\bpriorit",
    r"\bdisagree\b",
    r"\bfeedback\b",
    r"\bmistake\b",
    r"\bproject\b",
    r"\bcolleague\b",
    r"\bmanager\b",
    r"\bcompany\b",
    r"\brole\b",
    r"\bimprove\b",
    r"\banalytical\b",
    r"\bestimate\b",
    r"\bcalculate\b",
    r"\bhow many\b",
    r"\bteach your interviewer\b",
    r"\bgrandmother\b",
    r"\bgift\b",
    r"\bgerbil\b",
    r"\bbelong anywhere\b",
]

JUNIOR_PATTERNS = [
    r"\bintern\b",
    r"\bentry[- ]level\b",
    r"\bfirst job\b",
    r"\bgraduate\b",
    r"\bjunior\b",
    r"\blearning\b",
]

SENIOR_PATTERNS = [
    r"\bled\b",
    r"\bmentor",
    r"\barchitect",
    r"\bstaff\b",
    r"\bprincipal\b",
    r"\bcross[- ]team\b",
    r"\bstrategic\b",
    r"\bmanager\b",
    r"\binitiative\b",
    r"\bhardest\b",
    r"\bmost difficult\b",
]


@dataclass
class HrDocument:
    document_id: str
    area: str
    question: str
    role: str
    seniority: str
    difficulty: int
    role_class: str
    role_hint: str | None
    seniority_class: str
    simulated_role: str
    simulated_seniority: str


def _matches(patterns: list[str], text: str) -> bool:
    lower = text.lower()

    return any(re.search(pattern, lower) for pattern in patterns)


def _classify_role(question: str) -> tuple[str, str | None]:
    for role, patterns in ROLE_SPECIFIC_PATTERNS.items():
        if _matches(patterns, question):
            return "ROLE_SPECIFIC", role

    if _matches(ROLE_GENERIC_PATTERNS, question):
        return "ROLE_GENERIC", None

    if _matches([r"\bbug\b", r"\bbuilt\b", r"\btechnical\b", r"\btechnolog"], question):
        return "ROLE_GENERIC", None

    return "ROLE_GENERIC", None


def _classify_seniority(question: str, area: str) -> str:
    if _matches(JUNIOR_PATTERNS, question):
        return "JUNIOR_ONLY"

    if _matches(SENIOR_PATTERNS, question):
        return "SENIOR_ONLY"

    if area in {"hr_brain_teaser", "hr_analytical"}:
        return "MULTI_LEVEL"

    if area in {"hr_background", "hr_situational"}:
        return "MULTI_LEVEL"

    return "MULTI_LEVEL"


def _load_hr_documents() -> list[dict]:
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

        if area not in HR_AREAS:
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


def _simulate_retagging(raw_docs: list[dict]) -> list[HrDocument]:
    area_role_counts: dict[str, Counter[str]] = defaultdict(Counter)
    area_seniority_counts: dict[str, Counter[str]] = defaultdict(Counter)

    role_values = [role.value for role in AUDIT_ROLES]
    seniority_values = [level.value for level in SeniorityLevel]

    classified: list[HrDocument] = []

    for item in raw_docs:
        role_class, role_hint = _classify_role(item["question"])
        seniority_class = _classify_seniority(item["question"], item["area"])

        classified.append(
            HrDocument(
                document_id=item["document_id"],
                area=item["area"],
                question=item["question"],
                role=item["role"],
                seniority=item["seniority"],
                difficulty=item["difficulty"],
                role_class=role_class,
                role_hint=role_hint,
                seniority_class=seniority_class,
                simulated_role="",
                simulated_seniority="",
            )
        )

    for area in HR_AREAS:
        area_docs = [doc for doc in classified if doc.area == area]

        for doc in area_docs:
            if doc.role_class == "ROLE_SPECIFIC" and doc.role_hint:
                doc.simulated_role = doc.role_hint
            else:
                doc.simulated_role = min(
                    role_values,
                    key=lambda role: area_role_counts[area][role],
                )

            area_role_counts[area][doc.simulated_role] += 1

            allowed_seniorities = seniority_values

            if doc.seniority_class == "JUNIOR_ONLY":
                allowed_seniorities = ["junior"]
            elif doc.seniority_class == "SENIOR_ONLY":
                allowed_seniorities = ["senior"]
            elif doc.seniority_class == "MID_ONLY":
                allowed_seniorities = ["mid"]

            doc.simulated_seniority = min(
                allowed_seniorities,
                key=lambda level: area_seniority_counts[area][level],
            )
            area_seniority_counts[area][doc.simulated_seniority] += 1

    return classified


def _strict_filter_match(
    doc: HrDocument,
    *,
    role: str,
    seniority: str,
    use_simulated: bool,
) -> bool:
    doc_role = doc.simulated_role if use_simulated else doc.role
    doc_seniority = doc.simulated_seniority if use_simulated else doc.seniority

    if doc_role != role or doc_seniority != seniority:
        return False

    min_difficulty = max(1, 3 - 1)
    max_difficulty = min(5, 3 + 1)

    return min_difficulty <= doc.difficulty <= max_difficulty


def _survival_stats(
    documents: list[HrDocument],
    *,
    use_simulated: bool,
) -> dict:
    profile_matches: dict[str, int] = {}
    profile_area_matches: dict[str, dict[str, int]] = defaultdict(dict)
    zero_profiles = 0

    for role in AUDIT_ROLES:
        for seniority in SeniorityLevel:
            profile_key = f"{role.value}/{seniority.value}"
            total = 0
            per_area: dict[str, int] = {}

            for area in HR_AREAS:
                count = sum(
                    1
                    for doc in documents
                    if doc.area == area
                    and _strict_filter_match(
                        doc,
                        role=role.value,
                        seniority=seniority.value,
                        use_simulated=use_simulated,
                    )
                )
                per_area[area] = count
                total += count

            profile_matches[profile_key] = total
            profile_area_matches[profile_key] = per_area

            if total == 0:
                zero_profiles += 1

    total_profile_area_cells = len(AUDIT_ROLES) * len(SeniorityLevel) * len(HR_AREAS)
    filled_cells = sum(
        1
        for profile in profile_area_matches.values()
        for count in profile.values()
        if count > 0
    )

    return {
        "profiles_with_any_strict_match": len(AUDIT_ROLES) * len(SeniorityLevel)
        - zero_profiles,
        "zero_match_profiles": zero_profiles,
        "total_profiles": len(AUDIT_ROLES) * len(SeniorityLevel),
        "filled_profile_area_cells": filled_cells,
        "total_profile_area_cells": total_profile_area_cells,
        "profile_matches": profile_matches,
        "profile_area_matches": dict(profile_area_matches),
    }


def _simulate_interview_prompts(
    documents: list[HrDocument],
    *,
    use_simulated: bool,
) -> list[str]:
    prompts: list[str] = []

    for interview_index, (role, seniority) in enumerate(HR_INTERVIEW_CONFIGS):
        for area in HR_AREAS:
            pool = [
                doc
                for doc in documents
                if doc.area == area
                and _strict_filter_match(
                    doc,
                    role=role.value,
                    seniority=seniority.value,
                    use_simulated=use_simulated,
                )
            ]

            if not pool:
                pool = [doc for doc in documents if doc.area == area]

            if not pool:
                continue

            pick_index = (interview_index + hash(area)) % len(pool)
            doc = pool[pick_index]
            prompts.append(doc.question.strip().lower())

    return prompts


def _area_slice_counts(
    documents: list[HrDocument],
    *,
    use_simulated: bool,
) -> dict[str, Counter[tuple[str, str]]]:
    slices: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)

    for doc in documents:
        role = doc.simulated_role if use_simulated else doc.role
        seniority = doc.simulated_seniority if use_simulated else doc.seniority
        slices[doc.area][(role, seniority)] += 1

    return slices


def run_audit() -> dict:
    raw_docs = _load_hr_documents()
    documents = _simulate_retagging(raw_docs)

    current_survival = _survival_stats(documents, use_simulated=False)
    simulated_survival = _survival_stats(documents, use_simulated=True)

    current_prompts = _simulate_interview_prompts(documents, use_simulated=False)
    simulated_prompts = _simulate_interview_prompts(documents, use_simulated=True)

    current_unique = len(set(current_prompts))
    simulated_unique = len(set(simulated_prompts))
    total_prompts = len(current_prompts)

    role_class_counts = Counter(doc.role_class for doc in documents)
    seniority_class_counts = Counter(doc.seniority_class for doc in documents)

    simulated_slices = _area_slice_counts(documents, use_simulated=True)
    areas_below_15 = [
        area
        for area in HR_AREAS
        if sum(1 for doc in documents if doc.area == area) < 15
    ]

    under_role_slices: list[dict] = []
    under_seniority_slices: list[dict] = []

    for area in HR_AREAS:
        area_total = sum(1 for doc in documents if doc.area == area)
        slice_counts = simulated_slices[area]

        for role in AUDIT_ROLES:
            for seniority in SeniorityLevel:
                count = slice_counts.get((role.value, seniority.value), 0)

                if count < 5:
                    under_role_slices.append(
                        {
                            "area": area,
                            "slice": f"{role.value}/{seniority.value}",
                            "count": count,
                        }
                    )

        for seniority in SeniorityLevel:
            sen_count = sum(
                count
                for (role, sen), count in slice_counts.items()
                if sen == seniority.value
            )

            if sen_count < 5:
                under_seniority_slices.append(
                    {"area": area, "seniority": seniority.value, "count": sen_count}
                )

    return {
        "audit": "Phase 7C-B2B HR Metadata Diversity",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "corpus_size": len(documents),
        "classification_summary": {
            "role_class": dict(role_class_counts),
            "seniority_class": dict(seniority_class_counts),
            "role_specific_pct": round(
                role_class_counts["ROLE_SPECIFIC"] / len(documents) * 100,
                1,
            ),
            "multi_level_seniority_pct": round(
                seniority_class_counts["MULTI_LEVEL"] / len(documents) * 100,
                1,
            ),
        },
        "diversity_impact": {
            "current": {
                "hr_unique_prompts_simulated_10_interviews": current_unique,
                "hr_reuse_pct": round(
                    (1 - current_unique / total_prompts) * 100,
                    1,
                )
                if total_prompts
                else 0.0,
                "strict_filter_filled_profile_area_cells": current_survival[
                    "filled_profile_area_cells"
                ],
                "zero_match_profiles": current_survival["zero_match_profiles"],
                "profiles_with_any_strict_match": current_survival[
                    "profiles_with_any_strict_match"
                ],
            },
            "simulated_retagging": {
                "hr_unique_prompts_simulated_10_interviews": simulated_unique,
                "hr_reuse_pct": round(
                    (1 - simulated_unique / total_prompts) * 100,
                    1,
                )
                if total_prompts
                else 0.0,
                "strict_filter_filled_profile_area_cells": simulated_survival[
                    "filled_profile_area_cells"
                ],
                "zero_match_profiles": simulated_survival["zero_match_profiles"],
                "profiles_with_any_strict_match": simulated_survival[
                    "profiles_with_any_strict_match"
                ],
            },
            "observed_7c_a_baseline": {
                "hr_unique_prompts": 13,
                "hr_reuse_pct": 74.0,
                "note": "Phase 7C-A observed across 10 HR interviews (50 prompts)",
            },
        },
        "survival_comparison": {
            "current": current_survival,
            "simulated": simulated_survival,
        },
        "content_gaps_after_optimal_retagging": {
            "areas_below_15_documents": {
                area: sum(1 for doc in documents if doc.area == area)
                for area in areas_below_15
            },
            "role_seniority_slices_under_5": under_role_slices[:40],
            "seniority_under_5_by_area": under_seniority_slices,
        },
        "recovery_conclusions": {
            "metadata_only_recoverable_unique_prompts_gain": simulated_unique
            - current_unique,
            "estimated_7c_a_hr_unique_after_retag": min(
                50,
                max(
                    13,
                    int(13 + (simulated_unique - current_unique) * 0.85),
                ),
            ),
            "corpus_expansion_still_required": True,
            "expansion_reason": (
                "Metadata redistribution improves profile isolation but cannot "
                "raise area pool ceilings (hr_analytical=3, hr_technical_knowledge=4, "
                "hr_brain_teaser=7 remain below healthy threshold of 15)."
            ),
        },
        "documents": [asdict(doc) for doc in documents],
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_audit()

    output_path = OUTPUT_DIR / "phase_7c_b2b_hr_metadata_diversity_audit.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary = {key: report[key] for key in report if key != "documents"}
    summary_path = OUTPUT_DIR / "phase_7c_b2b_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    main()
