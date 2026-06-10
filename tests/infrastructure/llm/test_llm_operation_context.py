# tests/infrastructure/llm/test_llm_operation_context.py

from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext


def test_set_and_get_operation() -> None:
    token = LLMOperationContext.set_operation("written_evaluation")

    try:
        assert LLMOperationContext.get_operation() == "written_evaluation"
    finally:
        LLMOperationContext.reset(token)


def test_reset_restores_previous_operation() -> None:
    outer = LLMOperationContext.set_operation("question_generation")

    try:
        inner = LLMOperationContext.set_operation("hint_generation")
        assert LLMOperationContext.get_operation() == "hint_generation"
        LLMOperationContext.reset(inner)
        assert LLMOperationContext.get_operation() == "question_generation"
    finally:
        LLMOperationContext.reset(outer)


def test_nested_scopes() -> None:
    with LLMOperationContext.scope("narrative_generation"):
        assert LLMOperationContext.get_operation() == "narrative_generation"

        inner = LLMOperationContext.set_operation("answer_improvement")
        try:
            assert LLMOperationContext.get_operation() == "answer_improvement"
        finally:
            LLMOperationContext.reset(inner)

        assert LLMOperationContext.get_operation() == "narrative_generation"


def test_default_operation_is_unknown() -> None:
    assert LLMOperationContext.get_operation() == "unknown"
