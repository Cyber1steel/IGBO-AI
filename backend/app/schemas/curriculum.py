import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# --- Curriculum (read-only content) -----------------------------------------
class LevelSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    name: str
    order: int


class UnitSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    description: str | None
    order: int
    lesson_count: int = 0


class LevelDetail(LevelSummary):
    units: list[UnitSummary] = []


class LessonSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    order: int


class UnitDetail(UnitSummary):
    lessons: list[LessonSummary] = []


class LessonObjectiveOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    description: str
    order: int


class VocabularyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    igbo_text: str
    english_text: str
    part_of_speech: str | None
    example_sentence: str | None
    category: str | None
    difficulty: float
    audio_url: str | None
    is_verified: bool


class ExercisePublicOut(BaseModel):
    """Exercise shape sent to the client BEFORE it's answered — the correct
    answer is deliberately stripped out (see schemas.curriculum.to_public)."""

    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    exercise_type: str
    prompt: str
    content: dict  # correct-answer keys already stripped by the router
    difficulty: float
    order: int


class LessonDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    order: int
    content: str | None
    examples: list
    unit_id: uuid.UUID
    objectives: list[LessonObjectiveOut] = []
    vocabulary: list[VocabularyOut] = []
    exercises: list[ExercisePublicOut] = []


# --- Learner-scoped progress -------------------------------------------------
class LessonProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    lesson_id: uuid.UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    score: float | None
    attempts: int


class ExerciseAttemptRequest(BaseModel):
    answer: str
    time_taken_seconds: int | None = None


class ExerciseAttemptResult(BaseModel):
    is_correct: bool
    correct_answer: str | None  # safe to reveal now — the attempt is graded
    explanation: str | None
    attempt_number: int


class VocabularyProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    vocabulary: VocabularyOut
    exposures_count: int
    correct_count: int
    incorrect_count: int
    mastery_score: float
    last_reviewed_at: datetime | None
