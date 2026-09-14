import uuid
from typing import Literal

from pydantic import BaseModel


class TutorMessageSchema(BaseModel):
    role: Literal["learner", "tutor"]
    content: str


class TutorRequest(BaseModel):
    message: str
    # Optional: which conversation this continues. Omit to start a new one.
    conversation_id: uuid.UUID | None = None
    # Optional: which lesson the learner is currently in, used to build
    # relevant context (see app/services/tutor_context.py). Purely
    # informational — never required.
    lesson_id: uuid.UUID | None = None


class TutorResponse(BaseModel):
    conversation_id: uuid.UUID
    message: str
    provider: str
    correction: str | None = None
    explanation: str | None = None
    suggested_exercise: str | None = None
    language_level: str | None = None
