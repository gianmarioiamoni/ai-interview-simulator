# domain/contracts/seniority_level.py

from enum import Enum


class SeniorityLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
