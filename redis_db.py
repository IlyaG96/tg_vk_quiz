import redis
from environs import Env


def write_question_db(base, user, question_num):

    base.hset(user, 'question_num', question_num)


def read_question_db(base, user):

    question_num = (base.hget(user, 'question_num'))
    return question_num


def write_scores_db(base, user, score):

    base.hset(user, 'scores', score)


def read_scores_db(base, user):

    scores = (base.hget(user, 'scores'))
    return scores


def run_base():
    env = Env()
    env.read_env()
    host = env.str('REDIS_HOST')
    port = env.str('REDIS_PORT')
    password = env.str('REDIS_PASSWORD')
    redis_base = redis.Redis(host=host,
                             port=port,
                             password=password,
                             decode_responses=True)

    return redis_base

