# domain/contracts/company_profile.py

# company profile contract
#
# - There is a predefined list of global IT companies
# - There is an option to add a custom company
# - The custom company is sanitized
# - There is no logic in the domain
# - The contract is strict

from enum import Enum
from pydantic import BaseModel, Field, model_validator


class CompanyType(str, Enum):
    GOOGLE = "google"
    AMAZON = "amazon"
    MICROSOFT = "microsoft"
    META = "meta"
    APPLE = "apple"
    NETFLIX = "netflix"
    OTHER = "other"


class CompanyProfile(BaseModel):
    type: CompanyType
    custom_name: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_custom_company(self) -> "CompanyProfile":
        if self.type == CompanyType.OTHER:
            if not self.custom_name:
                raise ValueError("custom_name required when company type is OTHER")
        else:
            if self.custom_name is not None:
                raise ValueError(
                    "custom_name must be None unless company type is OTHER"
                )

        return self

    model_config = {"frozen": True}
