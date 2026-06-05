# services/question_intelligence/interview_difficulty_ordering.py

from domain.contracts.question.question import Question
from domain.contracts.question.question_bank_item import QuestionBankItem
from services.planning.difficulty_progression_analyzer import DifficultyProgressionAnalyzer
from services.planning.difficulty_spike_suppressor import DifficultySpikeSuppressor
from services.question_intelligence.question_difficulty_mapper import (
    question_difficulty_to_corpus_int,
    question_to_bank_item_stub,
)


def append_difficulty_to_memory_history(
    difficulty_history: list[int],
    question: Question,
) -> list[int]:

    return [
        *difficulty_history,
        question_difficulty_to_corpus_int(question.difficulty),
    ]


def order_questions_for_interview_progression(
    questions: list[Question],
) -> list[Question]:

    if len(questions) < 2:
        return questions

    stubs = [question_to_bank_item_stub(q) for q in questions]
    ordered_stubs = _sort_by_difficulty(stubs)
    polished_stubs = _polish_with_spike_suppressor(ordered_stubs)

    question_by_id = {question.id: question for question in questions}
    return [
        question_by_id[stub.id]
        for stub in polished_stubs
        if stub.id in question_by_id
    ]


def calculate_progression_score(questions: list[Question]) -> float:

    if not questions:
        return 1.0

    stubs = [question_to_bank_item_stub(q) for q in questions]
    return DifficultyProgressionAnalyzer().calculate_progression_score(stubs)


def _sort_by_difficulty(stubs: list[QuestionBankItem]) -> list[QuestionBankItem]:

    return sorted(
        stubs,
        key=lambda item: (item.difficulty, item.area.value),
    )


def _polish_with_spike_suppressor(
    stubs: list[QuestionBankItem],
) -> list[QuestionBankItem]:

    suppressor = DifficultySpikeSuppressor()
    result = list(stubs)
    max_passes = len(result) * 2

    for _ in range(max_passes):
        changed = False

        for index in range(len(result) - 1):
            penalty = _spike_penalty(
                suppressor,
                result[index + 1],
                result[: index + 1],
            )

            if penalty == 0.0:
                continue

            if index + 2 >= len(result):
                continue

            trial = list(result)
            trial[index + 1], trial[index + 2] = trial[index + 2], trial[index + 1]

            if _total_spike_penalty(suppressor, trial) < _total_spike_penalty(
                suppressor,
                result,
            ):
                result = trial
                changed = True

        if not changed:
            break

    return result


def _spike_penalty(
    suppressor: DifficultySpikeSuppressor,
    candidate: QuestionBankItem,
    selected: list[QuestionBankItem],
) -> float:

    adjusted = suppressor.apply_penalty(
        candidate=candidate,
        selected_questions=selected,
        current_score=0.0,
    )

    return abs(adjusted)


def _total_spike_penalty(
    suppressor: DifficultySpikeSuppressor,
    stubs: list[QuestionBankItem],
) -> float:

    total = 0.0

    for index in range(1, len(stubs)):
        total += _spike_penalty(suppressor, stubs[index], stubs[:index])

    return total
