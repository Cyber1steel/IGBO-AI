from httpx import AsyncClient


async def _register(client: AsyncClient, email="ada@example.com", password="igbo1234", name="Ada"):
    resp = await client.post(
        "/auth/register", json={"email": email, "password": password, "display_name": name}
    )
    assert resp.status_code == 201
    return resp.json()


async def test_login_succeeds_with_correct_credentials(client: AsyncClient):
    await _register(client)
    resp = await client.post("/auth/login", json={"email": "ada@example.com", "password": "igbo1234"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_fails_with_wrong_password(client: AsyncClient):
    await _register(client)
    resp = await client.post("/auth/login", json={"email": "ada@example.com", "password": "wrongpass1"})
    assert resp.status_code == 401


async def test_login_fails_for_unknown_email(client: AsyncClient):
    resp = await client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever1"})
    assert resp.status_code == 401


async def test_protected_route_requires_token(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_protected_route_rejects_garbage_token(client: AsyncClient):
    resp = await client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


async def test_me_returns_authenticated_users_own_data(client: AsyncClient):
    body = await _register(client, email="me@example.com", name="Me")
    token = body["access_token"]

    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


async def test_refresh_issues_a_valid_token_and_rotates_the_refresh_cookie(client: AsyncClient):
    await _register(client)
    await client.post("/auth/login", json={"email": "ada@example.com", "password": "igbo1234"})
    old_refresh_cookie = client.cookies.get("igboai_refresh_token")

    refresh = await client.post("/auth/refresh")
    assert refresh.status_code == 200
    assert "access_token" in refresh.json()

    new_refresh_cookie = client.cookies.get("igboai_refresh_token")
    assert new_refresh_cookie != old_refresh_cookie  # rotated, not reused

    # The old (pre-rotation) refresh token must now be rejected if replayed.
    client.cookies.set("igboai_refresh_token", old_refresh_cookie)
    replay = await client.post("/auth/refresh")
    assert replay.status_code == 401


async def test_refresh_fails_without_cookie(client: AsyncClient):
    resp = await client.post("/auth/refresh")
    assert resp.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient):
    await _register(client)
    await client.post("/auth/login", json={"email": "ada@example.com", "password": "igbo1234"})

    logout_resp = await client.post("/auth/logout")
    assert logout_resp.status_code == 204

    refresh_after_logout = await client.post("/auth/refresh")
    assert refresh_after_logout.status_code == 401
