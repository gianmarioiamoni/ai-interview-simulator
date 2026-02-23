from domain.contracts.question_bank_item import QuestionBankItem
import pytest
from pydantic import ValidationError


def test_question_bank_item_is_immutable():
    q = QuestionBankItem(
        id="1",
        text="Explain ACID properties.",
        interview_type="technical",
        area="databases",
        role="backend",
        level="mid",
        difficulty=3,
    )

    with pytest.raises(ValidationError):
        q.text = "Modified"
