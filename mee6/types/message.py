class Message:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.channel_id = kwargs.get('channel_id')
        self.content = kwargs.get('content')
        self.timestamp = kwargs.get('timestamp')
        self.edited_timestamp = kwargs.get('edited_timestamp')
        self.tts = kwargs.get('tts')
        self.mentions = kwargs.get('mentions')
        self.mention_everyone = kwargs.get('mention_everyone')
        self.mention_roles = kwargs.get('mention_roles')
        self.webhook_id = kwargs.get('webhook_id')

        if not self.webhook_id:
            self.author = User(**kwargs.get('author'))
        else:
            self.author = None
