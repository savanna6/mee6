import os

from mee6.discord.api.http import HTTPClient
from mee6.types import Channel, Guild, Message

class APIClient:

    TOKEN = os.getenv('TOKEN')

    def __init__(self):
        self.http = HTTPClient(self.TOKEN)

    def send_message(self, channel_id, message_content):
        r = self.http.post('channels/{}/messages'.format(channel_id),
                           json={'content': message_content})
        return Message(**r.json())

