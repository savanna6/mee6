import os
import redis

from mee6.discord.api.http import HTTPClient
from mee6.types import Channel, Guild, Message, Webhook
from mee6.exceptions import APIException

class WebhookStorage:

    def __init__(self):
        redis_url = os.getenv('REDIS_URL', 'redis://localhost')
        self.db = redis.from_url(redis_url, decode_responses=True)

class APIClient:

    TOKEN = os.getenv('TOKEN')

    def __init__(self):
        redis_url = os.getenv('REDIS_URL', 'redis://localhost')

        self.http = HTTPClient(self.TOKEN)
        self.db = redis.from_url(redis_url, decode_responses=True)

    def create_webhook(self, webhook_id, channel_id):
        path = 'channels/{}/webhooks'.format(channel_id)
        body = {'name': 'Mee6 Webhook'}
        r = self.http.post(path, json=body)
        webhook = Webhook(**r.json())

        self.db.set('webhooks.{}'.format(webhook_id),
                    '{0.id}.{0.token}'.format(webhook))

        return webhook

    def get_webhook(self, webhook_id):
        data = self.db.get('webhooks.{}'.format(webhook_id))
        if not data:
            return None

        id, token = data.split('.')
        return Webhook(id=id, token=token)

    def reset_webhook(self, webhook_id):
        self.db.delete('webhooks.{}'.format(webhook_id))


    def execute_webhook(self, webhook, message_content, username=None,
                        avatar_url=None):
        path = 'webhooks/{0.id}/{0.token}?wait=true'.format(webhook)

        username = username or 'Mee6'
        avatar_url = avatar_url or 'https://i.imgur.com/qCe8hGX.png'

        body = {'content': message_content,
                'username': username,
                'avatar_url': avatar_url}

        r = self.http.post(path, auth=False, json=body)

        return Message(**r.json())

    def send_webhook_message(self, webhook_id, channel_id, message_content):
        webhook = self.get_webhook(webhook_id)
        if webhook is None:
            webhook = self.create_webhook(webhook_id, channel_id)

        try:
            return self.execute_webhook(webhook, message_content)
        except APIException as e:
            if e.status_code == 404:
                self.reset_webhook(webhook_id)
                return self.send_webhook_message(webhook_id, channel_id, message_content)
            else:
                raise e

    def send_message(self, channel_id, message_content, embed=None):
        path = 'channels/{}/messages'.format(channel_id)
        body = {'content': message_content}
        if embed:
            body['embed'] = embed.get_dict()

        r = self.http.post(path, json=body)

        return Message(**r.json())

