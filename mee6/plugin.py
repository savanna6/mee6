import redis
import os
import gevent
import mee6.types
import inspect

from mee6.types import Guild
from mee6.utils import Logger, get, json
from mee6.command import Command
from mee6 import Permission


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
    id = "plugin"
    name = "Plugin"
    description = ""
    _permissions = {}

    is_global = False

    db = redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)

    def __init__(self):
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        commands_callbacks = [meth for name, meth in methods if get(meth, 'command_info')]

        self.commands = []
        for cb in commands_callbacks:
            info = cb.command_info

            opts = dict()
            opts['expression'] = info['expression']
            opts['description'] = info['description']
            opts['callback'] = cb
            opts['after_check'] = self.check_command_permission
            command = Command(**opts)
            self.commands.append(command)

            command_permission_name = self.command_permission_name(command)

            if not info.get('default_restrict'):
                command_permission = Permission(command_permission_name,
                                                default=lambda gid: [gid])
            else:
                command_permission = Permission(command_permission_name)

            self._permissions[command_permission.name] = command_permission

        # Configs group keys
        key = 'plugin.' + self.id + '.configs'
        self.config_db = GroupKeys(self.id, self.db)

    @property
    def db_prefix(self):
        return 'plugin.' + self.id + '.'

    def command_permission_name(self, command):
        return 'cmd-' + self.id + '.' + command.name

    def check_command_permission(self, command, ctx):
        member_permissions = ctx.author.get_permissions(ctx.guild)
        if ( member_permissions >> 5 & 1 ) or ( member_permissions >> 3 & 1):
            return True

        if int(ctx.author.id) == int(ctx.guild.owner_id):
            return True

        command_permission_name = self.command_permission_name(command)
        permission = self._permissions[command_permission_name]
        if not permission.is_allowed(ctx.guild, ctx.author):
            return False

        return True

    def on_message_create(self, guild, message):
        for command in self.commands:
            command.execute(guild, message)

    def on_guild_join(self, guild): pass

    def on_guild_leave(self, guild): pass

    def on_member_join(self, guild, member): pass

    def on_member_leave(self, guild, member): pass

    def get_guild_storage(self, guild): return GuildStorage(self.db, self, guild)

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

    def get_config(self, guild):
        guild_id = get(guild, 'id', guild)

        key = 'plugin.{}.config.{}'.format(self.id, guild_id)
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

        self.config_db.set('plugin.{}.config.{}'.format(self.id, guild_id),
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
        print(event_type)
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
