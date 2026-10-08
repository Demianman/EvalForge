from redis import Redis
from rq import Queue, Worker
from .config import settings


def main():
    connection = Redis.from_url(settings.redis_url)
    Worker([Queue("evaluations", connection=connection)], connection=connection).work()


if __name__ == "__main__": main()
