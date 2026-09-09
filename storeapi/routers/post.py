import logging

from fastapi import APIRouter, HTTPException

from storeapi.database import comment_table, database, post_table
from storeapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)

router = APIRouter()
logger = logging.getLogger(__name__)


async def find_post(post_id: int):
    logger.info(f"finding a post with id: {post_id}")
    query = post_table.select().where(post_table.c.id == post_id)
    logger.debug(query)
    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(post: UserPostIn):
    data = post.model_dump()
    query = post_table.insert().values(**data)
    last_record_id = await database.execute(query)
    logger.debug(query)
    logger.info("a new post was created..")
    return {**data, "id": last_record_id}


@router.get("/post", response_model=list[UserPost])
async def get_posts():
    logger.info("Getting all posts..")
    query = post_table.select()
    logger.debug(query)
    return await database.fetch_all(query)

@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(comment: CommentIn):
    post = await find_post(comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    logger.info(f"a new comment was created for post-id: {comment.post_id}")
    new_comment = comment.model_dump()
    query = comment_table.insert().values(**new_comment)
    logger.debug(query)
    last_record_id = await database.execute(query)
    return {**new_comment, "id": last_record_id}


@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_comments(post_id: int):
    post = await find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    logger.info(f"getting all comments for post-id {post_id}")
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    logger.debug(query)
    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    post = await find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    logger.info(f"Getting post and comments of post-id {post_id}")
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    logger.debug(query)
    comments = await database.fetch_all(query)
    return {
        "post": post,
        "comments": comments,
    }
                