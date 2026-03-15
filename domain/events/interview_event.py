# domain/events/interview_event.py

from pydantic import BaseModel, Field
from datetime import datetime, timezone


class InterviewEvent(BaseModel):

    type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
