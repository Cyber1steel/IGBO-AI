from pydantic import BaseModel
from typing import Literal


class TutorMessageSchema(BaseModel):
    role: Literal["learner", "tutor"]
    content: str


class TutorRequest(BaseModel):
    history: list[TutorMessageSchema] = []
    message: str


class TutorResponse(BaseModel):
    message: str
    provider: str
