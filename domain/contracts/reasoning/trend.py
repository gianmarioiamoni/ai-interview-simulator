# domain/contracts/reasoning/trend.py

from enum import Enum


class Trend(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"
