# domain/contracts/role.py

# role contract
#
# - There are only technical IT roles
# - There is a predefined list
# - There is an option to add a custom role
# - It must be type-safe
# - It must be immutable

from enum import Enum
from pydantic import BaseModel, model_validator


# predefined roles
class RoleType(str, Enum):
    BACKEND_ENGINEER = "backend_engineer"
    FRONTEND_ENGINEER = "frontend_engineer"
    FULLSTACK_ENGINEER = "fullstack_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    DATA_ENGINEER = "data_engineer"
    ML_ENGINEER = "ml_engineer"
    QA_ENGINEER = "qa_engineer"
    OTHER = "other"

# role-specific statistical baseline for percentile modeling
ROLE_DISTRIBUTION: dict[RoleType, dict[str, float]] = {
    RoleType.BACKEND_ENGINEER: {"mean": 60.0, "std": 15.0},
    RoleType.FRONTEND_ENGINEER: {"mean": 62.0, "std": 14.0},
    RoleType.FULLSTACK_ENGINEER: {"mean": 63.0, "std": 14.0},
    RoleType.DEVOPS_ENGINEER: {"mean": 65.0, "std": 13.0},
    RoleType.DATA_ENGINEER: {"mean": 64.0, "std": 14.0},
    RoleType.ML_ENGINEER: {"mean": 68.0, "std": 12.0},
    RoleType.QA_ENGINEER: {"mean": 58.0, "std": 16.0},
    RoleType.OTHER: {"mean": 60.0, "std": 15.0},
}

# Ensure statistical model completeness
_missing = set(RoleType) - set(ROLE_DISTRIBUTION.keys())
if _missing:
    raise ValueError(f"Missing percentile distribution for roles: {_missing}")


class Role(BaseModel):
    type: RoleType
    custom_name: str | None = None



    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_custom_name(self) -> "Role":
        if self.type == RoleType.OTHER:
            if not self.custom_name:
                raise ValueError("custom_name required when role type is OTHER")
        else:
            if self.custom_name is not None:
                raise ValueError("custom_name must be None unless role type is OTHER")

        return self
