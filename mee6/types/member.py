from mee6.types import User


class Member:
    def __init__(self, **kwargs):
        self.user = User(**kwargs.get('user', {}))
        self.nick = kwargs.get('nick')
        self.roles = kwargs.get('roles')
        self.joined_at = kwargs.get('joined_at')
        self.deaf = kwargs.get('deaf')
        self.mute = kwargs.get('mute')
        self.voice_state = kwargs.get('voice_state')

    def get_voice_channel(self, guild):
        if not self.voice_state:
            return None

        if not self.voice_state['channel_id']:
            return None

        for vc in guild.voice_channels:
            if vc.id == self.voice_state['channel_id']:
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
