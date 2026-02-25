# app/ui/sample_data_loader.py

import json
from pathlib import Path
from typing import List

from domain.contracts.question import Question, QuestionType


def load_sample_questions() -> List[Question]:
    file_path = Path("data/sample_questions.json")

    with open(file_path, "r") as f:
        raw_questions = json.load(f)

    questions: List[Question] = []

    for q in raw_questions:
        questions.append(
            Question(
                id=q["id"],
                area=q["area"],
                type=QuestionType(q["type"]),
                prompt=q["prompt"],
                difficulty=q["difficulty"],
            )
        )

    return questions
