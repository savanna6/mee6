import requests
import logging

from mee6.utils import Logger
from mee6.discord.api.ratelimit import LocalRatelimit, RedisRatelimit

logging.getLogger('requests').setLevel(logging.WARNING)

class APIException(Exception):
    def __init__(self, r):
        msg = 'Request failed status_code={} payload={}'.format(r.status_code,
                                                                r.text)
        super(APIException, self).__init__(msg)


class HTTPClient(Logger):

    BASE_URL = 'https://discordapp.com/api/v6'

    def __init__(self, token, redis_url=None):
        self.token = token

        if redis_url:
            self.ratelimit = RedisRatelimit('redis://localhost')
        else:
            self.ratelimit = LocalRatelimit()

    @property
    def headers(self):
        return dict(Authorization="Bot " + self.token)

    def build_url(self, route): return self.BASE_URL + '/' + route

    def __call__(self, method, route, **kwargs):
        url = self.build_url(route)

        self.ratelimit.check(route)

        r = requests.request(method, url, headers=self.headers, **kwargs)

        self.ratelimit.update(route, r)

        if r.status_code < 400:
            return r

        if r.status_code != 429 and 400 <= r.status_code < 500:
            raise APIException(r)

        if r.status_code == 429:
            self.log('We are being ratelimited... This shouldn\'t happen...')

    def get(self, route, **kwargs): return self('GET', route, **kwargs)

    def post(self, route, **kwargs): return self('POST', route, **kwargs)

    def put(self, route, **kwargs): return self('PUT', route, **kwargs)

    def patch(self, route, **kwargs): return self('PATCH', route, **kwargs)

    def delete(self, route, **kwargs): return self('DELETE', route, **kwargs)

