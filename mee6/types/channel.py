class Channel:

    @classmethod
    def from_payload(cls, payload): return cls(**payload)

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.type = kwargs.get('type')
        self.position = kwargs.get('position')
        self.permission_overwrites = kwargs.get('permission_overwrites')

    @property
    def mention(self):
        return '<#{}>'.format(self.id)

    def __repr__(self): return "<Channel id={} name={}>".format(self.id, self.name)
