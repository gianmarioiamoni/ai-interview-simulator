from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from domain.contracts.question_evaluation import QuestionEvaluation
from services.prompt_builders.evaluation_prompt_builder import build_evaluation_prompt
from domain.contracts.evaluation_decision import EvaluationDecision


def build_evaluation_node(llm):

    def evaluation_node(state: InterviewState) -> InterviewState:

        question = state.current_question
        answer = state.last_answer

        if question is None or answer is None:
            return state

        if question.type != QuestionType.WRITTEN:
            return state

        print("EVALUATION NODE:", question.id)

        existing = state.get_result_for_question(question.id)

        if existing and existing.evaluation is not None:
            return state

        prompt = build_evaluation_prompt(question, answer)

        response = llm.invoke(prompt)

        # ---------------------------------------------------------
        # Try to parse structured LLM output
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Safe fallback if parsing fails
        # ---------------------------------------------------------

        except Exception as e:

            print("EVALUATION PARSE ERROR:", e)
            print("LLM RAW RESPONSE:", response.content)

            evaluation = QuestionEvaluation(
                question_id=question.id,
                score=0,
                max_score=100,
                passed=False,
                feedback="Evaluation failed due to LLM parsing error.",
                strengths=[],
                weaknesses=["Evaluation parsing failed"],
            )

        print("REGISTER EVAL:", question.id)

        state.register_evaluation(evaluation)

        return state

    return evaluation_node
