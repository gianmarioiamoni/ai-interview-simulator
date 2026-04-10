# domain/contracts/severity.py

from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    # -----------------------------------------------------
    # DOMAIN LOGIC (CRITICO)
    # -----------------------------------------------------

    def rank(self) -> int:
        return {
            Severity.ERROR: 0,
            Severity.WARNING: 1,
            Severity.INFO: 2,
        }[self]

    def weight(self) -> float:
        return {
            Severity.ERROR: 1.0,
            Severity.WARNING: 0.7,
            Severity.INFO: 0.5,
        }[self]
