# domain/contracts/interview_state/init.py

from .base import InterviewStateBase
from .results import InterviewStateResultsMixin
from .progress import InterviewStateProgressMixin
from .events import InterviewStateEventsMixin
from .computed import InterviewStateComputedMixin
from .factory import InterviewStateFactoryMixin


class InterviewState(
    InterviewStateBase,
    InterviewStateResultsMixin,
    InterviewStateProgressMixin,
    InterviewStateEventsMixin,
    InterviewStateComputedMixin,
    InterviewStateFactoryMixin,
):
    pass


__all__ = ["InterviewState"]
