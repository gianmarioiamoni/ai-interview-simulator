# domain/contracts/answer.py

# Answer contract
#
# This contract defines the structure of an answer that can be used in the interview simulator.
# It is used to store the answer in the database and to retrieve it when needed.
#
# The answer is associated with a question and contains the candidate's response.
# The answer also contains the attempt number, which is used to track the number of attempts the candidate has made to answer the question.
#
# Responsability: represents a frozen and immutable answer in time.

from pydantic import BaseModel, Field


class Answer(BaseModel):
    question_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)

    # useful for follow-up tracking
    attempt: int = Field(..., ge=1)

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
