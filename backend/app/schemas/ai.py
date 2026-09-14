import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


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
    hint: str | None = None
    example: str | None = None
    follow_up_question: str | None = None
    learning_action: str | None = None
    suggested_exercise: str | None = None
    language_level: str | None = None


class ConversationMessageOut(BaseModel):
    role: Literal["learner", "tutor"]
    content: str
    created_at: datetime


class ConversationHistoryOut(BaseModel):
    conversation_id: uuid.UUID
    messages: list[ConversationMessageOut]
