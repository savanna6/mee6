from modus import Model
from modus.fields import Snowflake, String


class User(Model):
    id = Snowflake(required=True)
    username = String()
    discriminator = String()
    avatar = String()

