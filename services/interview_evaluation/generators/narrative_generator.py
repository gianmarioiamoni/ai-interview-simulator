# services/interview_evaluation/generators/narrative_generator.py

import json

from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS

from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer

from app.core.logger import get_logger
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.metrics.llm_operation_names import NARRATIVE_GENERATION

logger = get_logger(__name__)


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

        # convert to string
        evaluations_str = json.dumps([e.model_dump() for e in evaluations], indent=2)
        readable_dimension_scores_str = json.dumps(readable_dimension_scores, indent=2)

        template = PromptLoader.load("narrative/narrative_generator.txt")

        context = {
            "role": role.value,
            "interview_type": interview_type.value,
            "evaluations": evaluations_str,
            "dimension_scores": readable_dimension_scores_str,
        }
        prompt = PromptRenderer.render(template, context)

        with LLMOperationContext.scope(NARRATIVE_GENERATION):
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
            if start == -1 or end == -1:
                raise ValueError("Invalid JSON format")
            
            
            return json.loads(text[start : end + 1])
