from modus import Model
from modus.fields import Snowflake, String, Integer, List, ModelField
from mee6.types import User


class VoiceState(Model):
    guild_id = Snowflake()
    channel_id = Snowflake()
    user_id = Snowflake()
    session_id = String()


class Member(Model):
    user = ModelField(User)
    nick = String()
    roles = List(Snowflake())
    joined_at = String()
    voice_state = ModelField(VoiceState)

    def get_voice_channel(self, guild):
        if not self.voice_state:
            return None

        if not self.voice_state.channel_id:
            return None

        for vc in guild.voice_channels:
            if vc.id == self.voice_state.channel_id:
                return vc

        return None

    @property
    def mention(self):
        return '<@{}>'.format(self.id)

    def get_permissions(self, guild):
        roles = [role for role in guild.roles if role.id in self.roles]
        return sum(role.permissions for role in roles)

    def __repr__(self): return "<Member id={} name={}>".format(self.user.id,
                                                               self.user.username)
