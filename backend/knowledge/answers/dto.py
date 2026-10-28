from pydantic import Field, field_validator
from knowledge.core.dto import DTO
from knowledge.conversations.dto import clean_text


class TurnRequest(DTO):
    question: str = Field(min_length=1, max_length=30000)
    request_id: str = Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9_.:-]+$')

    @field_validator('question')
    @classmethod
    def meaningful_question(cls, value):
        return clean_text(value)


class AnswerRequest(TurnRequest):
    conversation_id: str = Field(min_length=1, max_length=64)


class RetryRequest(DTO):
    request_id: str = Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9_.:-]+$')
