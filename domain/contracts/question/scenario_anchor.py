# domain/contracts/question/scenario_anchor.py

from enum import Enum


class ScenarioAnchor(str, Enum):
    REPORTING = "reporting"
    OPTIMIZATION = "optimization"
    TROUBLESHOOTING = "troubleshooting"
    DATA_QUALITY = "data_quality"
    ANTI_PATTERN = "anti_pattern"
    DML_PATTERN = "dml_pattern"
