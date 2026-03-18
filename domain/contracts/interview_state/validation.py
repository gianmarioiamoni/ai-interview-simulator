# domain/contracts/interview_state/validation.py

from pydantic import model_validator

from domain.contracts.interview_progress import InterviewProgress


class InterviewStateValidationMixin:

    @model_validator(mode="after")
    def validate_progress_consistency(self):

        if self.progress == InterviewProgress.COMPLETED:
            if not self.results_by_question:
                raise ValueError("Cannot complete interview without results")

        return self
