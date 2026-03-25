# services/answer_improvement/answer_improver.py

from infrastructure.llm.llm_factory import get_llm


class AnswerImprover:

    def __init__(self):
        self._llm = get_llm()

    def improve(
        self,
        question: str,
        user_answer: str,
        feedback: str,
    ) -> str:

        prompt = f"""
You are a senior technical interviewer.

Your task is to rewrite the candidate's answer to make it stronger.

CONTEXT:
Question:
{question}

Candidate Answer:
{user_answer}

Feedback:
{feedback}

INSTRUCTIONS:
- Keep the original intent
- Improve clarity and structure
- Add a concrete example if missing
- Be concise but strong
- Do NOT explain, just output the improved answer

OUTPUT:
"""

        try:
            response = self._llm.invoke(prompt)
            return response.content.strip()
        except Exception:
            return ""
