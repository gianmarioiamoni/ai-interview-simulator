# scripts/question_corpus/build_hr_corpus_expansion.py

# Phase 7C-B2C — HR corpus expansion + metadata diversification (single rebuild cycle).

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BEHAVIORAL_PATH = PROJECT_ROOT / "datasets/curated/local_import/behavioral_interview_questions.json"
AK_INTERVIEW_PATH = PROJECT_ROOT / "datasets/curated/hf_import/ak_interview.json"
BEHAVIORAL_SEED_PATH = PROJECT_ROOT / "datasets/curated/interview_seed/behavioral/behavioral_seed.json"
EXPANSION_PATH = PROJECT_ROOT / "datasets/curated/local_import/hr_corpus_expansion.json"
VALIDATION_PATH = PROJECT_ROOT / "scripts/question_intelligence/output/phase_7c_b2c_validation.json"

HR_AREAS = {
    "hr_analytical",
    "hr_technical_knowledge",
    "hr_brain_teaser",
    "hr_situational",
    "hr_background",
}

ROLES = [
    "backend_engineer",
    "frontend_engineer",
    "fullstack_engineer",
    "data_engineer",
    "devops_engineer",
    "qa_engineer",
    "ml_engineer",
]

SENIORITIES = ["junior", "mid", "senior"]

SENIORITY_DIFFICULTY = {
    "junior": 2,
    "mid": 3,
    "senior": 4,
}

SOURCE = "manual_seed/hr_corpus_expansion_7c_b2c"

# Shared document id collision fix (hr_background vs technical_technical_knowledge).
HR_BACKGROUND_ID_COLLISION_OLD = "a17674f6d0eddb34"
HR_BACKGROUND_ID_NEW = "hr_bg_5yr_career_goal_001"

