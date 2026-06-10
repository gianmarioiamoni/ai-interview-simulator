# scripts/question_intelligence/audit_cross_interview_diversity.py

# Phase 7C-A — Cross-Interview Diversity Attribution Audit (read-only).

from __future__ import annotations

import json
import re
import sys
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from infrastructure.llm.llm_adapter import DefaultLLMAdapter
from services.question_intelligence.constrained_equivalence_band import (
    ConstrainedEquivalenceBand,
)
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

INTERVIEW_CONFIGS: list[tuple[InterviewType, RoleType, SeniorityLevel]] = [
    (InterviewType.HR, RoleType.FULLSTACK_ENGINEER, SeniorityLevel.JUNIOR),
    (InterviewType.HR, RoleType.FULLSTACK_ENGINEER, SeniorityLevel.MID),
    (InterviewType.HR, RoleType.FULLSTACK_ENGINEER, SeniorityLevel.SENIOR),
    (InterviewType.HR, RoleType.BACKEND_ENGINEER, SeniorityLevel.JUNIOR),
    (InterviewType.HR, RoleType.BACKEND_ENGINEER, SeniorityLevel.MID),
    (InterviewType.HR, RoleType.BACKEND_ENGINEER, SeniorityLevel.SENIOR),
    (InterviewType.HR, RoleType.FRONTEND_ENGINEER, SeniorityLevel.MID),
    (InterviewType.HR, RoleType.DATA_ENGINEER, SeniorityLevel.MID),
    (InterviewType.HR, RoleType.ML_ENGINEER, SeniorityLevel.SENIOR),
    (InterviewType.HR, RoleType.DEVOPS_ENGINEER, SeniorityLevel.MID),
    (InterviewType.TECHNICAL, RoleType.BACKEND_ENGINEER, SeniorityLevel.MID),
    (InterviewType.TECHNICAL, RoleType.BACKEND_ENGINEER, SeniorityLevel.SENIOR),
    (InterviewType.TECHNICAL, RoleType.BACKEND_ENGINEER, SeniorityLevel.JUNIOR),
    (InterviewType.TECHNICAL, RoleType.FULLSTACK_ENGINEER, SeniorityLevel.MID),
    (InterviewType.TECHNICAL, RoleType.FULLSTACK_ENGINEER, SeniorityLevel.JUNIOR),
    (InterviewType.TECHNICAL, RoleType.FULLSTACK_ENGINEER, SeniorityLevel.SENIOR),
    (InterviewType.TECHNICAL, RoleType.FRONTEND_ENGINEER, SeniorityLevel.MID),
    (InterviewType.TECHNICAL, RoleType.FRONTEND_ENGINEER, SeniorityLevel.SENIOR),
    (InterviewType.TECHNICAL, RoleType.DATA_ENGINEER, SeniorityLevel.MID),
    (InterviewType.TECHNICAL, RoleType.DATA_ENGINEER, SeniorityLevel.SENIOR),
    (InterviewType.TECHNICAL, RoleType.ML_ENGINEER, SeniorityLevel.MID),
    (InterviewType.TECHNICAL, RoleType.ML_ENGINEER, SeniorityLevel.SENIOR),
    (InterviewType.TECHNICAL, RoleType.DEVOPS_ENGINEER, SeniorityLevel.MID),
    (InterviewType.TECHNICAL, RoleType.DEVOPS_ENGINEER, SeniorityLevel.SENIOR),
    (InterviewType.TECHNICAL, RoleType.QA_ENGINEER, SeniorityLevel.MID),
    (InterviewType.TECHNICAL, RoleType.QA_ENGINEER, SeniorityLevel.JUNIOR),
    (InterviewType.TECHNICAL, RoleType.BACKEND_ENGINEER, SeniorityLevel.MID),
    (InterviewType.TECHNICAL, RoleType.DATA_ENGINEER, SeniorityLevel.SENIOR),
    (InterviewType.TECHNICAL, RoleType.FULLSTACK_ENGINEER, SeniorityLevel.MID),
    (InterviewType.TECHNICAL, RoleType.ML_ENGINEER, SeniorityLevel.JUNIOR),
]

