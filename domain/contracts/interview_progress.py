# domain/contracts/interview_progress.py

# Interview progress contract
#
# This contract defines the structure of an interview progress that can be used in the interview simulator.
# It is used to track the progress of an interview.
#
from enum import Enum


class InterviewProgress(str, Enum):
    SETUP = "setup"
    QUESTIONS_GENERATED = "questions_generated"
    IN_PROGRESS = "in_progress"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
