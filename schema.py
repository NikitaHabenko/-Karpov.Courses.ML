import datetime
from pydantic import BaseModel
from typing import List


class UserGet(BaseModel):
    exp_group: int
    city: str
    id: int
    source: str
    gender: int
    country: str
    age: int
    os: str

    class Config:
        from_attributes = True


class PostGet(BaseModel):
    id: int
    text: str
    topic: str

    class Config:
        from_attributes = True


class Response(BaseModel):
    exp_group: str
    recommendations: List[PostGet]


class FeedGet(BaseModel):
    action: str
    post_id: int
    time: datetime.datetime
    user_id: int
    post: PostGet
    user: UserGet

    class Config:
        from_attributes = True
