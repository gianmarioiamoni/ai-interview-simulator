# services/interview_evaluation/generators/narrative_generator.py

import logging
import json

from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS

logger = logging.getLogger(__name__)


class NarrativeGenerator:

    def __init__(self, llm):
        self._llm = llm

    def generate(self, evaluations, dimension_scores, interview_type, role):

        readable_dimension_scores = {
            DIMENSION_LABELS.get(dim, dim.value): (
                score if score is not None else "NOT_EVALUATED"
            )
            for dim, score in dimension_scores.items()
        }

        prompt = f"""
You are a senior technical interviewer.

Role: {role.value}
Interview type: {interview_type.value}

Here are evaluated answers:
{[e.model_dump() for e in evaluations]}

Dimension scores:
{readable_dimension_scores}

Provide:

1. Justification for each dimension
2. 3 improvement suggestions

Return STRICT JSON only.
No explanations.
No text outside JSON.
"""

        response = self._llm.invoke(prompt)

        try:
            parsed = self._extract_json(response.content)

            if "dimension_justifications" not in parsed:
                parsed["dimension_justifications"] = {}
            if "improvement_suggestions" not in parsed:
                parsed["improvement_suggestions"] = []

            return parsed

        except Exception:
            logger.warning("narrative_json_parsing_failed")

            return {
                "dimension_justifications": {
                    name: "Justification unavailable."
                    for name in DIMENSION_LABELS.values()
                },
                "improvement_suggestions": [],
            }

    # -----------------------------------------------------

    def _extract_json(self, text: str):

        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            return json.loads(text[start : end + 1])
