from mee6.types import Channel, Role
from mee6.utils import listify

class Guild:

    @classmethod
    def from_payload(cls, payload):
        return cls(**payload)

    def __init__(self, **kwargs):
        self.id = int(kwargs.get('id'))
        self.name = kwargs.get('name')
        self.owner_id = kwargs.get('owner_id')
        self.roles = [Role.from_payload(r) for r in listify(kwargs.get('roles', []))]
        self.channels = [Channel.from_payload(c) for c in listify(kwargs.get('channels', []))]

        self.db = kwargs.get('db')
        self.plugin = kwargs.get('plugin')

    @property
    def members(self): pass

    @property
    def config(self): return self.plugin.get_config(self)

    @property
    def storage(self): return self.plugin.get_guild_storage(self)

    @property
    def voice_channels(self): return [c for c in self.channels if c.type == 2]

    @property
    def text_channels(self): return [c for c in self.channels if c.type == 0]

    def __repr__(self): return "<Guild id={} name={}>".format(self.id, self.name)
