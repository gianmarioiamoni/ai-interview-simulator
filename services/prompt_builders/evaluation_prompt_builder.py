# services/prompt_builders/evaluation_prompt_builder.py

from domain.contracts.question import Question
from domain.contracts.answer import Answer


def build_evaluation_prompt(question: Question, answer: Answer) -> str:
    # Builds a strict evaluation prompt for the LLM
    # The output MUST be valid JSON following the required schema

    prompt = f"""
You are a senior technical interviewer.

Evaluate the candidate answer.

Question:
{question.content}

Answer:
{answer.content}

Return STRICT JSON with this structure:
{{
    "score": float between 0 and 100,
    "feedback": "concise but precise explanation",
    "clarification_needed": boolean,
    "follow_up_question": "string or null"
}}

Rules:
- Only suggest clarification if the answer is incomplete or ambiguous.
- Never generate follow-up for coding or SQL questions.
- Output JSON only.
"""

    return prompt.strip()
