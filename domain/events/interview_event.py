# domain/events/interview_event.py

from pydantic import BaseModel
from datetime import datetime
from pytz import timezone


class InterviewEvent(BaseModel):

    type: str
    timestamp: datetime = datetime.now(timezone.utc)
