import pytest
from httpx import AsyncClient


async def create_post(body: dict, async_client: AsyncClient):
    response = await async_client.post("/post", json=body)
    return response.json()


async def create_comment(post_id: int, body: dict, async_client: AsyncClient):
    response = await async_client.post("/comment", json=body)
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient):
    return await create_post(
        {"title": "Test Post", "description": "This is a test post."},
        async_client,
    )


@pytest.fixture()
async def created_comment(async_client: AsyncClient, created_post: dict):
    return await create_comment(
        created_post["id"],
        {"post_id": created_post["id"], "body": "This is a test comment."},
        async_client,
    )


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient):
    response = await async_client.post(
        "/post", json={"title": "Test Post", "description": "This is a test post."}
    )
    assert response.status_code == 201
    assert response.json()["id"] == 1

@pytest.mark.anyio
async def test_get_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/post")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == created_post["id"]

@pytest.mark.anyio
async def test_create_post_without_description(async_client: AsyncClient):
    response = await async_client.post("/post", json={"title": "Test Post"})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_comment(async_client: AsyncClient, created_post: dict):
    response = await async_client.post(
        "/comment",
        json={"post_id": created_post["id"], "body": "This is a test comment."},
    )
    assert response.status_code == 201
    assert response.json()["id"] == 1


@pytest.mark.anyio
async def test_create_comment_for_nonexistent_post(async_client: AsyncClient):
    response = await async_client.post(
        "/comment", json={"post_id": 999, "body": "This is a test comment."}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/post/{created_post['id']}")
    assert response.status_code == 200
    assert response.json()["post"]["id"] == created_post["id"]
    assert len(response.json()["comments"]) == 1
    assert response.json()["comments"][0]["id"] == created_comment["id"]
