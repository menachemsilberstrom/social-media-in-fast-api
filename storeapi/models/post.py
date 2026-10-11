from pydantic import BaseModel, ConfigDict


class UserPostIn(BaseModel):
    title: str
    description: str


class UserPost(UserPostIn):
    id: int
    user_id: int
    image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserPostWithLikes(UserPost):
    likes: int

    model_config = ConfigDict(from_attributes=True)


class CommentIn(BaseModel):
    body: str
    post_id: int


class Comment(CommentIn):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class UserPostWithComments(BaseModel):
    post: UserPostWithLikes
    comments: list[Comment]


class PostLikeIn(BaseModel):
    post_id: int


class PostLike(PostLikeIn):
    id: int
    user_id: int
