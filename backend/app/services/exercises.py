"""Exercise grading and content projection.

Deliberately NOT AI-based: whether an answer is correct is application logic
against curated content, not something N-ATLaS decides (see Phase 1/4
architecture principle: Curriculum -> Lesson -> Exercise -> Learner
Performance -> Mastery, with the AI kept out of the grading path).
"""
from app.models import Exercise

# Any content key starting with one of these is answer-key material and must
# never reach the client before an exercise is attempted.
_ANSWER_KEY_PREFIXES = ("correct",)


def strip_answer_key(content: dict) -> dict:
    return {k: v for k, v in content.items() if not k.startswith(_ANSWER_KEY_PREFIXES)}


def to_public_exercise(exercise: Exercise):
    from app.schemas.curriculum import ExercisePublicOut  # local import avoids a circular import

    return ExercisePublicOut(
        id=exercise.id,
        exercise_type=exercise.exercise_type,
        prompt=exercise.prompt,
        content=strip_answer_key(exercise.content),
        difficulty=exercise.difficulty,
        order=exercise.order,
    )


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def grade_answer(exercise: Exercise, answer: str) -> tuple[bool, str | None]:
    """Returns (is_correct, human-readable correct answer for feedback)."""
    content = exercise.content
    submitted = _normalize(answer)

    if "correct_option" in content:
        correct = content["correct_option"]
        return submitted == _normalize(correct), correct

    if "correct_answer" in content:
        correct = content["correct_answer"]
        return submitted == _normalize(correct), correct

    if "correct_answers" in content:
        options = content["correct_answers"]
        is_correct = submitted in {_normalize(o) for o in options}
        return is_correct, " / ".join(options)

    if "correct_order" in content:
        correct = content["correct_order"]
        # Learner submits items comma-separated in their chosen order.
        submitted_order = [_normalize(p) for p in answer.split(",")]
        correct_order = [_normalize(p) for p in correct]
        return submitted_order == correct_order, ", ".join(correct)

    # Content without a recognizable answer key can't be auto-graded — this
    # is a content-authoring bug, not a learner error, so fail closed.
    return False, None
