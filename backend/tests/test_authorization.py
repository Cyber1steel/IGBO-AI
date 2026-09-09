from httpx import AsyncClient


async def _register_and_get_token(client: AsyncClient, email: str, name: str) -> str:
    resp = await client.post(
        "/auth/register", json={"email": email, "password": "igbo1234", "display_name": name}
    )
    return resp.json()["access_token"]


async def test_learner_can_read_own_profile(client: AsyncClient):
    token = await _register_and_get_token(client, "ada@example.com", "Ada")
    resp = await client.get("/learners/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Ada"


async def test_two_learners_get_their_own_distinct_profiles(client: AsyncClient):
    ada_token = await _register_and_get_token(client, "ada@example.com", "Ada")
    obi_token = await _register_and_get_token(client, "obi@example.com", "Obi")

    ada_profile = await client.get("/learners/me", headers={"Authorization": f"Bearer {ada_token}"})
    obi_profile = await client.get("/learners/me", headers={"Authorization": f"Bearer {obi_token}"})

    assert ada_profile.json()["display_name"] == "Ada"
    assert obi_profile.json()["display_name"] == "Obi"


async def test_update_profile_only_affects_own_profile(client: AsyncClient):
    ada_token = await _register_and_get_token(client, "ada@example.com", "Ada")
    obi_token = await _register_and_get_token(client, "obi@example.com", "Obi")

    await client.patch(
        "/learners/me",
        json={"learning_goal": "Speak with grandma fluently"},
        headers={"Authorization": f"Bearer {ada_token}"},
    )

    obi_profile = await client.get("/learners/me", headers={"Authorization": f"Bearer {obi_token}"})
    assert obi_profile.json()["learning_goal"] is None  # untouched by Ada's update


async def test_there_is_no_route_to_fetch_another_learners_profile_by_id(client: AsyncClient):
    # The API never accepts a learner/user id from the client for these
    # routes — ownership is structural, not just checked. Confirm no such
    # parametrized route exists.
    token = await _register_and_get_token(client, "ada@example.com", "Ada")
    resp = await client.get(
        "/learners/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404  # no matching route, not a data leak
