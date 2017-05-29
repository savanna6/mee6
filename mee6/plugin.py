import redis
import os
import gevent
import json

from mee6.types import Guild
from mee6.utils import Logger, get

class GuildStorage:
    def __init__(self, db, plugin, guild):
        self.db = db
        self.pre = 'plugin.{}.guild.{}.storage:'.format(plugin.id,
                                                        guild.id)

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
    """

    Utility functions:
        - get_guilds () -> (list of guilds)
            Gets all the guilds (partial guilds) that have the plugin enabled.
        - check_guild (guild_id | guild) -> (bool)
            Checks if a guild has the plugin enabled
        - get_config (guild_id | guild) -> (dict config)
            Gets the config of a guild
        - get_default_config (guild_id | guild) -> (dict config)
            Gets the default config
        - patch_config (guild_id | guild, new_config) -> (dict config)
            Pathes the config of a guild
    """
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
        guilds = (id for id in self.db.smembers('servers'))
        guilds = filter(lambda g: self.db.sismember('plugins:'+g, self.name),
                        guilds)

        return [self._make_guild({'id': id}) for id in guilds]

    def enable(self, guild):
        guild_id = get(guild, 'id', guild)
        self.db.sadd('plugins:{}'.format(guild_id), self.name)

    def disable(self, guild):
        guild_id = get(guild, 'id', guild)
        self.db.srem('plugins:{}'.format(guild_id), self.name)

    def check_guild(self, guild):
        guild_id = get(guild, 'id', guild)

        if not self.db.sismember('servers', guild_id):
            return False

        # Legacy
        plugins = self.db.smembers('plugins:{}'.format(guild_id))
        return self.id in map(lambda s: s.lower(), plugins)
        # /Legacy

        #return self.db.sismember('plugins:{}'.format(guild_id), self.id)

    def _make_guild(self, guild_payload):
        guild = Guild.from_payload(guild_payload)
        guild.db = self.db
        guild.plugin = self
        return guild

    def get_config(self, guild):
        guild_id = get(guild, 'id', guild)

        key = 'plugin.{}.config.{}'.format(self.id, guild_id)
        config = self.db.get(key)

        if config:
            return json.loads(config)

        return self.get_default_config(guild_id)

    def get_default_config(self, guild_id):
        default_config = {}
        return default_config

    def patch_config(self, guild, new_config):
        guild_id = get(guild, 'id', guild)

        old_config = self.get_config(guild_id)

        # pre-hook
        self.before_config_patch(guild_id, old_config, new_config)

        config = {k: new_config.get(k, old_config[k]) for k in old_config.keys()}

        # validation
        config = self.validate_config(guild_id, config)

        self.db.set('plugin.{}.config.{}'.format(self.id, guild_id),
                    json.dumps(config))

        # post-hook
        self.after_config_patch(guild_id, config)

        return config

    def before_config_patch(self, guild_id, old_config, new_config): pass
    def after_config_patch(self, guild_id, config): pass
    def validate_config(self, guild_id, config): return config

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
