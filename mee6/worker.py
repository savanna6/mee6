import os
import redis
import json
import mee6.types
import time
import gevent

from mee6.utils import Logger, get


EVENTS = ['GUILD_JOIN', 'GUILD_LEAVE', 'MEMBER_JOIN', 'MEMBER_LEAVE',
          'MESSAGE_CREATE', 'VOICE_SERVER_UPDATE', 'VOICE_STATE_UPDATE',]
EVENT_TIMEOUT = 5

class Worker(Logger):

    BROKER_URL = os.getenv('BROKER_URL')
    LISTNERS_COUNT = int(os.getenv('LISTNERS_COUNT', 100))

    def listener(self, *queue_names):
        r = redis.from_url(self.BROKER_URL, decode_responses=True)
        while True:
            queue_name, data = r.brpop(queue_names)
            try:
                payload = json.loads(data)
                self.handle_event(payload)
            except json.decoder.JSONDecodeError:
                self.log('Cannot decode payload: "{}"'.format(payload))
            finally:
                gevent.sleep(0.1)

    def run(self, *plugins):
        self.plugins = [P() for P in plugins]

        plugins_ids = [p.id for p in self.plugins]
        self.log('Loaded {} plugins: {}'.format(len(plugins_ids), ', '.join(plugins_ids)))

        queue_names = ['mee6.dispatch.' + event.lower() for event in EVENTS]

        self.log('Spawning {} listeners'.format(self.LISTNERS_COUNT))
        listeners = [gevent.spawn(self.listener, *queue_names) for _ in range(self.LISTNERS_COUNT)]

        gevent.joinall(listeners)

    def handle_event(self, payload):
        timestamp = payload.get('ts')
        # Ignore old events
        if time.time() > timestamp + EVENT_TIMEOUT:
            return

        guild = payload['g']
        for plugin in self.plugins:
            if not plugin.is_global and not plugin.check_guild(guild['id']):
                continue

            plugin.handle_event(payload)

