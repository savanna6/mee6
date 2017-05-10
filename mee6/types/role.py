class Role:

    @classmethod
    def from_payload(cls, payload): return cls(**payload)

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.color = kwargs.get('color')
        self.permissions = kwargs.get('permissions')
        self.managed = kwargs.get('managed')
