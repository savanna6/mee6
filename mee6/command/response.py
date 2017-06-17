from mee6.utils import get
from mee6.discord import send_message


class Response:

    @classmethod
    def ok(cls, message="Done 👍 "):
        return cls('ok', message)

    @classmethod
    def not_found(cls, message="Didn't find anything 😟"):
        return cls('not_found', message)

    @classmethod
    def missing_requirements(cls, message="Something is missing... 🤔"):
        return cls('missing_requirements', message)

    @classmethod
    def internal_error(cls, message="Oops, something went wrong in Mee6 land 🤕! Please contact our support if it happens again 🙏 ."):
        return cls('internal_error', message)

    def __init__(self, response_type, message, embed=None):
        self.response_type = response_type
        self.message = message
        self.embed = embed

    def send(self, guild, channel):
        guild_id = get(guild, 'id', guild)
        channel_id = get(channel, 'id', channel)
        return send_message(channel_id, self.message, embed=self.embed)
