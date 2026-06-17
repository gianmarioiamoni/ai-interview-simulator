# domain/contracts/question/sql_domain.py

from enum import Enum


class SqlDomain(str, Enum):
    TECHNICAL_DATABASE = "technical_database"
    JOIN = "join"
    GROUP_BY = "group_by"
    HAVING = "having"
    EXISTS = "exists"
    INDEXING = "indexing"
    PERFORMANCE = "performance"
    CTE = "cte"
    RECURSIVE_CTE = "recursive_cte"
    TRANSACTION = "transaction"
    ACID = "acid"
    NORMALIZATION = "normalization"
    DATA_MODELING = "data_modeling"
    UNION = "union"
    INTERSECT = "intersect"
    EXCEPT = "except"
    CORRELATED_SUBQUERY = "correlated_subquery"
    WINDOW_FUNCTION = "window_function"
