import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models import LearnerProfile, User


def test_hash_password_never_returns_plaintext():
    hashed = hash_password("correct horse battery")
    assert hashed != "correct horse battery"
    assert hashed.startswith("$2b$")  # bcrypt identifier


def test_verify_password_round_trip():
    hashed = hash_password("correct horse battery")
    assert verify_password("correct horse battery", hashed) is True
    assert verify_password("wrong password", hashed) is False


async def test_register_creates_user_and_learner_profile(client: AsyncClient, db_session: AsyncSession):
    resp = await client.post(
        "/auth/register",
        json={"email": "ada@example.com", "password": "igbo1234", "display_name": "Ada"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["email"] == "ada@example.com"
    assert "access_token" in body

    user = (await db_session.execute(select(User).where(User.email == "ada@example.com"))).scalar_one()
    assert user.password_hash != "igbo1234"  # never stored in plaintext

    profile = (
        await db_session.execute(select(LearnerProfile).where(LearnerProfile.user_id == user.id))
    ).scalar_one_or_none()
    assert profile is not None
    assert profile.display_name == "Ada"
    assert profile.current_level == "absolute_beginner"


async def test_register_rejects_duplicate_email(client: AsyncClient):
    payload = {"email": "dupe@example.com", "password": "igbo1234", "display_name": "First"}
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/auth/register", json={**payload, "display_name": "Second"})
    assert second.status_code == 400


@pytest.mark.parametrize(
    "password",
    ["short1", "alllettersnodigits", "12345678"],
)
async def test_register_rejects_weak_passwords(client: AsyncClient, password: str):
    resp = await client.post(
        "/auth/register",
        json={"email": "weak@example.com", "password": password, "display_name": "Weak"},
    )
    assert resp.status_code == 422
