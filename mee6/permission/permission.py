import redis
import os

from mee6.utils import get


class Permission:

    db = redis.from_url(os.getenv('PERMISSIONS_REDIS_URL', 'redis://localhost'),
                        decode_responses= True)

    def __init__(self, name, default=lambda _: []):
        self.name = name
        self.default = default

    def key(self, guild):
        guild_id = get(guild, 'id', guild)
        return 'permissions.{}.{}'.format(self.name, guild_id)

    def set(self, guild, roles):
        key = self.key(guild)

        if len(roles) == 0:
            self.db.delete(key)
            return

        roles_ids = []
        for role in roles:
            role_id = get(role, 'id', role)
            roles_ids.append(role_id)

        self.db.delete(key)
        self.db.sadd(key, *roles_ids)

        key = key + '.is_set'
        self.db.set(key, 1)

    def is_set(self, guild):
        key = self.key(guild) + '.is_set'
        return self.db.get(key) is not None

    def get(self, guild):
        allowed = self.db.smembers(self.key(guild))
        if len(allowed) > 0:
            return list(allowed)

        if self.is_set(guild):
            return list(allowed)
        else:
            guild_id = get(guild, 'id', guild)
            roles = self.default(guild_id)
            self.set(guild, roles)
            return roles

    def is_allowed(self, guild, member):
        allowed = self.get(guild)
        for role_id in member.roles:
            if role_id in allowed:
                return True

        return False
