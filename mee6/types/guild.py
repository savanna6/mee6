from mee6.types import Channel, Role

class Guild:

    @classmethod
    def from_payload(cls, payload):
        return cls(**payload)

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.owner_id = kwargs.get('owner_id')
        self.roles = [Role.from_payload(r) for r in kwargs.get('roles', [])]
        self.channels = [Channel.from_payload(c) for c in kwargs.get('channels', [])]

        self.db = kwargs.get('db')
        self.plugin = kwargs.get('plugin')

    @property
    def members(self): pass

    @property
    def config(self): return self.plugin.get_config(self)

    @property
    def storage(self): return self.plugin.get_guild_storage(self)

    def __repr__(self): return "<Guild {} {}>".format(self.id, self.name)
