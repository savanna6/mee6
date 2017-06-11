from mee6.types import User


class Member:
    def __init__(self, **kwargs):
        self.user = User(**kwargs.get('user', {}))
        self.nick = kwargs.get('nick')
        self.roles = kwargs.get('roles')
        self.joined_at = kwargs.get('joined_at')
        self.deaf = kwargs.get('deaf')
        self.mute = kwargs.get('mute')

    def __repr__(self): return "<Member id={} name={}>".format(self.user.id,
                                                               self.user.username)
