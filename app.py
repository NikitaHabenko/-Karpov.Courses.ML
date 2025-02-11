from sqlalchemy.orm import Session
from database import SessionLocal
from sqlalchemy.orm.exc import NoResultFound
from table_feed import Post, User, Feed
from schema import UserGet, PostGet, FeedGet, Response
from fastapi import Depends, FastAPI, HTTPException
import os
from typing import List

import pandas as pd
from catboost import CatBoostClassifier
from sqlalchemy import create_engine
import hashlib
import logging

def get_model_path(path: str, exp_group: str) -> str:
    if os.environ.get("IS_LMS") == "1":
        if exp_group == 'control':
            MODEL_PATH = '/workdir/user_input/model_control'
        else:
            MODEL_PATH = '/workdir/user_input/model_test'
    else:
        MODEL_PATH = path
    return MODEL_PATH

def load_model_control():
    model_path = get_model_path("D:/karpov_ml/2_ml/ml_lesson_22_final_project_recs/control_model", 'control')
    from_file = CatBoostClassifier()
    model = from_file.load_model(model_path)
    return model

def load_model_test():
    model_path = get_model_path("D:/karpov_ml/2_ml/ml_lesson_22_final_project_recs/test_model", 'test')
    from_file = CatBoostClassifier()
    model = from_file.load_model(model_path)
    return model


def batch_load_sql(query: str) -> pd.DataFrame:
    CHUNKSIZE = 200000
    engine = create_engine(
        "postgresql://robot-startml-ro:pheiph0hahj1Vaif@"
        "postgres.lab.karpov.courses:6432/startml"
    )
    conn = engine.connect().execution_options(stream_results=True)
    chunks = []
    for chunk_dataframe in pd.read_sql(query, conn, chunksize=CHUNKSIZE):
        chunks.append(chunk_dataframe)
    conn.close()
    return pd.concat(chunks, ignore_index=True)


def load_features() -> pd.DataFrame:
    user_data = batch_load_sql('SELECT * FROM n_habenko_14_users_lesson_22')
    return user_data


def load_post_features() -> pd.DataFrame:
    post_data = batch_load_sql('SELECT * FROM n_habenko_14_posts_lesson_22')
    return post_data


def load_posts() -> pd.DataFrame:
    posts = batch_load_sql('SELECT * FROM public.post_text_df')
    return posts

salt = 'salt_2025'
def get_exp_group(user_id: int) -> str:
    value_str = str(user_id) + salt
    value_num = int(hashlib.md5(value_str.encode()).hexdigest(), 16)
    if value_num % 100 <= 50:
        return 'control'
    else:
        return 'test'




user_data = load_features()
user_data = user_data.drop('index', axis=1)

post_data = load_post_features()
post_data = post_data.drop('index', axis=1)

posts = load_posts()



app = FastAPI()

def get_db():
    with SessionLocal() as db:
        return db


@app.get('/user/{id}', response_model=UserGet)
def get_id(id: int, db: Session = Depends(get_db)):
    try:
        result = db.query(User).filter(User.id == id).one()
        return result
    except NoResultFound:
        raise HTTPException(404)


@app.get('/post/{id}', response_model=PostGet)
def get_post(id: int, db: Session = Depends(get_db)):
    try:
        result = db.query(Post).filter(Post.id == id).one()
        return result
    except NoResultFound:
        raise HTTPException(404)


@app.get('/user/{id}/feed', response_model=List[FeedGet])
def get_feed_by_user(id: int, db: Session = Depends(get_db), limit: int = 10):
    result = db.query(Feed).filter(Feed.user_id == id).order_by(Feed.time.desc()).limit(limit).all()
    return result

@app.get('/post/{id}/feed', response_model=List[FeedGet])
def get_feed_by_post(id: int, db: Session = Depends(get_db), limit: int = 10):
    result = db.query(Feed).filter(Feed.post_id == id).order_by(Feed.time.desc()).limit(limit).all()
    return result


@app.get("/post/recommendations/", response_model=Response)   #List[Response]
def recommended_posts(id: int) -> Response:  #List[Response]
    exp_group = get_exp_group(id)
    if exp_group == 'control':
        model = load_model_control()
    elif exp_group == 'test':
        model = load_model_test()
    else:
        raise ValueError('unknown group')
    logging.info(exp_group)

    data = user_data[user_data['user_id'] == id].merge(post_data, how='cross').drop(['user_id', 'post_id'], axis=1)
    predictions = pd.DataFrame()
    predictions['predict_proba'] = model.predict_proba(data)[:, 1]
    predictions['post_id'] = posts['post_id']
    predictions['text'] = posts['text']
    predictions['topic'] = posts['topic']
    result = predictions.sort_values(by='predict_proba', ascending=False).head(5)

    post_get_list = []

    for index, row in result.iterrows():
        post_id = row['post_id']
        data = row.drop('post_id').to_dict()
        post_get = PostGet(id=post_id, **data)
        post_get_list.append(post_get)

    return  Response(exp_group=exp_group, recommendations=post_get_list)

