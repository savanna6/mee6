class Webhook:
    def __init__(self, **kwargs):
        self.id = int(kwargs.get('id'))
        self.guild_id = kwargs.get('guild_id')
        self.channel_id = kwargs.get('channel_id')
        self.name = kwargs.get('name')
        self.avatar = kwargs.get('avatar')
        self.token = kwargs.get('token')
