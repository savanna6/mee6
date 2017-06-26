from modus import Model
from modus.fields import Snowflake, String, Integer


class Role(Model):
    id = Snowflake(required=True)
    name = String()
    color = Integer()
    permissions = Integer()

