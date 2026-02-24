# services/prompt_builders/humanizer_prompt_builder.py

from domain.contracts.question import Question


def build_humanizer_prompt(
    question: Question,
    language: str,
    chat_history: list[str],
) -> str:
    # Build prompt to reformulate question conversationally
    # Must preserve technical meaning and constraints

    history_snippet = "\n".join(chat_history[-5:]) if chat_history else ""

    return f"""
You are a professional technical interviewer.

Rephrase the following question in a natural conversational way.

Constraints:
- Do NOT change the technical requirements.
- Do NOT remove constraints.
- Do NOT simplify coding tasks.
- Preserve original meaning.
- Keep the same difficulty level.
- Output plain text only.

Language: {language}

Previous conversation context:
{history_snippet}

Original question:
{question.prompt}
""".strip()
