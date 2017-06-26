from modus import Model
from modus.fields import Snowflake, String, Integer, List, ModelField
from mee6.types import Channel, Role


class Guild(Model):
    id = Snowflake(required=True)
    name = String()
    owner_id = Snowflake()
    roles = List(ModelField(Role))
    channels = List(ModelField(Channel))

    def __init__(self, **kwargs):
        self.db = kwargs.get('db')
        self.plugin = kwargs.get('plugin')
        super(Guild, self).__init__(**kwargs)

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
