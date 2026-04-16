# app/graph/nodes/evaluation_aggregate_node.py


from services.interview_evaluation_service import InterviewEvaluationService


class EvaluationAggregateNode:

    def __init__(self, service):
        self._service = service

    def __call__(self, state):

        # safety (idempotency)
        if state.interview_evaluation is not None:
            return state

        if not state.is_completed:
            return state

        evaluations = [
            r.evaluation for r in state.results_by_question.values() if r.evaluation
        ]

        interview_eval = self._service.evaluate(
            per_question_evaluations=evaluations,
            questions=state.questions,
            interview_type=state.interview_type,
            role=state.role.type,
        )

        return state.model_copy(update={"interview_evaluation": interview_eval})
