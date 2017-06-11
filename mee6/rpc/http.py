import logging
import requests
import os
import re

from mee6.utils import Logger, timed
from mee6.exceptions import RPCException


logging.getLogger('requests').setLevel(logging.WARNING)

rx = re.compile(r'^[0-9]*$')

class HTTPClient(Logger):

    BASE_URL = os.getenv('SHARDS_RPC_URL')

    def build_url(self, route): return self.BASE_URL + '/' + route

    def build_metric_type(self, method, route):
        route = route.split('?')[0]
        route_splitted = route.split('/')
        route_splitted = [part for part in route_splitted if len(part) < 15]
        parts = [method] + [part for part in route_splitted if not rx.match(part)]
        return '_'.join(parts)

    def __call__(self, method, route, **kwargs):
        url = self.build_url(route)

        tags = {'request_type': self.build_metric_type(method, route)}
        with timed('rpc_request_duration', tags=tags):
            r = requests.request(method, url, **kwargs)

        if r.status_code < 400:
            return r

        raise RPCException(r)

    def get(self, route, **kwargs): return self('GET', route, **kwargs)

    def post(self, route, **kwargs): return self('POST', route, **kwargs)

    def put(self, route, **kwargs): return self('PUT', route, **kwargs)

    def patch(self, route, **kwargs): return self('PATCH', route, **kwargs)

    def delete(self, route, **kwargs): return self('DELETE', route, **kwargs)