NEW_QUESTIONS: list[dict] = [
    # hr_analytical (+12)
    {
        "question": "A product metric dropped 15% week-over-week. Walk me through how you would decompose the problem before proposing fixes.",
        "area": "hr_analytical",
        "role": "backend_engineer",
        "seniority": "junior",
        "expected_topics": ["problem_decomposition", "metrics"],
    },
    {
        "question": "You can either refactor a fragile module now or ship a requested feature on deadline. How would you analyze the trade-offs and recommend a path?",
        "area": "hr_analytical",
        "role": "backend_engineer",
        "seniority": "mid",
        "expected_topics": ["trade_offs", "prioritization"],
    },
    {
        "question": "Production latency spiked but error rates stayed flat. Describe your root-cause analysis approach from detection to confirmed cause.",
        "area": "hr_analytical",
        "role": "backend_engineer",
        "seniority": "senior",
        "expected_topics": ["root_cause_analysis", "production"],
    },
    {
        "question": "Your team has ten UI defects and two weeks before release. How would you prioritize which issues to fix first?",
        "area": "hr_analytical",
        "role": "frontend_engineer",
        "seniority": "junior",
        "expected_topics": ["prioritization", "quality"],
    },
    {
        "question": "Stakeholders disagree on whether to optimize for performance or delivery speed. How would you structure the decision?",
        "area": "hr_analytical",
        "role": "frontend_engineer",
        "seniority": "mid",
        "expected_topics": ["decision_making", "trade_offs"],
    },
    {
        "question": "Describe how you would break down an ambiguous customer complaint into testable hypotheses.",
        "area": "hr_analytical",
        "role": "frontend_engineer",
        "seniority": "senior",
        "expected_topics": ["problem_decomposition", "ambiguity"],
    },
    {
        "question": "A nightly ETL job started failing intermittently. Outline the steps you would take to isolate the failure domain.",
        "area": "hr_analytical",
        "role": "data_engineer",
        "seniority": "junior",
        "expected_topics": ["root_cause_analysis", "data_pipelines"],
    },
    {
        "question": "You must choose between batch reprocessing and incremental backfill after a schema change. How do you evaluate the options?",
        "area": "hr_analytical",
        "role": "data_engineer",
        "seniority": "mid",
        "expected_topics": ["trade_offs", "data_quality"],
    },
    {
        "question": "Leadership asks for a single KPI to track data platform health. How would you decide whether that is appropriate and which metric to use?",
        "area": "hr_analytical",
        "role": "data_engineer",
        "seniority": "senior",
        "expected_topics": ["decision_making", "metrics"],
    },
    {
        "question": "Three alerts fire at once during a deployment window. How would you prioritize investigation and communication?",
        "area": "hr_analytical",
        "role": "devops_engineer",
        "seniority": "junior",
        "expected_topics": ["prioritization", "incident_response"],
    },
    {
        "question": "Your team debates blue/green versus rolling deployments for a critical service. How would you compare the operational trade-offs?",
        "area": "hr_analytical",
        "role": "devops_engineer",
        "seniority": "mid",
        "expected_topics": ["trade_offs", "reliability"],
    },
    {
        "question": "Post-incident, how would you distinguish contributing factors from the root cause in your written analysis?",
        "area": "hr_analytical",
        "role": "qa_engineer",
        "seniority": "senior",
        "expected_topics": ["root_cause_analysis", "quality"],
    },
    # hr_technical_knowledge (+11)
    {
        "question": "When would you choose a monolith over microservices for a new product, and what signals would change your decision later?",
        "area": "hr_technical_knowledge",
        "role": "backend_engineer",
        "seniority": "mid",
        "expected_topics": ["architecture", "trade_offs"],
    },
    {
        "question": "Explain how you approach API versioning so clients can evolve without breaking production integrations.",
        "area": "hr_technical_knowledge",
        "role": "backend_engineer",
        "seniority": "senior",
        "expected_topics": ["architecture", "delivery"],
    },
    {
        "question": "How do you balance component reusability with page-specific performance needs in a large frontend codebase?",
        "area": "hr_technical_knowledge",
        "role": "frontend_engineer",
        "seniority": "mid",
        "expected_topics": ["engineering_practices", "quality"],
    },
    {
        "question": "Describe how you design client-side state management for a feature that must stay responsive under slow networks.",
        "area": "hr_technical_knowledge",
        "role": "frontend_engineer",
        "seniority": "senior",
        "expected_topics": ["architecture", "scalability"],
    },
    {
        "question": "What engineering practices do you use to keep fullstack features maintainable across frontend and backend boundaries?",
        "area": "hr_technical_knowledge",
        "role": "fullstack_engineer",
        "seniority": "mid",
        "expected_topics": ["engineering_practices", "delivery"],
    },
    {
        "question": "How would you explain idempotency to a teammate and where would you enforce it in a distributed workflow?",
        "area": "hr_technical_knowledge",
        "role": "fullstack_engineer",
        "seniority": "junior",
        "expected_topics": ["architecture", "quality"],
    },
    {
        "question": "What factors guide your choice between streaming and batch processing for a new analytics use case?",
        "area": "hr_technical_knowledge",
        "role": "data_engineer",
        "seniority": "senior",
        "expected_topics": ["scalability", "architecture"],
    },
    {
        "question": "How do you design data quality checks so they catch issues without blocking legitimate late-arriving data?",
        "area": "hr_technical_knowledge",
        "role": "data_engineer",
        "seniority": "mid",
        "expected_topics": ["quality", "delivery"],
    },
    {
        "question": "Describe the observability signals you would monitor to know a deployment pipeline is healthy over time.",
        "area": "hr_technical_knowledge",
        "role": "devops_engineer",
        "seniority": "senior",
        "expected_topics": ["engineering_practices", "scalability"],
    },
    {
        "question": "How do you decide what belongs in automated tests versus manual exploratory testing before a release?",
        "area": "hr_technical_knowledge",
        "role": "qa_engineer",
        "seniority": "mid",
        "expected_topics": ["quality", "delivery"],
    },
    {
        "question": "What practices help you keep model-serving pipelines reliable when upstream feature data changes frequently?",
        "area": "hr_technical_knowledge",
        "role": "ml_engineer",
        "seniority": "senior",
        "expected_topics": ["scalability", "engineering_practices"],
    },
    # hr_brain_teaser (+8)
    {
        "question": "Estimate how many HTTP requests per second a mid-size API might handle if average latency is 50ms and you run 20 application instances.",
        "area": "hr_brain_teaser",
        "role": "backend_engineer",
        "seniority": "mid",
        "expected_topics": ["estimation", "structured_thinking"],
    },
    {
        "question": "A requirement says the UI must feel instant but the backend needs 2 seconds of processing. How would you reason about the user experience design?",
        "area": "hr_brain_teaser",
        "role": "frontend_engineer",
        "seniority": "junior",
        "expected_topics": ["reasoning", "ambiguity"],
    },
    {
        "question": "You are given a vague goal to improve reliability with no metric defined. What clarifying questions would you ask first?",
        "area": "hr_brain_teaser",
        "role": "devops_engineer",
        "seniority": "senior",
        "expected_topics": ["ambiguity", "structured_thinking"],
    },
    {
        "question": "Roughly how much storage would you expect for one year of application logs if you emit 500 structured events per user session?",
        "area": "hr_brain_teaser",
        "role": "data_engineer",
        "seniority": "mid",
        "expected_topics": ["estimation", "reasoning"],
    },
    {
        "question": "Explain how you would test whether a reported bug is reproducible when the steps from the reporter are incomplete.",
        "area": "hr_brain_teaser",
        "role": "qa_engineer",
        "seniority": "junior",
        "expected_topics": ["structured_thinking", "ambiguity"],
    },
    {
        "question": "If two teammates propose opposite solutions that both seem reasonable, how do you structure a quick evaluation?",
        "area": "hr_brain_teaser",
        "role": "fullstack_engineer",
        "seniority": "senior",
        "expected_topics": ["reasoning", "decision_making"],
    },
    {
        "question": "How would you break down the question 'Is our mobile app fast enough?' into measurable sub-questions?",
        "area": "hr_brain_teaser",
        "role": "frontend_engineer",
        "seniority": "mid",
        "expected_topics": ["structured_thinking", "mobile"],
    },
    {
        "question": "A dataset doubles in size every quarter. What high-level capacity questions would you raise before the next architecture review?",
        "area": "hr_brain_teaser",
        "role": "ml_engineer",
        "seniority": "mid",
        "expected_topics": ["estimation", "scalability"],
    },
]


