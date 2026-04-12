# domain/services/evaluation_aggregator.py

from typing import List, Dict
from domain.contracts.question.question_evaluation import QuestionEvaluation


class EvaluationAggregator:

    @staticmethod
    def aggregate(evaluations: List[QuestionEvaluation]) -> Dict:

        if not evaluations:
            return {
                "score": 0,
                "strengths": [],
                "weaknesses": [],
                "decision": "no_hire",
            }

        scores = []
        strengths = []
        weaknesses = []

        for ev in evaluations:

            score = ev.score or 0
            scores.append(score)

            if score >= 0.8:
                strengths.append(ev.topic or "general")
            elif score < 0.5:
                weaknesses.append(ev.topic or "general")

        avg_score = sum(scores) / len(scores)

        decision = "hire" if avg_score >= 0.7 else "no_hire"

        return {
            "score": round(avg_score, 2),
            "strengths": list(set(strengths)),
            "weaknesses": list(set(weaknesses)),
            "decision": decision,
        }