_SELECTION_EVENTS: list[dict[str, Any]] = []
_ORIGINAL_DIVERSIFY = ConstrainedEquivalenceBand.diversify_pick


def _normalize_prompt(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text.strip().lower())
    return collapsed


def _load_corpus_index() -> dict[str, dict[str, str]]:
    prompt_to_doc: dict[str, dict[str, str]] = {}

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

                doc_id = item.get("id")
                question = item.get("question", "")

                if not doc_id or not question:
                    continue

                prompt_to_doc[_normalize_prompt(str(question))] = {
                    "document_id": str(doc_id),
                    "area": str(item.get("area", "")),
                    "source": str(item.get("source", "")),
                }

    return prompt_to_doc


def _instrument_equivalence_band() -> None:

    def _wrapped(
        self: ConstrainedEquivalenceBand,
        *,
        pool: list,
        best,
        target: int,
        previous_difficulty: int | None,
        context,
        rank_index: dict[int, int],
        selected_bank_items: list,
    ):
        best_tier = self._adaptive_tier(
            candidate=best,
            target=target,
            previous_difficulty=previous_difficulty,
        )
        equivalents = self._collect_equivalents(
            pool=pool,
            best=best,
            best_tier=best_tier,
            target=target,
            previous_difficulty=previous_difficulty,
            context=context,
            selected_bank_items=selected_bank_items,
        )
        pick = _ORIGINAL_DIVERSIFY(
            self,
            pool=pool,
            best=best,
            target=target,
            previous_difficulty=previous_difficulty,
            context=context,
            rank_index=rank_index,
            selected_bank_items=selected_bank_items,
        )
        pick_doc = str(pick.document.metadata.get("document_id", ""))
        best_doc = str(best.document.metadata.get("document_id", ""))
        _SELECTION_EVENTS.append(
            {
                "area": context.target_area,
                "target_difficulty": target,
                "pool_size": len(pool),
                "best_tier": list(best_tier),
                "equivalents_count": len(equivalents),
                "fresh_start": self._is_fresh_start(
                    context=context,
                    selected_bank_items=selected_bank_items,
                ),
                "picked_document_id": pick_doc,
                "best_document_id": best_doc,
                "selector_changed_pick": pick_doc != best_doc,
            }
        )
        return pick

    ConstrainedEquivalenceBand.diversify_pick = _wrapped  # type: ignore[method-assign]


def _origin_label(question: Question) -> str:
    if question.provenance is None:
        return "generated"

    origin = question.provenance.origin_type

    if origin == QuestionOriginType.LLM_GENERATED:
        return "generated"

    if origin in (QuestionOriginType.RETRIEVAL, QuestionOriginType.HYBRID):
        return "retrieved"

    if origin == QuestionOriginType.FOLLOW_UP:
        return "follow_up"

    return origin.value


def _is_follow_up(question: Question) -> bool:
    if question.provenance is None:
        return False

    return question.provenance.origin_type == QuestionOriginType.FOLLOW_UP


def _resolve_document_id(
    question: Question,
    corpus_by_prompt: dict[str, dict[str, str]],
) -> str | None:
    normalized = _normalize_prompt(question.prompt)
    match = corpus_by_prompt.get(normalized)

    if match:
        return match["document_id"]

    if question.provenance and question.provenance.origin_type in (
        QuestionOriginType.RETRIEVAL,
        QuestionOriginType.HYBRID,
    ):
        return None

    return None


@dataclass
class DeliveredQuestion:
    interview_id: str
    path: str
    role: str
    seniority: str
    interview_type: str
    area: str
    question_index: int
    question_id: str
    document_id: str | None
    generated_vs_retrieved: str
    difficulty: str
    follow_up: bool
    prompt_normalized: str
    prompt_preview: str


@dataclass
class AuditMetrics:
    total_prompts: int = 0
    unique_prompts: int = 0
    reuse_pct: float = 0.0
    top_repeated: list[dict[str, Any]] = field(default_factory=list)


