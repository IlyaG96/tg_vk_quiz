import redis
from environs import Env
import json


def write_to_db(user, question):
    pass


def read_from_db(user, question):
    pass


def main():
    env = Env()
    env.read_env()
    host = env.str('REDIS_HOST')
    port = env.str('REDIS_PORT')
    password = env.str('REDIS_PASSWORD')
    base = redis.Redis(host=host,
                       port=port,
                       password=password,
                       decode_responses=True)

    data = {'question': 3}
    base.hset('quiz', 'player', json.dumps(data))
    player_info_string = (base.hget('quiz', 'player'))
    player_info_json = json.loads(player_info_string)




if __name__ == '__main__':
    main()