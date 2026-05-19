# services/question_intelligence/fallback/retrieval_stage.py

from pydantic import BaseModel


class RetrievalStage(BaseModel):

    use_role: bool

    use_level: bool

    use_interview_type: bool

    use_area: bool

    model_config = {
        "frozen": True,
    }
