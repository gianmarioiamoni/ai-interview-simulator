# scripts/question_intelligence/audit_interview_generation.py

# End-to-end interview generation audit.
# Runs AreaQuestionBuilder per area (fixed order) and reports provenance + memory.

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import QuestionType
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from infrastructure.llm.llm_adapter import DefaultLLMAdapter
from infrastructure.vector_store.chroma_question_store import ChromaQuestionStore
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.area_question_builder import AreaQuestionBuilder
from services.question_intelligence.coding_question_generator import (
    CodingQuestionGenerator,
)
from services.question_intelligence.question_generator import QuestionGenerator
from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)
from services.question_intelligence.question_vector_store import QuestionVectorStore
from services.question_intelligence.sql_question_generator import SQLQuestionGenerator
from services.question_intelligence.coding_question_generator import (
    CodingQuestionGenerator,
)
from app.settings.constants import QUESTIONS_PER_AREA

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORPUS_ROOTS = [
    PROJECT_ROOT / "datasets/curated/hf_import",
    PROJECT_ROOT / "datasets/curated/interview_seed",
    PROJECT_ROOT / "datasets/curated/local_import",
    PROJECT_ROOT / "datasets/curated",
]

AREA_ORDER = [
    InterviewArea.TECH_BACKGROUND,
    InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
    InterviewArea.TECH_CASE_STUDY,
    InterviewArea.TECH_DATABASE,
    InterviewArea.TECH_CODING,
]


def load_corpus_index() -> dict[str, dict]:

    index: dict[str, dict] = {}

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

                if not doc_id:
                    continue

                index[str(doc_id)] = {
                    "source": item.get("source", "unknown"),
                    "question": item.get("question", ""),
                    "area": item.get("area", ""),
                }

    return index


def format_memory(memory: InterviewRetrievalMemory) -> str:

    ids = memory.asked_question_ids

    return (
        f"asked_ids={ids} "
        f"covered_domains={memory.covered_domains} "
        f"difficulty_history={memory.difficulty_history}"
    )


def resolve_origin(
    question,
    memory_before: InterviewRetrievalMemory,
    memory_after: InterviewRetrievalMemory,
    corpus_index: dict[str, dict],
) -> tuple[str, str | None, float | None, str | None, str]:

    new_ids = [
        qid
        for qid in memory_after.asked_question_ids
        if qid not in memory_before.asked_question_ids
    ]

    provenance = question.provenance

    if provenance is not None:
        corpus_id = new_ids[-1] if new_ids else None
        entry = corpus_index.get(corpus_id) if corpus_id else None
        seed = entry.get("question", "")[:80] if entry else ""

        return (
            provenance.origin_type.value.upper(),
            provenance.source_name,
            provenance.retrieval_score,
            corpus_id,
            seed,
        )

    if new_ids:
        doc_id = new_ids[-1]
        entry = corpus_index.get(doc_id, {})

        return (
            QuestionOriginType.RETRIEVAL.value.upper(),
            entry.get("source"),
            None,
            doc_id,
            (entry.get("question") or "")[:80],
        )

    prompt_key = question.prompt.split("\n")[0].strip().lower()

    for doc_id, entry in corpus_index.items():
        corpus_q = (entry.get("question") or "").strip().lower()

        if corpus_q and (corpus_q in prompt_key or prompt_key.startswith(corpus_q)):
            return (
                QuestionOriginType.RETRIEVAL.value.upper(),
                entry.get("source"),
                None,
                doc_id,
                entry.get("question", "")[:80],
            )

    return "GENERATED", None, None, None, ""


def question_type_label(question) -> str:

    return question.type.value


def main() -> None:

    load_dotenv()

    corpus_index = load_corpus_index()

    llm = DefaultLLMAdapter()
    chroma_store = ChromaQuestionStore()
    vector_store = QuestionVectorStore(chroma_store)
    retrieval_service = QuestionRetrievalService(vector_store)

    area_builder = AreaQuestionBuilder(
        retrieval_service=retrieval_service,
        generator=QuestionGenerator(llm),
        coding_generator=CodingQuestionGenerator(llm),
        sql_generator=SQLQuestionGenerator(llm),
    )

    role = RoleType.FULLSTACK_ENGINEER
    level = SeniorityLevel.MID
    interview_type = InterviewType.TECHNICAL

    memory = InterviewRetrievalMemory()

    print("=" * 80)
    print("INTERVIEW GENERATION AUDIT")
    print(f"Role: {role.value} | Level: {level.value} | Type: {interview_type.value}")
    print(f"Questions per area: {QUESTIONS_PER_AREA}")
    print(f"Corpus index entries loaded: {len(corpus_index)}")
    print("=" * 80)

    retrieval_count = 0
    generated_count = 0

    for area in AREA_ORDER:

        memory_before = memory.model_copy(deep=True)

        questions, memory = area_builder.build(
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
            questions_per_area=QUESTIONS_PER_AREA,
            memory=memory,
        )

        print()
        print("-" * 80)
        print(f"AREA: {area.value}")
        print("-" * 80)

        if not questions:
            print("(no questions produced)")
            print(f"Memory after: {format_memory(memory)}")
            continue

        for idx, question in enumerate(questions, start=1):

            origin, source, score, corpus_id, corpus_seed = resolve_origin(
                question,
                memory_before,
                memory,
                corpus_index,
            )

            if origin == QuestionOriginType.RETRIEVAL.value.upper():
                retrieval_count += 1
            else:
                generated_count += 1

            score_str = f"{score:.3f}" if score is not None else "n/a"

            prompt_preview = question.prompt.replace("\n", " ")
            if len(prompt_preview) > 120:
                prompt_preview = prompt_preview[:117] + "..."

            print()
            print(f"  Question {idx} [{question_type_label(question)}]")
            print(f"    Prompt: {prompt_preview}")
            print(f"    Origin: {origin}")
            print(f"    Corpus source: {source or 'n/a'}")
            print(f"    Corpus document_id: {corpus_id or 'n/a'}")
            if corpus_seed:
                print(f"    Corpus seed: {corpus_seed}")
            print(f"    Retrieval score: {score_str}")

            if question.provenance and question.provenance.generated_by_model:
                print(
                    f"    Enrichment model: {question.provenance.generated_by_model}",
                )

            if question.type == QuestionType.CODING and question.coding_spec:
                print(
                    f"    Coding entrypoint: {question.coding_spec.entrypoint} "
                    f"tests={len(question.visible_tests)}",
                )

            if question.type == QuestionType.DATABASE:
                print(f"    SQL test cases: {len(question.sql_test_cases)}")

        print()
        print(f"  Memory after area: {format_memory(memory)}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print(f"  Retrieval-sourced questions: {retrieval_count}")
    print(f"  Generated (no retrieval provenance): {generated_count}")
    print(f"  Final memory asked_ids ({len(memory.asked_question_ids)}): ")
    print(f"    {memory.asked_question_ids}")
    print("=" * 80)


if __name__ == "__main__":
    main()
