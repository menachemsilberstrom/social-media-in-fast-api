import pytest
from httpx import AsyncClient

from storeapi import security


async def create_post(
    body: dict,
    async_client: AsyncClient,
    logged_in_token: str,
) -> dict:
    response = await async_client.post(
        "/post",
        json=body,
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def create_comment(
    post_id: int, body: dict, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/comment",
        json=body,
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def like_post(
    post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/like",
        json={"post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str) -> dict:
    return await create_post(
        {"title": "Test Post", "description": "This is a test post."},
        async_client,
        logged_in_token,
    )


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    return await create_comment(
        created_post["id"],
        {"post_id": created_post["id"], "body": "This is a test comment."},
        async_client,
        logged_in_token,
    )


@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient, registered_user: dict, logged_in_token: str
):
    response = await async_client.post(
        "/post",
        json={
            "title": "Test Post",
            "description": "This is a test post.",
            "user_id": registered_user["id"],
        },
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201
    assert response.json()["id"] == 1


@pytest.mark.anyio
async def test_get_posts(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    response = await async_client.get(
        "/post", headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == created_post["id"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "sorting, expected_order",
    [
        ("new", [2, 1]),
        ("old", [1, 2]),
    ],
)
async def test_get_all_posts_sorting(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: int,
    expected_order: list[int],
):
    await create_post(
        {"title": "Test Post 1", "description": "This is a test post 1."},
        async_client,
        logged_in_token,
    )
    await create_post(
        {"title": "Test Post 2", "description": "This is a test post 2."},
        async_client,
        logged_in_token,
    )
    response = await async_client.get(
        "/post",
        headers={"Authorization": f"Bearer {logged_in_token}"},
        params={"sorting": sorting},
    )
    assert response.status_code == 200

    data = response.json()
    post_ids = [post["id"] for post in data]
    assert post_ids == expected_order


@pytest.mark.anyio
async def test_get_all_posts_sort_likes(
    async_client: AsyncClient,
    logged_in_token: str,
):
    await create_post(
        {"title": "Test Post 1", "description": "This is a test post 1."},
        async_client,
        logged_in_token,
    )
    await create_post(
        {"title": "Test Post 2", "description": "This is a test post 2."},
        async_client,
        logged_in_token,
    )
    await like_post(2, async_client, logged_in_token)
    response = await async_client.get(
        "/post",
        headers={"Authorization": f"Bearer {logged_in_token}"},
        params={"sorting": "most_likes"},
    )
    assert response.status_code == 200

    data = response.json()
    post_ids = [post["id"] for post in data]
    assert post_ids == [2, 1]


@pytest.mark.anyio
async def test_get_posts_wrong_sorting(async_client: AsyncClient, logged_in_token: str):
    response = await async_client.get(
        "/post",
        headers={"Authorization": f"Bearer {logged_in_token}"},
        params={"sorting": "invalid_sorting"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_post_without_description(
    async_client: AsyncClient, logged_in_token: str
):
    response = await async_client.post(
        "/post",
        json={"title": "Test Post"},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201


@pytest.mark.anyio
async def test_get_post_expired_token(
    async_client: AsyncClient, registered_user: dict, mocker
):
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    token = security.create_access_token(registered_user["email"])
    response = await async_client.get(
        "/post",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    registered_user: dict,
    logged_in_token: str,
):
    response = await async_client.post(
        "/comment",
        json={
            "post_id": created_post["id"],
            "body": "This is a test comment.",
            "user_id": registered_user["id"],
        },
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201
    assert response.json()["id"] == 1


@pytest.mark.anyio
async def test_create_comment_for_nonexistent_post(
    async_client: AsyncClient, logged_in_token: str
):
    response = await async_client.post(
        "/comment",
        json={"post_id": 999, "body": "This is a test comment."},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/post/{created_post['id']}")

    assert response.status_code == 200
    assert response.json() == {
        "post": {**created_post, "likes": 0},
        "comments": [created_comment],
    }
