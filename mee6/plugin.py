import redis
import os
import gevent

from mee6.types import Guild
from mee6.utils import Logger

class PluginConfig: pass

class GuildStorage:
    def __init__(self, db, plugin, guild):
        self.db = db
        self.pre = '.'.join((plugin.name, guild.id)) + ':'

    def get(self, key):
        return self.db.get(self.pre + key)

    def set(self, key, value):
        return self.db.set(self.pre + key, value)

    def sismember(self, key, value):
        return self.db.sismember(self.pre + key, value)

    def smembers(self, key):
        return self.db.smembers(self.pre + key)

    def sadd(self, key, *values):
        return self.db.sadd(self.pre + key, *values)


class Plugin(Logger):
    id = "plugin"
    name = "Plugin"
    description = ""
    db = redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)

    def on_message_create(self, guild, message): pass

    def on_guild_join(self, guild): pass

    def on_guild_leave(self, guild): pass

    def on_member_join(self, guild, member): pass

    def on_member_leave(self, guild, member): pass

    def get_guild_storage(self, guild): return GuildStorage(self.db, self, guild)

    def get_guilds(self):
        guilds = (id for id in self.db.smembers('guilds'))
        guilds = filter(lambda g: self.db.sismember('plugins:'+g, self.name),
                        guilds)

        return [self._make_guild({'id': id}) for id in guilds]

    def _make_guild(self, guild_payload):
        guild = Guild.from_payload(guild_payload)
        guild.db = self.db
        guild.plugin = self
        return guild

    def dispatch(self, event):
        event_type = event['t'].lower()
        guild_payload = event['g']
        data = event['d']

        try:
            listener = getattr(self, 'on_' + event_type)
        except AttributeError:
            listener = None

        if not handler: return

        guild = self._make_guild(guild_payload)

        if data:
            gevent.spawn(handler, guild, data)
        else:
            gevent.spawn(handler, guild)

    def run(self, sleep_time=1):
        while True:
            self.loop()
            gevent.sleep(sleep_time)
