# domain/contracts/interview_state/init.py

from .base import InterviewStateBase
from .results import InterviewStateResultsMixin
from .progress import InterviewStateProgressMixin
from .events import InterviewStateEventsMixin
from .computed import InterviewStateComputedMixin
from .validation import InterviewStateValidationMixin
from .factory import InterviewStateFactoryMixin


class InterviewState(
    InterviewStateBase,
    InterviewStateResultsMixin,
    InterviewStateProgressMixin,
    InterviewStateEventsMixin,
    InterviewStateComputedMixin,
    InterviewStateValidationMixin,
    InterviewStateFactoryMixin,
):
    pass
