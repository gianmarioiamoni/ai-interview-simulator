# services/humanizer/follow_up/follow_up_prompt_builder.py

from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer
from services.humanizer.follow_up.follow_up_prompt_input import FollowUpPromptInput

_TEMPLATE_PATH = "humanizer/follow_up_generation.txt"


class FollowUpPromptBuilder:
    """Collects follow-up context and delegates rendering to PromptRenderer.

    SRP: only responsibility is building the rendered prompt string.
    No LLM calls, no parsing, no validation logic.
    """

    def build(self, prompt_input: FollowUpPromptInput) -> str:
        template = PromptLoader.load(_TEMPLATE_PATH)
        context = {
            "question_area": prompt_input.question_area,
            "previous_question": prompt_input.previous_question,
            "previous_answer": prompt_input.previous_answer,
            "previous_feedback": prompt_input.previous_feedback,
            "candidate_level": prompt_input.candidate_level,
            "role": prompt_input.role,
            "seniority": prompt_input.seniority,
            "job_description": prompt_input.job_description,
            "company_description": prompt_input.company_description,
            "business_context": prompt_input.business_context,
            "follow_up_type": prompt_input.follow_up_type,
        }
        return PromptRenderer.render(template, context)