def _collect_delivered(
    *,
    interview_id: str,
    path: str,
    interview_type: InterviewType,
    role: RoleType,
    level: SeniorityLevel,
    questions: list[Question],
    corpus_by_prompt: dict[str, dict[str, str]],
) -> list[DeliveredQuestion]:
    rows: list[DeliveredQuestion] = []

    for index, question in enumerate(questions, start=1):
        normalized = _normalize_prompt(question.prompt)
        rows.append(
            DeliveredQuestion(
                interview_id=interview_id,
                path=path,
                role=role.value,
                seniority=level.value,
                interview_type=interview_type.value,
                area=question.area.value,
                question_index=index,
                question_id=question.id,
                document_id=_resolve_document_id(question, corpus_by_prompt),
                generated_vs_retrieved=_origin_label(question),
                difficulty=question.difficulty.value,
                follow_up=_is_follow_up(question),
                prompt_normalized=normalized,
                prompt_preview=question.prompt[:120],
            )
        )

    return rows


def _global_metrics(rows: list[DeliveredQuestion]) -> AuditMetrics:
    counts = Counter(row.prompt_normalized for row in rows)
    total = len(rows)
    unique = len(counts)
    repeated = total - unique
    reuse_pct = round((repeated / total) * 100, 1) if total else 0.0

    top = [
        {
            "count": count,
            "reuse_pct": round((count / total) * 100, 1) if total else 0.0,
            "prompt_preview": next(
                row.prompt_preview for row in rows if row.prompt_normalized == prompt
            ),
            "document_id": next(
                (
                    row.document_id
                    for row in rows
                    if row.prompt_normalized == prompt and row.document_id
                ),
                None,
            ),
        }
        for prompt, count in counts.most_common(10)
        if count > 1
    ]

    return AuditMetrics(
        total_prompts=total,
        unique_prompts=unique,
        reuse_pct=reuse_pct,
        top_repeated=top,
    )


def _by_position(rows: list[DeliveredQuestion]) -> dict[str, dict[str, Any]]:
    grouped: dict[int, list[DeliveredQuestion]] = defaultdict(list)

    for row in rows:
        grouped[row.question_index].append(row)

    result: dict[str, dict[str, Any]] = {}

    for position in range(1, 6):
        bucket = grouped.get(position, [])

        if not bucket:
            continue

        counts = Counter(row.prompt_normalized for row in bucket)
        total = len(bucket)
        unique = len(counts)
        top_prompt, top_count = counts.most_common(1)[0]

        result[f"Q{position}"] = {
            "total": total,
            "unique": unique,
            "reuse_pct": round(((total - unique) / total) * 100, 1),
            "top_prompt_share_pct": round((top_count / total) * 100, 1),
            "top_count": top_count,
        }

    return result


def _by_area(rows: list[DeliveredQuestion]) -> list[dict[str, Any]]:
    grouped: dict[str, list[DeliveredQuestion]] = defaultdict(list)

    for row in rows:
        grouped[row.area].append(row)

    area_stats: list[dict[str, Any]] = []

    for area, bucket in grouped.items():
        prompt_counts = Counter(row.prompt_normalized for row in bucket)
        doc_counts = Counter(
            row.document_id for row in bucket if row.document_id is not None
        )
        total = len(bucket)
        unique = len(prompt_counts)
        top_doc_count = doc_counts.most_common(1)[0][1] if doc_counts else 0

        area_stats.append(
            {
                "area": area,
                "total": total,
                "unique": unique,
                "reuse_pct": round(((total - unique) / total) * 100, 1),
                "top_doc_share_pct": round((top_doc_count / total) * 100, 1)
                if total
                else 0.0,
                "top_document_id": doc_counts.most_common(1)[0][0]
                if doc_counts
                else None,
            }
        )

    area_stats.sort(key=lambda item: item["reuse_pct"], reverse=True)
    return area_stats


