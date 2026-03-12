# app/graph/nodes/evaluation_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from domain.contracts.question_evaluation import QuestionEvaluation
from services.prompt_builders.evaluation_prompt_builder import build_evaluation_prompt
from domain.contracts.evaluation_decision import EvaluationDecision


def build_evaluation_node(llm):

    def evaluation_node(state: InterviewState) -> InterviewState:

        question = state.current_question
        answer = state.last_answer

        print("EVALUATION NODE:", question.id)


        if question is None or answer is None:
            return state

        if question.type != QuestionType.WRITTEN:
            return state

        # ---------------------------------------------------------
        # Avoid double evaluation
        # ---------------------------------------------------------

        existing = state.get_result_for_question(question.id)

        if existing and existing.evaluation is not None:
            return state

        # ---------------------------------------------------------
        # LLM evaluation
        # ---------------------------------------------------------

        prompt = build_evaluation_prompt(question, answer)

        response = llm.invoke(prompt)

        try:
            decision = EvaluationDecision.model_validate_json(response.content)
        except Exception:
            return state

        evaluation = QuestionEvaluation(
            question_id=question.id,
            score=decision.score,
            max_score=100,
            passed=decision.score >= 60,
            feedback=decision.feedback,
            strengths=getattr(decision, "strengths", []),
            weaknesses=getattr(decision, "weaknesses", []),
        )

        state.register_evaluation(evaluation)

        return state

    return evaluation_node
