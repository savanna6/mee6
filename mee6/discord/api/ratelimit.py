import gevent
import redis
import time
import math

from mee6.utils import Logger
from gevent.lock import Semaphore

class Ratelimit(Logger):

    def __init__(self):
        self._lock = Semaphore()

    def get_route(route):
        raise NotImplemented

    def set_route(route, reset):
        raise NotImplemented

    def del_route(route):
        raise NotImplemented

    def check(self, route):
        with self._lock:
            reset = self.get_route(route) or self.get_route('global')

        if not reset: return

        sleep_time = math.floor(max(0, reset - time.time()))
        self.log('Bucket {} full, waiting {}s'.format(route, sleep_time))
        gevent.sleep(sleep_time + 0.1)

        with self._lock:
            self.del_route(route)
            self.del_route('global')

        return

    def update(self, route, r):
        remaining = r.headers.get('X-RateLimit-Remaining')
        if remaining == '0':
            with self._lock:
                self.set_route(route, int(r.headers.get('X-RateLimit-Reset', 0)))
        return

    def handle_429(self, route, r):
        payload = r.json()
        retry_after = math.ceil(payload['retry_after'] / 1000.)
        if payload['global']:
            with self._lock:
                self.set_route('global', math.ceil(time.time() + retry_after))
            self.log('Received 429: Bucket {} [GLOBAL RATELIMIT], waiting {}s'.format(route, retry_after))
        else:
            with self._lock:
                self.set_route(route, math.ceil(time.time() + retry_after))
            self.log('Received 429: Bucket {} full, waiting {}s'.format(route,
                                                                       retry_after))
        return retry_after

class LocalRatelimit(Ratelimit):
    def __init__(self):
        self.routes = {}
        super(LocalRatelimit, self).__init__()

    def get_route(self, route):
        return self.routes.get(route)

    def set_route(self, route, reset):
        self.routes[route] = reset

    def del_route(self, route):
        del self.routes[route]

class RedisRatelimit(Ratelimit):
    def __init__(self, redis_url):
        self.r = redis.from_url(redis_url, decode_responses=True)
        super(RedisRatelimit, self).__init__()

    def get_route(self, route):
        reset = self.r.get('Ratelimit.{}'.format(route))

        if reset is not None:
            return math.ceil(float(reset))
        else:
            return None

    def set_route(self, route, reset):
        return self.r.set('Ratelimit.{}'.format(route), reset)

    def del_route(self, route):
        return self.r.delete('Ratelimit.{}'.format(route))

