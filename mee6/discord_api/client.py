import os

from mee6.discord_api.http import HTTPClient
from mee6.types import Channel, Guild, Message

class APIClient:

    token = os.getenv('TOKEN')
    redis_url = os.getenv('REDIS_URL')

    def __init__(self):
        self.http = HTTPClient(self.token, self.redis_url)

    def send_message(self, channel_id, message_content):
        r = self.http.post('channels/{}/messages'.format(channel_id),
                           json={'content': message_content})
        return Message(**r.json())
