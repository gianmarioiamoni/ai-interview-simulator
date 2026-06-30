# domain/contracts/reasoning/data_sufficiency.py

from enum import Enum


class DataSufficiency(str, Enum):
    INSUFFICIENT = "insufficient"
    TENTATIVE = "tentative"
    CONFIDENT = "confident"
    STRONG = "strong"
