import gevent
import redis
import time
import math

from mee6.utils import Logger

class Ratelimit(Logger):
    def get_route(route):
        raise NotImplemented

    def set_route(route, reset):
        raise NotImplemented

    def del_route(route):
        raise NotImplemented

    def check(self, route):
        reset = self.get_route(route)
        if not reset: return

        sleep_time = math.floor(max(0, reset - time.time()))
        self.log('Bucket {} full, waiting {}s'.format(route, sleep_time))
        gevent.sleep(sleep_time)

        self.del_route(route)

        return

    def update(self, route, r):
        remaining = r.headers.get('X-RateLimit-Remaining')
        if remaining == '0':
            self.set_route(route, int(r.headers.get('X-RateLimit-Reset', 0)))
        return

class LocalRatelimit(Ratelimit):
    def __init__(self):
        self.routes = {}

    def get_route(self, route):
        return self.routes.get(route)

    def set_route(self, route, reset):
        self.routes[route] = reset

    def del_route(self, route):
        del self.routes[route]

class RedisRatelimit(Ratelimit):
    def __init__(self, redis_url):
        self.r = redis.from_url(redis_url, decode_responses=True)

    def get_route(self, route):
        reset = self.r.get('Ratelimit.{}'.format(route))

        if reset is not None:
            return int(reset)
        else:
            return None

    def set_route(self, route, reset):
        return self.r.set('Ratelimit.{}'.format(route), reset)

    def del_route(self, route):
        return self.r.delete('Ratelimit.{}'.format(route))

