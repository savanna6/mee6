class User:

    def __init__(self, **kwargs):
        self.id = int(kwargs.get('id'))
        self.username = kwargs.get('username')
        self.discriminator = kwargs.get('discriminator')
        self.avatar = kwargs.get('avatar')
        self.bot = kwargs.get('bot')
        self.mfa_enabled = kwargs.get('mfa_enabled')
        self.verified = kwargs.get('verified')
        self.email = kwargs.get('email')