def _make_id(question: str, area: str) -> str:
    prefix = area.replace("hr_", "hr_")[:4]
    digest = hashlib.sha256(f"{area}|{question.strip().lower()}".encode()).hexdigest()[:12]
    return f"hr_{digest}"


def _to_entry(spec: dict) -> dict:
    question = spec["question"].strip()
    area = spec["area"]
    seniority = spec["seniority"]

    return {
        "id": spec.get("id") or _make_id(question, area),
        "question": question,
        "role": spec["role"],
        "seniority": seniority,
        "area": area,
        "domains": [area],
        "difficulty": spec.get("difficulty", SENIORITY_DIFFICULTY[seniority]),
        "source": spec.get("source", SOURCE),
        "quality_score": 0.85,
        "tags": list(spec.get("tags", [])),
        "expected_topics": list(spec.get("expected_topics", [])),
        "follow_up_hints": [],
    }


def _build_expansion_entries() -> list[dict]:
    return [_to_entry(spec) for spec in NEW_QUESTIONS]


def _diversify_hr_item(
    item: dict,
    *,
    area: str,
    role_index: int,
    seniority_index: int,
) -> dict:
    updated = dict(item)
    updated["role"] = ROLES[role_index % len(ROLES)]
    updated["seniority"] = SENIORITIES[seniority_index % len(SENIORITIES)]
    updated["difficulty"] = SENIORITY_DIFFICULTY[updated["seniority"]]

    if (
        updated.get("area") == "hr_background"
        and updated.get("id") == HR_BACKGROUND_ID_COLLISION_OLD
    ):
        updated["id"] = HR_BACKGROUND_ID_NEW

    return updated


