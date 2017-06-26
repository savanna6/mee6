from modus import Model
from modus.fields import Snowflake, String


class Webhook(Model):
    id = Snowflake(required=True)
    guild_id = Snowflake()
    channel_id = Snowflake()
    name = String()
    avatar = String()
    token = String()

