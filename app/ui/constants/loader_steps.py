# app/ui/constants/loader_steps.py

from enum import Enum


class LoaderStep(str, Enum):
    GENERATING_STRUCTURE = "GENERATING_STRUCTURE"
    GENERATING_QUESTIONS = "GENERATING_QUESTIONS"
    GENERATING_TESTS = "GENERATING_TESTS"
    FINALIZING = "FINALIZING"
