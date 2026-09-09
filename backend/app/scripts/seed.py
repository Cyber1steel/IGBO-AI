"""Development/seed data only.

This is NOT the final, authoritative Igbo curriculum — it's a small,
hand-picked set of common, uncontroversial words/phrases (greetings, basic
courtesy) just enough to exercise the schema end-to-end. The verified Igbo
knowledge system (Phase 1 principle: no confidently-invented vocabulary,
RAG-backed validation) is built in a later phase.

Run with: python -m app.scripts.seed
"""
import asyncio

from sqlalchemy import select

from app.core.db import async_session
from app.models import Exercise, Lesson, Level, Unit, Vocabulary


async def seed() -> None:
    async with async_session() as db:
        existing = await db.execute(select(Level).limit(1))
        if existing.scalar_one_or_none() is not None:
            print("Seed data already present — skipping.")
            return

        beginner = Level(code="absolute_beginner", name="Absolute Beginner", order=1)
        elementary = Level(code="beginner", name="Beginner", order=2)
        db.add_all([beginner, elementary])
        await db.flush()

        first_words = Unit(
            level_id=beginner.id,
            title="First Words",
            description="Greetings, courtesy, and introducing yourself",
            order=1,
        )
        db.add(first_words)
        await db.flush()

        greetings_lesson = Lesson(unit_id=first_words.id, title="Greetings & Introductions", order=1)
        db.add(greetings_lesson)
        await db.flush()

        db.add_all(
            [
                Exercise(
                    lesson_id=greetings_lesson.id,
                    exercise_type="multiple_choice",
                    prompt="How do you say \u201cGood morning / Hello\u201d in Igbo?",
                    content={
                        "options": ["Ndewo", "Daalụ", "Kedu", "Biko"],
                        "correct_option": "Ndewo",
                    },
                    order=1,
                ),
                Exercise(
                    lesson_id=greetings_lesson.id,
                    exercise_type="fill_blank",
                    prompt="Aha ___ bụ Ada. (My name is Ada.)",
                    content={"correct_answer": "m"},
                    order=2,
                ),
            ]
        )

        db.add_all(
            [
                Vocabulary(igbo_text="Ndewo", english_text="Hello", part_of_speech="interjection", level_id=beginner.id),
                Vocabulary(igbo_text="Nnọọ", english_text="Welcome", part_of_speech="interjection", level_id=beginner.id),
                Vocabulary(igbo_text="Daalụ", english_text="Thank you", part_of_speech="interjection", level_id=beginner.id),
                Vocabulary(igbo_text="Biko", english_text="Please", part_of_speech="interjection", level_id=beginner.id),
                Vocabulary(igbo_text="Kedu", english_text="How are you", part_of_speech="phrase", level_id=beginner.id),
                Vocabulary(igbo_text="Aha m bụ", english_text="My name is", part_of_speech="phrase", level_id=beginner.id),
            ]
        )

        await db.commit()
        print("Seeded: 2 levels, 1 unit, 1 lesson, 2 exercises, 6 vocabulary items.")


if __name__ == "__main__":
    asyncio.run(seed())
