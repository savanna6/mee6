import redis
import os
import gevent
import mee6.types
import inspect

from mee6.types import Guild
from mee6.utils import Logger, get, json
from mee6.utils.redis import GroupKeys, PrefixedRedis
from mee6.command import Command
from mee6 import Permission


class PermissionStorage:
    def __init__(self, db):
        self.db = db

    def get(self, permission_id, guild, default=[]):
        key = 'permission.{}.guild.{}'.format(permission_id, guild.id)
        is_set_key = key + '.is_set'

        if not self.db.get(is_set_key):
            return default

        return list(self.db.smembers(key))

    def set(self, permission_id, guild, roles):
        roles_ids = []
        for role in roles:
            role_id = get(role, 'id', role)
            roles_ids.append(role)

        key = 'permission.{}.guild.{}'.format(permission_id, guild.id)
        is_set_key = key + '.is_set'

        self.db.set(is_set_key, 1)

        self.db.delete(key)
        if roles_ids != []:
            self.db.sadd(key, *roles_ids)

        return roles_ids


class Plugin(Logger):
    id = "plugin"
    name = "Plugin"
    description = ""

    is_global = False

    db = redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)

    guild_storages = {}

    def to_dict(self, guild_id=None):
        dct = {'id': self.id,
               'name': self.name,
               'description': self.description,
               'commands': [cmd.to_dict(guild_id) for cmd in self.commands]}

        if guild_id is not None:
            dct['enabled'] = self.check_guild(guild_id)
            dct['config'] = self.get_config(guild_id)

        return dct

    def __init__(self, in_bot=True):
        self.plugin_db = PrefixedRedis(self.db, 'plugin.' + self.id + '.')

        self.in_bot = in_bot

        self.permission_storage = PermissionStorage(self.plugin_db)

        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        commands_callbacks = [meth for name, meth in methods if get(meth, 'command_info')]
        self.commands = []
        for cb in commands_callbacks:
            info = cb.command_info

            opts = dict()
            opts['expression'] = info['expression']
            opts['description'] = info['description']
            opts['callback'] = cb
            opts['plugin'] = self
            opts['restrict_default'] = info.get('restrict_default', False)

            command = Command(**opts)
            self.commands.append(command)

        # Configs group keys
        self.config_db = GroupKeys(self.id + '.config', self.plugin_db, cache=in_bot,
                                   callback=self.handle_config_change)

        # Commands Configs group keys
        self.commands_config_db = GroupKeys(self.id + '.cmd-config', self.plugin_db, cache=in_bot,
                                            callback=self.handle_commands_config_change)


    def on_config_change(self, guild, config): pass

    def on_message_create(self, guild, message):
        for command in self.commands:
            command.execute(guild, message)

    def on_guild_join(self, guild): pass

    def on_guild_leave(self, guild): pass

    def on_member_join(self, guild, member): pass

    def on_member_leave(self, guild, member): pass

    def get_guild_storage(self, guild):
        guild_id = get(guild, 'id', guild)
        guild_storage = self.guild_storages.get(guild_id)

        if guild_storage:
            return guild_storage

        prefix = 'plugin.{}.guild.{}.storage'.format(self.id, guild_id)
        guild_storage = PrefixedRedis(self.db, prefix)
        self.guild_storages[guild_id] = guild_storage

        return guild_storage

    def get_guilds(self):
        guilds = self.db.smembers('plugin.{}.guilds'.format(self.name))
        guilds = [guild for guild in guilds if self.db.sismember('servers', guild)]

        return [self._make_guild({'id': id}) for id in guilds]

    def enable(self, guild):
        guild_id = get(guild, 'id', guild)
        self.db.sadd('plugins:{}'.format(guild_id), self.name)
        self.db.sadd('plugin.{}.guilds'.format(self.name), guild_id)

    def disable(self, guild):
        guild_id = get(guild, 'id', guild)
        self.db.srem('plugins:{}'.format(guild_id), self.name)
        self.db.srem('plugin.{}.guilds'.format(self.name), guild_id)

    def check_guild(self, guild):
        guild_id = get(guild, 'id', guild)

        if not self.db.sismember('servers', guild_id):
            return False

        plugins = self.db.smembers('plugins:{}'.format(guild_id))
        return self.name in plugins

    def _make_guild(self, guild_payload):
        guild = Guild.from_payload(guild_payload)
        guild.db = self.db
        guild.plugin = self
        return guild

    def handle_commands_config_change(self, payload):
        pass

    def handle_config_change(self, payload):
        op = payload[0]
        if op == 's':
            key = payload[1]
            value = payload[2]

            guild_id = int(key.split('.')[-1])
            config = json.loads(value)
            guild = self._make_guild({'id': guild_id})

            self.on_config_change(guild, config)

    def get_config(self, guild):
        guild_id = get(guild, 'id', guild)

        key = 'config.{}'.format(self.id, guild_id)
        raw_config = self.config_db.get(key)

        if raw_config:
            config = json.loads(raw_config)
        else:
            config = self.get_default_config(guild_id)

        return config

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

        self.config_db.set('config.{}'.format(self.id, guild_id),
                           json.dumps(config))

        # post-hook
        self.after_config_patch(guild_id, config)

        return config

    def before_config_patch(self, guild_id, old_config, new_config): pass
    def after_config_patch(self, guild_id, config): pass
    def validate_config(self, guild_id, config): return config

    def get_permissions(self, guild):
        guild_id = get(guild, 'id', guild)

    def handle_event(self, payload):
        event_type = payload['t']
        guild = self._make_guild(payload['g'])
        data = payload.get('d')

        if data:
            data_type_name = event_type.split('_')[0].lower()
            data_type_module = get(mee6.types, data_type_name)
            if data_type_module:
                data_type = get(data_type_module, data_type_name.capitalize())
            else:
                data_type = None

            if data_type:
                decoded_data = data_type(**data)
            else:
                decoded_data = data

        listener = get(self, 'on_' + event_type.lower())
        if listener:
            if data:
                gevent.spawn(listener, guild, decoded_data)
            else:
                gevent.spawn(listener, guild)

    @classmethod
    def loop(cls, sleep_time=1):
        def deco(f):
            f.is_loop = 1
            f.sleep_time = 1
            return f
        return deco

    def get_loop_container(self, loop):
        def loop_container():
            import traceback
            while True:
                try:
                    loop()
                except Exception as e:
                    traceback.print_exc()
                    gevent.sleep(3)

                gevent.sleep(loop.sleep_time)
        return loop_container

    def run(self):
        loops = []
        for name, method in self.__class__.__dict__.items():
            if hasattr(method, 'is_loop'):
                loops.append(name)

        loops = [get(self, loop) for loop in loops]

        active_loops = []

        import copy
        for loop in loops:
            active_loops.append(gevent.spawn(self.get_loop_container(loop)))

        gevent.joinall(active_loops)