def _apply_diversification_to_file(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        return 0

    area_role_idx: Counter[str] = Counter()
    area_seniority_idx: Counter[str] = Counter()
    updated_count = 0

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        area = item.get("area")

        if area not in HR_AREAS:
            continue

        diversified = _diversify_hr_item(
            item,
            area=str(area),
            role_index=area_role_idx[area],
            seniority_index=area_seniority_idx[area],
        )
        area_role_idx[area] += 1
        area_seniority_idx[area] += 1
        data[index] = diversified
        updated_count += 1

    path.write_text(
        json.dumps(data, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return updated_count


def _load_hr_from_roots() -> list[dict]:
    from services.question_corpus.loaders.folder_corpus_loader import FolderCorpusLoader

    loader = FolderCorpusLoader()
    roots = [
        "datasets/curated/hf_import",
        "datasets/curated/interview_seed",
        "datasets/curated/local_import",
    ]

    items: list[dict] = []

    for root in roots:
        corpus = loader.load(str(PROJECT_ROOT / root))

        for question in corpus.questions:
            if question.area.value not in HR_AREAS:
                continue

            items.append(
                {
                    "id": question.id,
                    "area": question.area.value,
                    "role": question.role.value,
                    "seniority": question.seniority.value,
                    "difficulty": question.difficulty,
                    "question": question.question[:80],
                }
            )

    return items


def _strict_filter_stats(items: list[dict]) -> dict:
    from domain.contracts.user.role import RoleType
    from domain.contracts.user.seniority_level import SeniorityLevel

    roles = list(RoleType)
    seniorities = list(SeniorityLevel)
    zero_profiles = 0
    filled_cells = 0

    for role in roles:
        for seniority in seniorities:
            profile_total = 0

            for area in HR_AREAS:
                count = sum(
                    1
                    for item in items
                    if item["area"] == area
                    and item["role"] == role.value
                    and item["seniority"] == seniority.value
                    and 2 <= int(item.get("difficulty", 3)) <= 4
                )

                if count > 0:
                    filled_cells += 1

                profile_total += count

            if profile_total == 0:
                zero_profiles += 1

    return {
        "zero_match_profiles": zero_profiles,
        "filled_profile_area_cells": filled_cells,
        "total_profile_area_cells": len(roles) * len(seniorities) * len(HR_AREAS),
    }


def _coverage_matrix(items: list[dict]) -> dict[str, dict[str, dict[str, int]]]:
    matrix: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )

    for item in items:
        matrix[item["area"]][item["role"]][item["seniority"]] += 1

    return {
        area: {role: dict(seniorities) for role, seniorities in roles.items()}
        for area, roles in matrix.items()
    }


def _project_diversity(items: list[dict]) -> dict:
    area_totals = Counter(item["area"] for item in items)
    critical_min = min(
        area_totals[area]
        for area in ("hr_analytical", "hr_technical_knowledge", "hr_brain_teaser")
    )

    strict = _strict_filter_stats(items)
    filled_ratio = strict["filled_profile_area_cells"] / strict["total_profile_area_cells"]

    projected_unique = min(50, int(13 + critical_min * 0.9 + filled_ratio * 18))
    projected_reuse = round((1 - projected_unique / 50) * 100, 1)

    return {
        "projected_hr_unique_prompts": projected_unique,
        "projected_hr_reuse_pct": projected_reuse,
        "strict_filter": strict,
    }


def _before_counts() -> dict[str, int]:
    return {
        "hr_analytical": 3,
        "hr_technical_knowledge": 4,
        "hr_brain_teaser": 7,
        "hr_background": 31,
        "hr_situational": 74,
        "total": 119,
    }


def main() -> None:
    expansion_entries = _build_expansion_entries()

    EXPANSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPANSION_PATH.write_text(
        json.dumps(expansion_entries, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    updated = 0
    updated += _apply_diversification_to_file(BEHAVIORAL_PATH)
    updated += _apply_diversification_to_file(AK_INTERVIEW_PATH)
    updated += _apply_diversification_to_file(BEHAVIORAL_SEED_PATH)

    after_items = _load_hr_from_roots()
    after_counts = Counter(item["area"] for item in after_items)

    role_counts = Counter(item["role"] for item in after_items)
    seniority_counts = Counter(item["seniority"] for item in after_items)

    max_role_share = max(role_counts.values()) / len(after_items) if after_items else 0.0
    max_seniority_share = (
        max(seniority_counts.values()) / len(after_items) if after_items else 0.0
    )

    validation = {
        "phase": "7C-B2C",
        "expansion_file": str(EXPANSION_PATH.relative_to(PROJECT_ROOT)),
        "new_questions_written": len(expansion_entries),
        "existing_hr_metadata_updated": updated,
        "corpus_counts": {
            "before": _before_counts(),
            "after": {
                **dict(after_counts),
                "total": len(after_items),
            },
        },
        "coverage_matrix": _coverage_matrix(after_items),
        "role_distribution": dict(role_counts),
        "seniority_distribution": dict(seniority_counts),
        "monoculture_check": {
            "max_role_share_pct": round(max_role_share * 100, 1),
            "max_seniority_share_pct": round(max_seniority_share * 100, 1),
            "passes_no_monoculture": max_role_share <= 0.20 and max_seniority_share <= 0.40,
        },
        "diversity_projection": _project_diversity(after_items),
        "critical_areas_at_least_15": {
            area: after_counts.get(area, 0) >= 15
            for area in (
                "hr_analytical",
                "hr_technical_knowledge",
                "hr_brain_teaser",
            )
        },
    }

    VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_PATH.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(validation, indent=2))
    print(f"\nWrote expansion: {EXPANSION_PATH}")
    print(f"Validation: {VALIDATION_PATH}")


if __name__ == "__main__":
    main()
