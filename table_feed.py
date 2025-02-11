from database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship


class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)
    text = Column(String)
    topic = Column(String)


class User(Base):
    __tablename__ = "user"
    age = Column(Integer)
    city = Column(String)
    country = Column(String)
    exp_group = Column(Integer)
    gender = Column(Integer)
    id = Column(Integer, primary_key=True)
    os = Column(String)
    source = Column(String)


class Feed(Base):
    __tablename__ = 'feed_action'
    action = Column(String)
    post_id = Column(
        Integer, ForeignKey("post.id"), primary_key=True
    )
    post = relationship("Post", uselist=False)
    time = Column(DateTime, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("user.id"), primary_key=True
    )
    user = relationship("User")