def _by_profile(rows: list[DeliveredQuestion]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[DeliveredQuestion]] = defaultdict(list)

    for row in rows:
        key = (row.interview_type, row.role, row.seniority)
        grouped[key].append(row)

    profiles: list[dict[str, Any]] = []

    for (interview_type, role, seniority), bucket in grouped.items():
        interviews = Counter(row.interview_id for row in bucket)
        duplicate_interviews = sum(
            1
            for interview_id in interviews
            if len([row for row in bucket if row.interview_id == interview_id]) > 0
        )
        prompt_counts = Counter(row.prompt_normalized for row in bucket)
        doc_counts = Counter(
            row.document_id for row in bucket if row.document_id is not None
        )
        total = len(bucket)
        unique = len(prompt_counts)
        repeated_doc_total = sum(
            count for count in doc_counts.values() if count > 1
        )

        profiles.append(
            {
                "profile": f"{interview_type}/{role}/{seniority}",
                "interviews": len(interviews),
                "total_prompts": total,
                "unique_prompts": unique,
                "overlap_pct": round(((total - unique) / total) * 100, 1),
                "repeated_document_share_pct": round(
                    (repeated_doc_total / total) * 100,
                    1,
                )
                if total
                else 0.0,
            }
        )

    profiles.sort(key=lambda item: item["overlap_pct"], reverse=True)
    return profiles


