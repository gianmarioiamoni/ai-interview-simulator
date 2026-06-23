# services/interview_evaluation/builders/improvement_builder.py

from typing import List, Optional

from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS


class ImprovementBuilder:

    def build(
        self,
        dimension_scores,
        narrative,
        evaluations: Optional[List[QuestionEvaluation]] = None,
    ) -> List[str]:

        missing_dims = [
            DIMENSION_LABELS.get(dim, dim.value)
            for dim, score in dimension_scores.items()
            if score is None
        ]

        improvements = narrative.get("improvement_suggestions", []) or []

        # Filter out empty/whitespace entries from LLM output
        improvements = [s for s in improvements if s and s.strip()]

        # Fallback: derive from per-question weaknesses when LLM returns nothing
        if not improvements and evaluations:
            seen: set = set()
            for ev in evaluations:
                for w in (ev.weaknesses or []):
                    if w and w not in seen:
                        improvements.append(w)
                        seen.add(w)
                        if len(improvements) >= 3:
                            break
                if len(improvements) >= 3:
                    break

        if missing_dims:
            improvements += [
                f"{dim} was not assessed — consider practicing this area."
                for dim in missing_dims
            ]

        return improvements
