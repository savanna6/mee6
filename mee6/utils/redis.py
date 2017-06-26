import gevent
import json

from gevent.lock import Semaphore


class GroupKeys:

    def __init__(self, channel_name, redis=None, cache=True, callback=None):
        self.channel_name = channel_name

        self.redis = redis

        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(channel_name)

        self._lock = Semaphore()

        self.callback = callback

        if cache:
            self.cache = {}
            self.watcher = gevent.spawn(self.watch)
        else:
            self.cache = None

    @property
    def cache_enable(self):
        return self.cache is not None

    def _publish(self, value):
        if isinstance(self.redis, PrefixedRedis):
            rdb = self.redis.rdb
        else:
            rdb = self.redis
        return rdb.publish(self.channel_name, value)

    def get(self, key):
        if self.cache_enable:
            value = self.cache.get(key)
            if value:
                return value

        value = self.redis.get(key)
        if self.cache_enable and value:
            self.cache[key] = value

        return value

    def set(self, key, value):
        self.redis.set(key, value)

        payload = ['s', key, value]
        packet = json.dumps(payload)
        self._publish(packet)

    def watch(self):
        for frame in self.pubsub.listen():
            if frame['type'] != 'message':
                continue

            with self._lock:
                data = frame['data']
                payload = json.loads(data)
                op = payload[0]

                if op == 's':
                    key = payload[1]
                    value = payload[2]
                    self.cache[key] = value

                if self.callback:
                    gevent.spawn(self.callback, payload)

class PrefixedRedis:
    def __init__(self, redis=None, prefix=''):
        self.rdb = redis
        self.pre = prefix

    def publish(self, key, value):
        return self.rdb.publish(self.pre + key, value)

    def get(self, key):
        return self.rdb.get(self.pre + key)

    def set(self, key, value):
        return self.rdb.set(self.pre + key, value)

    def setex(self, key, value, expire):
        return self.rdb.set(self.pre + key, value, expire)

    def sismember(self, key, value):
        return self.rdb.sismember(self.pre + key, value)

    def smembers(self, key):
        return self.rdb.smembers(self.pre + key)

    def sadd(self, key, *values):
        return self.rdb.sadd(self.pre + key, *values)

    def delete(self, key):
        return self.rdb.deletes(self.pre + key)

    @property
    def pubsub(self):
        return self.rdb.pubsub
