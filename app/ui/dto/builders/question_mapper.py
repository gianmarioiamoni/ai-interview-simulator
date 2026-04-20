# app/ui/dto/builders/question_mapper.py

from typing import List

from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO
from app.ui.utils.error_formatter import simplify_execution_error
from app.ui.mappers.interview_area_mapper import InterviewAreaMapper


class QuestionMapper:

    def map(self, state) -> List[QuestionAssessmentDTO]:

        assessments = []

        for q in state.questions:

            result = state.results_by_question.get(q.id)
            if result is None:
                continue

            assessments.append(
                self._map_single(q, result, state)
            )  # 🔥 pass full question

        return assessments

    def _map_single(self, question, result, state) -> QuestionAssessmentDTO:

        question_id = question.id

        score = 0.0
        feedback = ""

        passed_tests = None
        total_tests = None
        execution_status = None

        attempts = state.get_attempt_for_question(question_id)

        ai_hint_explanation = None
        ai_hint_suggestion = None

        # ---------------- Evaluation

        if result.evaluation and not result.execution:
            score = result.evaluation.score
            feedback = result.evaluation.feedback

        # ---------------- Execution

        elif result.execution:

            exec_res = result.execution
            execution_status = exec_res.status.value

            if exec_res.total_tests == 0 and not exec_res.success:
                execution_status = "RUNTIME_ERROR"
                score = 0
            else:
                passed_tests = exec_res.passed_tests
                total_tests = exec_res.total_tests

                if exec_res.total_tests:
                    score = (exec_res.passed_tests / exec_res.total_tests) * 100
                elif exec_res.success:
                    score = 100
                else:
                    score = 0

            feedback = (
                simplify_execution_error(exec_res.error)
                or "Execution evaluated automatically."
            )

        # ---------------- AI Hint

        if result.ai_hint:
            ai_hint_explanation = result.ai_hint.explanation
            ai_hint_suggestion = result.ai_hint.suggestion

        # ---------------- AREA

        area_label = InterviewAreaMapper.to_label(question.area)

        return QuestionAssessmentDTO(
            question_id=question_id,
            score=score,
            feedback=feedback,
            passed_tests=passed_tests,
            total_tests=total_tests,
            execution_status=execution_status,
            attempts=attempts,
            ai_hint_explanation=ai_hint_explanation,
            ai_hint_suggestion=ai_hint_suggestion,
            area=area_label,  
        )
