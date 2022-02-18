import redis
from environs import Env


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

    base.set('foo', 'bar')
    print(base.get('foo'))


if __name__ == '__main__':
    main()