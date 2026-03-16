# app/graph/nodes/answer_handler_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType

from services.execution_engine import ExecutionEngine
from services.prompt_builders.evaluation_prompt_builder import build_evaluation_prompt

from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.evaluation_decision import EvaluationDecision


def build_answer_handler_node(llm):

    engine = ExecutionEngine()

    def answer_handler_node(state: InterviewState) -> InterviewState:

        question = state.current_question
        answer = state.last_answer

        if question is None or answer is None:
            return state

        # ---------------------------------------------------------
        # WRITTEN QUESTION
        # ---------------------------------------------------------

        if question.type == QuestionType.WRITTEN:

            result = state.get_result_for_question(question.id)

            # Avoid double evaluation
            if result and result.evaluation:
                return state

            prompt = build_evaluation_prompt(question, answer)

            response = llm.invoke(prompt)

            try:

                decision = EvaluationDecision.model_validate_json(response.content)

                evaluation = QuestionEvaluation(
                    question_id=question.id,
                    score=decision.score,
                    max_score=100,
                    passed=decision.score >= 60,
                    feedback=decision.feedback,
                    strengths=getattr(decision, "strengths", []),
                    weaknesses=getattr(decision, "weaknesses", []),
                )

            except Exception:

                evaluation = QuestionEvaluation(
                    question_id=question.id,
                    score=0,
                    max_score=100,
                    passed=False,
                    feedback="Evaluation failed due to parsing error.",
                    strengths=[],
                    weaknesses=["Evaluation parsing failed"],
                )

            state.register_evaluation(evaluation)

        # ---------------------------------------------------------
        # CODING / DATABASE
        # ---------------------------------------------------------

        elif question.type in (QuestionType.CODING, QuestionType.DATABASE):

            result = state.get_result_for_question(question.id)

            # Avoid double execution
            if result and result.execution:
                return state

            execution = engine.execute(
                question,
                answer.content,
            )

            state.register_execution(execution)

        # ---------------------------------------------------------
        # IMPORTANT
        # Do NOT advance the question here.
        # The UI will decide when to move to the next question.
        # ---------------------------------------------------------

        return state

    return answer_handler_node
