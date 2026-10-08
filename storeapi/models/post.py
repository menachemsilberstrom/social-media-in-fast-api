from pydantic import BaseModel


class UserPostIn(BaseModel):
    title: str
    description: str


class UserPost(UserPostIn):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class CommentIn(BaseModel):
    body: str
    post_id: int


class Comment(CommentIn):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class UserPostWithComments(BaseModel):
    post: UserPost
    comments: list[Comment]

class PostLikeIn(BaseModel):
    post_id: int

class PostLike(PostLikeIn):
    id: int
    user_id: int


