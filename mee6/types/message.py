from modus import Model
from modus.fields import Snowflake, String, ModelField
from mee6.types import User


class Message(Model):
    id = Snowflake(required=True)
    channel_id = Snowflake()
    content = String()
    timestamp = String()
    edited_timestamp = String()
    author = ModelField(User)
    webhook_id = Snowflake()
