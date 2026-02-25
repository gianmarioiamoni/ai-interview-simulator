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