def _attribution_for_repeated(
    rows: list[DeliveredQuestion],
    selection_events: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = Counter(row.prompt_normalized for row in rows)
    repeated_prompts = {prompt for prompt, count in counts.items() if count > 1}

    area_event_index: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for event in selection_events:
        area_event_index[event["area"]].append(event)

    categories = Counter()
    samples: list[dict[str, Any]] = []

    for prompt in sorted(repeated_prompts, key=lambda p: counts[p], reverse=True)[:15]:
        prompt_rows = [row for row in rows if row.prompt_normalized == prompt]
        area = prompt_rows[0].area
        events = area_event_index.get(area, [])

        pool_sizes = [event["pool_size"] for event in events]
        avg_pool = sum(pool_sizes) / len(pool_sizes) if pool_sizes else 0
        avg_equivalents = (
            sum(event["equivalents_count"] for event in events) / len(events)
            if events
            else 0
        )
        selector_changes = sum(
            1 for event in events if event["selector_changed_pick"]
        )

        if avg_pool <= 3:
            category = "A_retrieval_footprint"
        elif avg_equivalents <= 1.5:
            category = "B_selector_convergence"
        elif area.startswith("hr_") or area.endswith("_case_study"):
            category = "C_area_planner_convergence"
        elif any(row.question_index > 1 for row in prompt_rows):
            category = "D_adaptive_navigation_convergence"
        else:
            category = "B_selector_convergence"

        categories[category] += counts[prompt]

        samples.append(
            {
                "prompt_count": counts[prompt],
                "area": area,
                "document_id": prompt_rows[0].document_id,
                "generated_vs_retrieved": prompt_rows[0].generated_vs_retrieved,
                "avg_pool_size": round(avg_pool, 1),
                "avg_equivalents": round(avg_equivalents, 1),
                "category": category,
            }
        )

    return {
        "category_counts": dict(categories),
        "samples": samples,
    }


def _overlap_pct(batch_rows: list[DeliveredQuestion], adaptive_rows: list[DeliveredQuestion]) -> float:
    batch_prompts = {row.prompt_normalized for row in batch_rows}
    adaptive_prompts = {row.prompt_normalized for row in adaptive_rows}
    union = batch_prompts | adaptive_prompts

    if not union:
        return 0.0

    intersection = batch_prompts & adaptive_prompts
    return round((len(intersection) / len(union)) * 100, 1)


def _run_batch_interview(
    provider: QuestionIntelligenceProvider,
    interview_type: InterviewType,
    role: RoleType,
    level: SeniorityLevel,
) -> list[Question]:
    return provider.generate(
        role=role,
        level=level,
        interview_type=interview_type,
        areas=interview_type.get_areas(),
    )


def _run_adaptive_interview(
    provider: QuestionIntelligenceProvider,
    interview_type: InterviewType,
    role: RoleType,
    level: SeniorityLevel,
) -> list[Question]:
    first_questions, memory, planned_areas = provider.generate_first_question(
        role=role,
        level=level,
        interview_type=interview_type,
    )
    questions = list(first_questions)

    for generated_count in range(1, len(planned_areas)):
        question, memory = provider.lazy_adaptive_service.generate_next_question(
            role=role,
            level=level,
            interview_type=interview_type,
            planned_areas=planned_areas,
            generated_count=generated_count,
            memory=memory,
        )
        questions.append(question)

    return questions


def main() -> None:
    load_dotenv()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    corpus_by_prompt = _load_corpus_index()
    _instrument_equivalence_band()

    llm = DefaultLLMAdapter()
    provider = QuestionIntelligenceProvider(llm)

    batch_rows: list[DeliveredQuestion] = []
    adaptive_rows: list[DeliveredQuestion] = []

    print(f"Running {INTERVIEW_COUNT} batch interviews...", flush=True)

    for index, (interview_type, role, level) in enumerate(INTERVIEW_CONFIGS, start=1):
        interview_id = f"batch-{index:02d}-{uuid.uuid4().hex[:8]}"
        print(
            f"[batch {index}/{INTERVIEW_COUNT}] "
            f"{interview_type.value} {role.value} {level.value}",
            flush=True,
        )

        questions = _run_batch_interview(provider, interview_type, role, level)
        batch_rows.extend(
            _collect_delivered(
                interview_id=interview_id,
                path="batch_generate",
                interview_type=interview_type,
                role=role,
                level=level,
                questions=questions,
                corpus_by_prompt=corpus_by_prompt,
            )
        )

    print(f"Running {INTERVIEW_COUNT} adaptive interviews...", flush=True)

    for index, (interview_type, role, level) in enumerate(INTERVIEW_CONFIGS, start=1):
        interview_id = f"adaptive-{index:02d}-{uuid.uuid4().hex[:8]}"
        print(
            f"[adaptive {index}/{INTERVIEW_COUNT}] "
            f"{interview_type.value} {role.value} {level.value}",
            flush=True,
        )

        questions = _run_adaptive_interview(provider, interview_type, role, level)
        adaptive_rows.extend(
            _collect_delivered(
                interview_id=interview_id,
                path="lazy_adaptive",
                interview_type=interview_type,
                role=role,
                level=level,
                questions=questions,
                corpus_by_prompt=corpus_by_prompt,
            )
        )

    batch_global = _global_metrics(batch_rows)
    adaptive_global = _global_metrics(adaptive_rows)

    report = {
        "audit": "Phase 7C-A Cross-Interview Diversity Attribution",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "interview_count": INTERVIEW_COUNT,
        "corpus_prompt_index_size": len(corpus_by_prompt),
        "selection_events_captured": len(_SELECTION_EVENTS),
        "batch_generate": {
            "global": asdict(batch_global),
            "by_position": _by_position(batch_rows),
            "by_area": _by_area(batch_rows),
            "by_profile": _by_profile(batch_rows),
            "attribution": _attribution_for_repeated(batch_rows, _SELECTION_EVENTS),
        },
        "lazy_adaptive": {
            "global": asdict(adaptive_global),
            "by_position": _by_position(adaptive_rows),
            "by_area": _by_area(adaptive_rows),
            "by_profile": _by_profile(adaptive_rows),
        },
        "path_comparison": {
            "prompt_overlap_pct": _overlap_pct(batch_rows, adaptive_rows),
            "batch_reuse_pct": batch_global.reuse_pct,
            "adaptive_reuse_pct": adaptive_global.reuse_pct,
            "batch_unique": batch_global.unique_prompts,
            "adaptive_unique": adaptive_global.unique_prompts,
        },
        "delivered_questions": {
            "batch": [asdict(row) for row in batch_rows],
            "adaptive": [asdict(row) for row in adaptive_rows],
        },
    }

    output_path = OUTPUT_DIR / "phase_7c_a_cross_interview_diversity_audit.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary_path = OUTPUT_DIR / "phase_7c_a_summary.json"
    summary = {
        key: value
        for key, value in report.items()
        if key != "delivered_questions"
    }
    summary_path.write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nFull report: {output_path}", flush=True)


if __name__ == "__main__":
    main()
