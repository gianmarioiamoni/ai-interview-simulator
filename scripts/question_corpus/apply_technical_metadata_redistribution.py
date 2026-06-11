# scripts/question_corpus/apply_technical_metadata_redistribution.py

# Phase 7C-T2B — Apply technical metadata redistribution (T2A validated model).

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = (
    PROJECT_ROOT
    / "scripts/question_intelligence/output/phase_7c_t2b_metadata_redistribution.json"
)

SOURCE_ROOTS = [
    PROJECT_ROOT / "datasets/curated/hf_import",
    PROJECT_ROOT / "datasets/curated/interview_seed",
    PROJECT_ROOT / "datasets/curated/local_import",
]

REDISTRIBUTION_AREAS = {
    "technical_background",
    "technical_technical_knowledge",
}

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

ROLE_MAX_PCT = 20.0
SENIORITY_MAX_PCT = 40.0


def _load_json_files() -> dict[Path, list[dict]]:
    files: dict[Path, list[dict]] = {}

    for root in SOURCE_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*.json"):
            try:
                data = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue

            if isinstance(data, list):
                files[path] = data

    return files


def _distribution(items: list[dict]) -> dict:
    total = len(items)

    role_counts = Counter(
        _role_bucket(str(item.get("role", ""))) for item in items
    )
    seniority_counts = Counter(str(item.get("seniority", "")) for item in items)

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
        "by_role": {bucket: role_counts.get(bucket, 0) for bucket in ROLE_BUCKETS},
        "role_concentration_pct": role_pct,
        "role_flags_over_20pct": [
            bucket for bucket, pct in role_pct.items() if pct > ROLE_MAX_PCT
        ],
        "by_seniority": {
            level: seniority_counts.get(level, 0) for level in ["junior", "mid", "senior"]
        },
        "seniority_concentration_pct": seniority_pct,
        "seniority_flags_over_40pct": [
            level for level, pct in seniority_pct.items() if pct > SENIORITY_MAX_PCT
        ],
    }


def _role_bucket(role: str) -> str:
    from scripts.question_intelligence.audit_technical_metadata_diversity import (
        ROLE_TO_BUCKET,
    )

    return ROLE_TO_BUCKET.get(role, "generic")


def _apply_redistribution() -> dict:
    from scripts.question_intelligence.audit_technical_metadata_diversity import (
        TechDocument,
        _allowed_seniorities,
        _classify_documents,
        _classify_role,
        _classify_seniority,
        _flexibility_score,
        _simulate_optimal_redistribution,
    )

    json_files = _load_json_files()
    before_by_area: dict[str, list[dict]] = {area: [] for area in REDISTRIBUTION_AREAS}
    raw_docs: list[dict] = []
    id_to_location: dict[str, tuple[Path, int]] = {}

    for path, items in json_files.items():
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue

            area = str(item.get("area", ""))

            if area not in REDISTRIBUTION_AREAS:
                continue

            doc_id = str(item.get("id", ""))

            if not doc_id:
                continue

            before_by_area[area].append(
                {
                    "id": doc_id,
                    "role": item.get("role"),
                    "seniority": item.get("seniority"),
                }
            )

            raw_docs.append(
                {
                    "document_id": doc_id,
                    "area": area,
                    "question": str(item.get("question", "")),
                    "role": str(item.get("role", "")),
                    "seniority": str(item.get("seniority", "")),
                    "difficulty": int(item.get("difficulty", 3)),
                }
            )
            id_to_location[doc_id] = (path, index)

    documents = _classify_documents(raw_docs)

    target_docs = [doc for doc in documents if doc.area in REDISTRIBUTION_AREAS]
    _simulate_optimal_redistribution(target_docs)

    changes: list[dict] = []

    for doc in target_docs:
        path, index = id_to_location[doc.document_id]
        item = json_files[path][index]

        old_role = str(item.get("role", ""))
        old_seniority = str(item.get("seniority", ""))

        if old_role == doc.simulated_role and old_seniority == doc.simulated_seniority:
            continue

        item["role"] = doc.simulated_role
        item["seniority"] = doc.simulated_seniority

        changes.append(
            {
                "document_id": doc.document_id,
                "area": doc.area,
                "file": str(path.relative_to(PROJECT_ROOT)),
                "before": {"role": old_role, "seniority": old_seniority},
                "after": {
                    "role": doc.simulated_role,
                    "seniority": doc.simulated_seniority,
                },
                "role_class": doc.role_class,
                "seniority_class": doc.seniority_class,
            }
        )

    modified_files = {str(path.relative_to(PROJECT_ROOT)) for path, _ in id_to_location.values()}

    for path in {loc[0] for loc in id_to_location.values()}:
        path.write_text(json.dumps(json_files[path], indent=4) + "\n")

    after_by_area: dict[str, list[dict]] = {area: [] for area in REDISTRIBUTION_AREAS}

    for path, items in json_files.items():
        for item in items:
            if not isinstance(item, dict):
                continue

            area = str(item.get("area", ""))

            if area not in REDISTRIBUTION_AREAS:
                continue

            after_by_area[area].append(item)

    distribution_after = {
        area: _distribution(after_by_area[area]) for area in sorted(REDISTRIBUTION_AREAS)
    }
    distribution_before = {
        area: _distribution(
            [
                {
                    "role": entry["role"],
                    "seniority": entry.get("seniority", "mid"),
                }
                for entry in before_by_area[area]
            ]
        )
        for area in sorted(REDISTRIBUTION_AREAS)
    }

    return {
        "phase": "7C-T2B Technical Metadata Redistribution",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "areas_modified": sorted(REDISTRIBUTION_AREAS),
        "areas_preserved": ["technical_case_study"],
        "documents_processed": len(target_docs),
        "documents_changed": len(changes),
        "modified_files": sorted(modified_files),
        "distribution_before": distribution_before,
        "distribution_after": distribution_after,
        "changes_sample": changes[:20],
        "all_changes_count_by_area": dict(
            Counter(change["area"] for change in changes)
        ),
    }


def main() -> None:
    report = _apply_redistribution()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))
    print(f"\nReport: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
