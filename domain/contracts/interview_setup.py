# domain/contracts/interview_setup.py

# - There are 2 types of interviews: HR and Technical
# - Each type has exactly 5 areas (not here, but linked)
# - There are predefined roles + Other
# - There are predefined companies + Other
# - The default language is English, dynamic adaptation
# - Only technical IT roles
# - The setup must not contain:
#   - questions
#   - runtime state
#   - score
#   - evaluation
# It is pure configuration input.


from pydantic import BaseModel, Field

from domain.contracts.role import Role
from domain.contracts.company_profile import CompanyProfile
from domain.contracts.interview_area import InterviewType


class InterviewSetup(BaseModel):
    interview_type: InterviewType
    role: Role
    company: CompanyProfile
    language: str = Field(default="en", min_length=2, max_length=5)

    model_config = {"frozen": True}
