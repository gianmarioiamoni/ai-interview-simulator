# domain/contracts/error_type.py

from enum import Enum


class ErrorType(str, Enum):
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    SIGNATURE = "signature"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"
