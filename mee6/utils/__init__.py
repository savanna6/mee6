import os

from mee6.utils.logger import Logger

def chunk(l, n):
    l = list(l)
    return [l[i:i+n] for i in range(0, len(l), n)]

import string
digs = string.digits + string.ascii_letters
def int2base(x, base):
    if x == 0: return digs[0]

    digits = []

    while x:
        digits.append(digs[x % base])
        x //= base

    digits.reverse()

    return ''.join(digits)

def get(obj, attr, default=None):
    try:
        return getattr(obj, attr)
    except AttributeError:
        return default

from time import time
from datadog import statsd

class timed:
    def __init__(self, metric, tags={}):
        self.metric = metric
        self.tags = tags

    def __enter__(self):
        self.start = time()
        return self

    def __exit__(self, *args):
        now = time()
        tags = ['{}:{}'.format(tag_name, value) for tag_name, value in self.tags.items()]
        statsd.timing(self.metric, (now - self.start) * 1000, tags=tags)

def init_dd_agent():
    dd_agent = os.getenv('DD_AGENT')
    if dd_agent:
        from datadog import initialize
        initialize(statsd_host=dd_agent, statsd_port=8125)

def real_dict(dct):
    return {k: v for k, v in dct.items() if v is not None}

def listify(list_or_dict):
    if type(list_or_dict) == dict:
        return list_or_dict.values()
    return list_or_dict
