import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Level(UUIDPKMixin, TimestampMixin, Base):
    """One of the 7 proficiency stages (see learner.LEVELS)."""

    __tablename__ = "levels"

    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    units: Mapped[list["Unit"]] = relationship(back_populates="level", order_by="Unit.order")


class Unit(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "units"

    level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("levels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    level: Mapped["Level"] = relationship(back_populates="units")
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="unit", order_by="Lesson.order")


class Lesson(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "lessons"

    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    # Teaching content shown in the "Learn" step of the lesson flow.
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Short list of example sentences/phrases shown in the "Examples" step.
    # e.g. [{"igbo": "...", "english": "..."}] — kept as JSONB rather than a
    # separate table since examples are lesson-owned, ordered, and never
    # queried independently.
    examples: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    grammar_topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grammar_topics.id", ondelete="SET NULL"), nullable=True, index=True
    )

    unit: Mapped["Unit"] = relationship(back_populates="lessons")
    objectives: Mapped[list["LessonObjective"]] = relationship(
        back_populates="lesson", order_by="LessonObjective.order"
    )
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="lesson", order_by="Exercise.order")
    vocabulary: Mapped[list["Vocabulary"]] = relationship(back_populates="lesson")
    grammar_topic: Mapped["GrammarTopic | None"] = relationship()


class LessonObjective(UUIDPKMixin, Base):
    __tablename__ = "lesson_objectives"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    lesson: Mapped["Lesson"] = relationship(back_populates="objectives")


class Exercise(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "exercises"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # e.g. "multiple_choice" | "fill_blank" | "translation" | "matching" |
    # "ordering" — plain string, not a DB enum, so new types need no migration
    exercise_type: Mapped[str] = mapped_column(String(30), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # Options / correct answer(s) — shape varies by exercise_type. Never sent
    # to the client as-is; see schemas/curriculum.py's public projection.
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # 0-1
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    lesson: Mapped["Lesson"] = relationship(back_populates="exercises")


class Assessment(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "assessments"

    unit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("units.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    passing_score: Mapped[int] = mapped_column(Integer, default=70, nullable=False)


class Vocabulary(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "vocabulary"

    igbo_text: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    english_text: Mapped[str] = mapped_column(String(120), nullable=False)
    part_of_speech: Mapped[str | None] = mapped_column(String(30), nullable=True)
    example_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    difficulty: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)  # 0-1
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    level_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("levels.id", ondelete="SET NULL"), nullable=True, index=True
    )
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True, index=True
    )
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Verified-source flag: Phase 1 principle that Igbo content must not be
    # confidently invented. Seed/curated entries are marked verified=True;
    # anything generated later must be reviewed before this flips.
    is_verified: Mapped[bool] = mapped_column(default=True, nullable=False)

    lesson: Mapped["Lesson | None"] = relationship(back_populates="vocabulary")


class GrammarTopic(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "grammar_topics"

    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    level_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("levels.id", ondelete="SET NULL"), nullable=True, index=True
    )
