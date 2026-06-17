# scripts/question_intelligence/audit_sql_diversity_wave1.py
# Measures real SQL interview diversity after Wave1 expansion.
# Generates 30 technical_database interviews and reports diversity metrics.

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from infrastructure.llm.llm_adapter import DefaultLLMAdapter
from services.question_intelligence.question_intelligence_provider import (
    QuestionIntelligenceProvider,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORPUS_ROOTS = [
    PROJECT_ROOT / "datasets/curated/hf_import",
    PROJECT_ROOT / "datasets/curated/interview_seed",
    PROJECT_ROOT / "datasets/curated/local_import",
    PROJECT_ROOT / "datasets/curated",
]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"
INTERVIEW_COUNT = 30

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
    (RoleType.BACKEND_ENGINEER, SeniorityLevel.MID),
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _load_corpus_index() -> tuple[dict[str, dict], dict[str, list[str]]]:
    """Returns (prompt_index, source_to_domains).

    prompt_index: normalized_prompt -> corpus metadata
    source_to_domains: source_name -> aggregated unique domains
    """
    index: dict[str, dict] = {}
    source_domains: dict[str, set[str]] = {}

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
                q_text = item.get("question", "")
                source = str(item.get("source", ""))
                area = str(item.get("area", ""))
                domains = item.get("domains", [])
                if not q_text:
                    continue
                entry = {
                    "id": str(item.get("id", "")),
                    "source": source,
                    "domains": domains,
                    "difficulty": item.get("difficulty", 0),
                }
                index[_normalize(str(q_text))] = entry
                # Only aggregate domains from technical_database area questions
                if source and area == "technical_database":
                    # Filter to meaningful SQL sub-domains (not area names)
                    sql_domains = [
                        d for d in domains
                        if d not in {
                            "technical_database", "technical_coding",
                            "technical_background", "technical_case_study",
                            "technical_technical_knowledge", "hr_situational",
                            "hr_background", "hr_brain_teaser", "hr_analytical",
                        }
                    ]
                    source_domains.setdefault(source, set()).update(sql_domains)

    return index, {k: sorted(v) for k, v in source_domains.items()}


def _origin_label(q: Question) -> str:
    if q.provenance is None:
        return "generated"
    origin = q.provenance.origin_type
    if origin == QuestionOriginType.LLM_GENERATED:
        return "generated"
    if origin in (QuestionOriginType.RETRIEVAL, QuestionOriginType.HYBRID):
        return "retrieved"
    return origin.value


def _generate_sql_interviews(
    provider: QuestionIntelligenceProvider,
    corpus_index: dict[str, dict],
    source_to_domains: dict[str, list[str]],
) -> list[dict]:
    records: list[dict] = []
    interview_idx = 0

    for cycle in range(3):
        for role, level in ROLES_SENIORITIES:
            interview_idx += 1
            if interview_idx > INTERVIEW_COUNT:
                break

            print(
                f"[{interview_idx}/{INTERVIEW_COUNT}] TECHNICAL {role.value} {level.value}",
                flush=True,
            )

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

            for q_idx, q in enumerate(questions, start=1):
                normalized = _normalize(q.prompt)
                corpus_entry = corpus_index.get(normalized, {})
                source = corpus_entry.get("source") or (
                    q.provenance.source_name if q.provenance else "unknown"
                )
                # Resolve domains: direct match first, then source-level fallback
                domains: list[str] = corpus_entry.get("domains") or source_to_domains.get(source, [])

                records.append(
                    {
                        "interview_id": interview_idx,
                        "cycle": cycle + 1,
                        "role": role.value,
                        "seniority": level.value,
                        "q_index": q_idx,
                        "question_id": q.id,
                        "prompt": q.prompt,
                        "prompt_normalized": normalized,
                        "difficulty": q.difficulty.value,
                        "source": source,
                        "domains": domains,
                        "origin": _origin_label(q),
                        "corpus_id": corpus_entry.get("id"),
                    }
                )

        if interview_idx >= INTERVIEW_COUNT:
            break

    return records


def _consecutive_same_domain_runs(records: list[dict]) -> int:
    by_interview: dict[int, list[list[str]]] = defaultdict(list)
    for r in records:
        by_interview[r["interview_id"]].append(r["domains"])

    runs = 0
    for domains_seq in by_interview.values():
        for i in range(1, len(domains_seq)):
            prev = set(domains_seq[i - 1])
            curr = set(domains_seq[i])
            if prev & curr:
                runs += 1
    return runs


def _report(records: list[dict]) -> dict:
    total = len(records)
    all_prompts = [r["prompt_normalized"] for r in records]
    prompt_counts = Counter(all_prompts)
    unique_prompts = len(prompt_counts)
    duplicate_q_rate = round((total - unique_prompts) / total * 100, 1) if total else 0.0

    all_domains_flat = [d for r in records for d in r["domains"]]
    domain_counts = Counter(all_domains_flat)

    interview_domains: dict[int, list[str]] = defaultdict(list)
    for r in records:
        interview_domains[r["interview_id"]].extend(r["domains"])

    per_interview_primary = [
        domains[0] if domains else "unknown"
        for domains in interview_domains.values()
    ]
    domain_per_interview = Counter(per_interview_primary)
    unique_domain_combos = len({
        frozenset(v) for v in interview_domains.values()
    })
    total_interviews = len(interview_domains)
    duplicate_domain_rate = round(
        (total_interviews - unique_domain_combos) / total_interviews * 100, 1
    ) if total_interviews else 0.0

    source_counts = Counter(r["source"] for r in records)
    difficulty_counts = Counter(r["difficulty"] for r in records)

    consecutive_runs = _consecutive_same_domain_runs(records)

    top_repeated = [
        {"prompt_preview": p[:100], "count": c, "rate_pct": round(c / total * 100, 1)}
        for p, c in prompt_counts.most_common(10)
        if c > 1
    ]

    top_domains = [
        {"domain": d, "count": c, "rate_pct": round(c / total * 100, 1)}
        for d, c in domain_counts.most_common(10)
    ]

    return {
        "summary": {
            "interviews_generated": total_interviews,
            "total_questions": total,
            "unique_prompts": unique_prompts,
            "duplicate_question_rate_pct": duplicate_q_rate,
            "unique_domain_combos": unique_domain_combos,
            "duplicate_domain_rate_pct": duplicate_domain_rate,
            "consecutive_same_domain_runs": consecutive_runs,
        },
        "domain_distribution": dict(domain_counts.most_common()),
        "difficulty_distribution": dict(sorted(difficulty_counts.items())),
        "source_distribution": dict(source_counts.most_common()),
        "top_repeated_questions": top_repeated,
        "top_repeated_domains": top_domains,
        "domain_per_interview_primary": dict(domain_per_interview.most_common()),
    }


def main() -> None:
    load_dotenv()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("SQL DIVERSITY AUDIT — Wave1", flush=True)
    print("=" * 60, flush=True)

    corpus_index, source_to_domains = _load_corpus_index()
    print(f"Corpus index size: {len(corpus_index)}", flush=True)

    llm = DefaultLLMAdapter()
    provider = QuestionIntelligenceProvider(llm)

    records = _generate_sql_interviews(provider, corpus_index, source_to_domains)

    report = _report(records)
    report["audit"] = "SQL Diversity Audit — Wave1"
    report["timestamp"] = datetime.now(timezone.utc).isoformat()
    report["raw_records"] = records

    output_path = OUTPUT_DIR / "audit_sql_diversity_wave1.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary = {k: v for k, v in report.items() if k != "raw_records"}

    print("\n" + json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}", flush=True)


if __name__ == "__main__":
    main()
