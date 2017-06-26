from modus import Model
from modus.fields import Snowflake, String, Integer


class Channel(Model):
    id = Snowflake(required=True)
    name = String()
    type = Integer()
    position = Integer()

    @property
    def mention(self):
        return '<#{}>'.format(self.id)

    def __repr__(self): return "<Channel id={} name={}>".format(self.id, self.name)


