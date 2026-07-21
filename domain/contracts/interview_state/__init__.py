# domain/contracts/interview_state/init.py

from .base import InterviewStateBase
from .results import InterviewStateResultsMixin
from .question_results import InterviewStateQuestionResultsMixin
from .events import InterviewStateEventsMixin
from .computed import InterviewStateComputedMixin
from .factory import InterviewStateFactoryMixin


class InterviewState(
    InterviewStateBase,
    InterviewStateResultsMixin,
    InterviewStateQuestionResultsMixin,
    InterviewStateEventsMixin,
    InterviewStateComputedMixin,
    InterviewStateFactoryMixin,
):
    pass


__all__ = ["InterviewState"]
