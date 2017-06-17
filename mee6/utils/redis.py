import gevent
import json

from gevent.lock import Semaphore


class GroupKeys:

    def __init__(self, channel_name, redis=None):
        self.channel_name = channel_name

        self.redis = redis

        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(channel_name)

        self.cache = {}

        self._lock = Semaphore()

        self.watcher = gevent.spawn(self.watch)

    def get(self, key):
        value = self.cache.get(key)
        if value:
            return value

        value = self.redis.get(key)
        if value:
            self.cache[key] = value

        return value

    def set(self, key, value):
        self.redis.set(key, value)

        payload = ['s', key, value]
        packet = json.dumps(payload)
        self.redis.publish(self.channel_name, packet)

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
