import requests
import logging
import gevent
import os

from mee6.utils import Logger
from mee6.discord.api.ratelimit import LocalRatelimit, RedisRatelimit
from mee6.exceptions import APIException

logging.getLogger('requests').setLevel(logging.WARNING)


class HTTPClient(Logger):

    BASE_URL = 'https://discordapp.com/api/v6'
    RATELIMIT_REDIS_URL = os.getenv('RATELIMIT_REDIS_URL')

    def __init__(self, token):
        self.token = token

        if self.RATELIMIT_REDIS_URL:
            self.ratelimit = RedisRatelimit(self.RATELIMIT_REDIS_URL)
        else:
            self.ratelimit = LocalRatelimit()

    def build_url(self, route): return self.BASE_URL + '/' + route

    def __call__(self, method, route, auth=True, **kwargs):
        url = self.build_url(route)

        self.ratelimit.check(route)

        headers = dict()
        if auth:
            headers['Authorization'] = 'Bot ' + self.token

        r = requests.request(method, url, headers=headers, **kwargs)

        self.ratelimit.update(route, r)

        if r.status_code < 400:
            return r

        if r.status_code != 429 and 400 <= r.status_code < 500:
            raise APIException(r)

        if r.status_code == 429:
            gevent.sleep(self.ratelimit.handle_429(route, r))
            return self.__call__(method, route, **kwargs)
        else:
            raise APIException(r)

    def get(self, route, **kwargs): return self('GET', route, **kwargs)

    def post(self, route, **kwargs): return self('POST', route, **kwargs)

    def put(self, route, **kwargs): return self('PUT', route, **kwargs)

    def patch(self, route, **kwargs): return self('PATCH', route, **kwargs)

    def delete(self, route, **kwargs): return self('DELETE', route, **kwargs)

