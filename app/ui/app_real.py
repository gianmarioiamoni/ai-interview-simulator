# app/ui/app_real.py

import gradio as gr

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.role import Role, RoleType

from app.graph.builder import build_graph
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.ui.controllers.interview_controller import InterviewController
from app.ui.sample_data_loader import load_sample_questions


# ---------------------------------------------------------
# Wiring
# ---------------------------------------------------------

graph = build_graph()
mapper = InterviewStateMapper()
controller = InterviewController(graph, mapper)


# ---------------------------------------------------------
# Handlers
# ---------------------------------------------------------


def start_interview():
    questions = load_sample_questions()

    state = InterviewState(
        interview_id="demo-session",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="Demo Company",
        language="en",
        questions=questions,
        progress=InterviewProgress.SETUP,
    )

    session_dto = controller.start_interview(state)

    return (
        state,
        session_dto.current_question.text,
        f"Question {session_dto.current_question.index}/{session_dto.current_question.total}",
        "",
        gr.update(visible=True),
        gr.update(visible=False),
    )


def submit_answer(state: InterviewState, user_answer: str):

    result, feedback = controller.submit_answer(state, user_answer)

    # ---------------------------------------------------------
    # Final report case
    # ---------------------------------------------------------

    if hasattr(result, "overall_score"):

        report = result

        # Performance breakdown
        dimension_block = ""
        for dim in report.dimension_scores:
            dimension_block += f"- **{dim.name}**: {round(dim.score,1)}/100\n"

        # Question-level assessment
        question_block = ""
        for q in report.question_assessments:
            question_block += (
                f"\n### Question {q.question_id}\n"
                f"- Score: {round(q.score,1)}/100\n"
                f"- Feedback: {q.feedback}\n"
            )

        # Improvements
        improvement_block = ""
        for imp in report.improvement_suggestions:
            improvement_block += f"- {imp}\n"

        report_text = f"""
# 🧠 AI Interview Final Evaluation

---

## 📊 Executive Summary

The candidate demonstrated a structured performance across evaluated areas.

---

## 🎯 Overall Metrics

- **Overall Score:** {report.overall_score}/100  
- **Hiring Probability:** {report.hiring_probability}%  

---

## 📈 Performance Breakdown

{dimension_block}

---

## 📝 Question-Level Assessment

{question_block}

---

## 🚀 Improvement Roadmap

{improvement_block}

---

## 🔎 Evaluation Confidence

Model confidence in scoring consistency: {state.final_evaluation.confidence.final}

---

*This evaluation combines deterministic scoring with structured AI narrative analysis.*
"""

        return (
            state,
            "",
            "",
            "",
            gr.update(visible=False),
            gr.update(
                value=report_text,
                visible=True,
            ),
        )

    # ---------------------------------------------------------
    # In-progress case
    # ---------------------------------------------------------

    session = result

    return (
        state,
        session.current_question.text,
        f"Question {session.current_question.index}/{session.current_question.total}",
        "",
        gr.update(visible=True),
        gr.update(value=f"### Feedback\n\n{feedback}", visible=True),
    )


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------


def build_app():
    with gr.Blocks() as demo:

        gr.Markdown("# AI Interview Simulator")

        state = gr.State()

        start_button = gr.Button("Start Interview")

        question_counter = gr.Markdown("")
        question_text = gr.Markdown("")
        answer_box = gr.Textbox(label="Your Answer", lines=5)

        submit_button = gr.Button("Submit Answer", visible=False)

        report_output = gr.Markdown(visible=False)

        start_button.click(
            start_interview,
            outputs=[
                state,
                question_text,
                question_counter,
                answer_box,
                submit_button,
                report_output,
            ],
        )

        submit_button.click(
            submit_answer,
            inputs=[state, answer_box],
            outputs=[
                state,
                question_text,
                question_counter,
                answer_box,
                submit_button,
                report_output,
            ],
        )

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch()
