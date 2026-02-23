# domain/contracts/interview_area.py

# interview area contract
#
# - There are 2 types of interviews: HR and Technical
# - Each type has exactly 5 areas
# - Each area is associated with a type
# - It must be immutable
# - It must be validable

from enum import Enum
from pydantic import BaseModel, Field


class InterviewType(str, Enum):
    HR = "hr"
    TECHNICAL = "technical"


class InterviewArea(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    interview_type: InterviewType

    model_config = {"frozen": True}
