"""Development/seed data only.

This is NOT the final, authoritative Igbo curriculum -- it's a small,
hand-picked set of common, uncontroversial words/phrases (greetings, basic
courtesy, family terms) just enough to exercise the full curriculum ->
lesson -> exercise -> vocabulary schema end-to-end. The verified Igbo
knowledge system (Phase 1 principle: no confidently-invented vocabulary,
RAG-backed validation) is built in a later phase.

Run with: python -m app.scripts.seed
"""
import asyncio

from sqlalchemy import select

from app.core.db import async_session
from app.models import Exercise, GrammarTopic, Lesson, LessonObjective, Level, Unit, Vocabulary
from app.models.learner import LEVELS


async def seed() -> None:
    async with async_session() as db:
        existing = await db.execute(select(Level).limit(1))
        if existing.scalar_one_or_none() is not None:
            print("Seed data already present -- skipping.")
            return

        # All 7 proficiency stages exist as rows (so level-progression UI has
        # something real to show), but only Absolute Beginner gets actual
        # content -- "small but properly structured", not hundreds of lessons.
        level_rows = {
            code: Level(code=code, name=code.replace("_", " ").title(), order=i + 1)
            for i, code in enumerate(LEVELS)
        }
        db.add_all(level_rows.values())
        await db.flush()
        beginner = level_rows["absolute_beginner"]

        pronouns_topic = GrammarTopic(
            title="Personal Pronouns",
            description="Igbo personal pronouns (m/gị/ọ/anyị/unu/ha) and how they attach to verbs and nouns.",
            level_id=beginner.id,
        )
        db.add(pronouns_topic)
        await db.flush()

        # --- Unit 1: First Words -------------------------------------------------
        first_words = Unit(
            level_id=beginner.id,
            title="First Words",
            description="Greetings, courtesy, and introducing yourself",
            order=1,
        )
        db.add(first_words)
        await db.flush()

        greetings_lesson = Lesson(
            unit_id=first_words.id,
            title="Greetings & Introductions",
            order=1,
            content=(
                "Igbo greetings change with the time of day and the relationship between "
                "speakers, but \u201cNdewo\u201d works as a safe, friendly greeting in most "
                "situations. \u201cKedu\u201d (\u201chow are you\u201d) is the natural follow-up. "
                "Responses are usually short: \u201c\u1ecc d\u1ecb mma\u201d (it is fine/good)."
            ),
            examples=[
                {"igbo": "Ndewo!", "english": "Hello!"},
                {"igbo": "Kedu?", "english": "How are you?"},
                {"igbo": "\u1ecc d\u1ecb mma.", "english": "I'm fine / It is good."},
            ],
            grammar_topic_id=None,
        )
        db.add(greetings_lesson)
        await db.flush()

        db.add_all(
            [
                LessonObjective(lesson_id=greetings_lesson.id, description="Greet someone appropriately", order=1),
                LessonObjective(lesson_id=greetings_lesson.id, description="Ask and answer \u201chow are you\u201d", order=2),
                LessonObjective(lesson_id=greetings_lesson.id, description="Introduce yourself by name", order=3),
            ]
        )

        db.add_all(
            [
                Exercise(
                    lesson_id=greetings_lesson.id,
                    exercise_type="multiple_choice",
                    prompt="How do you say \u201cHello\u201d in Igbo?",
                    content={"options": ["Ndewo", "Daal\u1ee5", "Kedu", "Biko"], "correct_option": "Ndewo"},
                    explanation="\u201cNdewo\u201d is a general, friendly greeting used across most of the day.",
                    difficulty=0.2,
                    order=1,
                ),
                Exercise(
                    lesson_id=greetings_lesson.id,
                    exercise_type="fill_blank",
                    prompt="Aha ___ b\u1ee5 Ada. (My name is Ada.)",
                    content={"correct_answer": "m"},
                    explanation="\u201cm\u201d here is the possessive \u201cmy\u201d, attached after \u201caha\u201d (name).",
                    difficulty=0.4,
                    order=2,
                ),
                Exercise(
                    lesson_id=greetings_lesson.id,
                    exercise_type="translation",
                    prompt="Translate to English: \u201cKedu ka \u1ecb mere?\u201d",
                    content={"correct_answer": "How are you doing"},
                    explanation="A common, slightly more casual variant of \u201cKedu\u201d.",
                    difficulty=0.5,
                    order=3,
                ),
            ]
        )

        db.add_all(
            [
                Vocabulary(igbo_text="Ndewo", english_text="Hello", part_of_speech="interjection",
                           example_sentence="Ndewo, kedu ka \u1ecb mere?", category="greetings",
                           difficulty=0.1, level_id=beginner.id, lesson_id=greetings_lesson.id),
                Vocabulary(igbo_text="Nn\u1ecd\u1ecd", english_text="Welcome", part_of_speech="interjection",
                           category="greetings", difficulty=0.2, level_id=beginner.id, lesson_id=greetings_lesson.id),
                Vocabulary(igbo_text="Daal\u1ee5", english_text="Thank you", part_of_speech="interjection",
                           category="courtesy", difficulty=0.1, level_id=beginner.id, lesson_id=greetings_lesson.id),
                Vocabulary(igbo_text="Biko", english_text="Please", part_of_speech="interjection",
                           category="courtesy", difficulty=0.1, level_id=beginner.id, lesson_id=greetings_lesson.id),
                Vocabulary(igbo_text="Kedu", english_text="How / How are you", part_of_speech="phrase",
                           example_sentence="Kedu ka \u1ecb mere?", category="greetings",
                           difficulty=0.3, level_id=beginner.id, lesson_id=greetings_lesson.id),
                Vocabulary(igbo_text="Aha m b\u1ee5", english_text="My name is", part_of_speech="phrase",
                           category="introductions", difficulty=0.3, level_id=beginner.id, lesson_id=greetings_lesson.id),
            ]
        )

        # --- Unit 2: People & Family ----------------------------------------------
        people_family = Unit(
            level_id=beginner.id,
            title="People & Family",
            description="Talking about people, pronouns, and family terms",
            order=2,
        )
        db.add(people_family)
        await db.flush()

        family_lesson = Lesson(
            unit_id=people_family.id,
            title="Family Members",
            order=1,
            content=(
                "Family terms in Igbo often distinguish relative age and side of the "
                "family. \u201cNne\u201d (mother) and \u201cNna\u201d (father) are foundational; "
                "\u201cNwanne\u201d covers siblings generally, without specifying gender."
            ),
            examples=[
                {"igbo": "Nne m", "english": "My mother"},
                {"igbo": "Nna m", "english": "My father"},
                {"igbo": "Nwanne m", "english": "My sibling"},
            ],
            grammar_topic_id=pronouns_topic.id,
        )
        db.add(family_lesson)
        await db.flush()

        db.add_all(
            [
                LessonObjective(lesson_id=family_lesson.id, description="Name immediate family members", order=1),
                LessonObjective(lesson_id=family_lesson.id, description="Use possessive pronouns with family terms", order=2),
            ]
        )

        db.add_all(
            [
                Exercise(
                    lesson_id=family_lesson.id,
                    exercise_type="multiple_choice",
                    prompt="Which word means \u201cmother\u201d?",
                    content={"options": ["Nne", "Nna", "Nwanne", "Nwa"], "correct_option": "Nne"},
                    explanation="\u201cNne\u201d is mother; \u201cNna\u201d is father.",
                    difficulty=0.2,
                    order=1,
                ),
                Exercise(
                    lesson_id=family_lesson.id,
                    exercise_type="multiple_choice",
                    prompt="Which word means \u201csibling\u201d (without specifying gender)?",
                    content={"options": ["Nne", "Nna", "Nwanne", "Nwa"], "correct_option": "Nwanne"},
                    explanation="\u201cNwanne\u201d covers brothers and sisters alike; Igbo often doesn't specify gender here.",
                    difficulty=0.3,
                    order=2,
                ),
            ]
        )

        db.add_all(
            [
                Vocabulary(igbo_text="Nne", english_text="Mother", part_of_speech="noun",
                           category="family", difficulty=0.1, level_id=beginner.id, lesson_id=family_lesson.id),
                Vocabulary(igbo_text="Nna", english_text="Father", part_of_speech="noun",
                           category="family", difficulty=0.1, level_id=beginner.id, lesson_id=family_lesson.id),
                Vocabulary(igbo_text="Nwanne", english_text="Sibling", part_of_speech="noun",
                           category="family", difficulty=0.2, level_id=beginner.id, lesson_id=family_lesson.id),
                Vocabulary(igbo_text="Nwa", english_text="Child", part_of_speech="noun",
                           category="family", difficulty=0.2, level_id=beginner.id, lesson_id=family_lesson.id),
            ]
        )

        await db.commit()
        print(
            "Seeded: 7 levels, 2 units, 2 lessons, 5 exercises, 10 vocabulary items, "
            "1 grammar topic."
        )


if __name__ == "__main__":
    asyncio.run(seed())
