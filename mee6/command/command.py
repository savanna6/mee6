import re
import traceback

from mee6.utils import get
from mee6.rpc import get_guild_member
from mee6.command.utils import build_regex
from mee6.command import Response
from functools import wraps


class CommandContext:
    def __init__(self, guild, message):
        self.guild = guild
        self.message = message

    @property
    def author(self):
        return get_guild_member(self.guild.id, self.message.author.id)

class Command:
    @classmethod
    def register(cls, expression):
        def deco(f):
            command_info = {'expression': expression,
                            'callback': f,
                            'description': ''}
            f.command_info = command_info
            return f
        return deco

    @classmethod
    def description(cls, descriptionn):
        def deco(f):
            f.command_info['description'] = description
            return f
        return deco

    @classmethod
    def default_restrict(cls, descriptionn):
        def deco(f):
            f.command_info['default_restrict'] = True
            return f
        return deco

    def __init__(self, expression=None, callback=None, require_roles=[],
                 description="", after_check=lambda _ : True):
        self.expression = expression
        self.callback = callback
        self.require_roles = require_roles
        self.description = description
        self.regex, self.cast_to = build_regex(self.expression)
        self.name = callback.__name__
        self.after_check = after_check

    def check_match(self, msg):
        match = self.regex.match(msg)
        if not match:
            return None

        return [t(arg) for t, arg in zip(self.cast_to, match.groups())]

    def execute(self, guild, message):
        arguments = self.check_match(message.content)
        if arguments is None:
            return

        ctx = CommandContext(guild, message)

        if not self.after_check(self, ctx):
            return

        try:
            response = self.callback(ctx, *arguments)
        except Exception as e:
            response = Response.internal_error()
            traceback.print_exc()

        if response:
            return response.send(guild, message.channel_id)

    def get_permission(self, db, prefix):
        key = prefix + 'command_permission.' + self.name
        permissions = db.smembers(key)
        users, roles = ([], [])
        for permission in permissions:
            perm_type, id = permission.split(':')
            if perm_type == 'u':
                users.append(int(id))
            if perm_type == 'r':
                roles.append(int(id))
        return users, roles

    def patch_permission(self, db, prefix, roles=[], users=[]):
        permissions = []

        for role in roles:
            id = get(role, 'id', role)
            permissions.append('r:{}'.format(id))

        for user in users:
            id = get(user, 'id', user)
            permissions.append('u:{}'.format(id))

        key = prefix + 'command_permission.' + self.name
        db.delete(key)
        db.sadd(key, *permissions)

        return users, roles
