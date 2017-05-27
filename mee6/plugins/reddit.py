import gevent
import gevent.queue
import requests
import os
import re

from collections import defaultdict
from itertools import groupby
from mee6 import Plugin
from mee6.utils import chunk, int2base
from mee6.discord.api.http import APIException
from mee6.discord import send_message
from mee6.types import Guild
from time import time

MESSAGE_FORMAT = "`New post from /r/{subreddit}`\n\n"\
                 "**{title}** *by {author}*\n"\
                 "**Link** {link}\n"\
                 "**Thread** {thread} \n\n"

class Reddit(Plugin):

    id = "reddit"
    name = "Reddit"
    description = "Get posts from your favourite subreddits directly to your Discord server"

    sender_queue = gevent.queue.Queue()
    sender_worker_instance = None

    last_post_id = None

    access_token = None
    access_token_expires_at = None
    user_agent = 'linux:mee6:v0.0.1 (by /u/cookkkie)'

    subreddit_rx = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9_]{2,20}\Z")

    def get_default_config(self, guild_id):
        default_config = {'subreddits': [],
                          'announcement_channel': guild_id}
        return default_config

    def before_config_patch(self, guild_id, old_config, new_config):
        for subreddit in old_config['subreddits']:
            key = 'plugin.{}.subreddit.{}.guilds'.format(self.id, subreddit)
            self.db.srem(key, guild_id)

    def after_config_patch(self, guild_id, config):
        for subreddit in config['subreddits']:
            key = 'plugin.{}.subreddit.{}.guilds'.format(self.id, subreddit)
            self.db.sadd(key, guild_id)

    def validate_config(self, guild_id, config):
        valid_subreddits = []

        for subreddit in config['subreddits']:
            sub = subreddit.split('/')[-1].lower()
            if self.subreddit_rx.match(sub): valid_subreddits.append(sub)

        config['subreddits'] = valid_subreddits

        return config

    def get_access_token(self):
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        url = 'https://www.reddit.com/api/v1/access_token'

        from requests.auth import HTTPBasicAuth
        auth = HTTPBasicAuth(client_id, client_secret)
        headers = {'user-agent': self.user_agent}
        data = {'grant_type': 'client_credentials'}
        r = requests.post(url, auth=auth, headers=headers, data=data,
                          timeout=10)
        result = r.json()

        access_token = result['access_token']
        expires_at = time() + result['expires_in']
        return (access_token, expires_at)

    def refresh_access_token(self):
        self.access_token, self.access_token_expires_at = self.get_access_token()

    def make_request(self, *args, **kwargs):
        # Check for access_token
        if self.access_token is None or time() > self.access_token_expires_at:
            self.refresh_access_token()

        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['user-agent'] = self.user_agent
        kwargs['headers']['Authorization'] = 'bearer ' + self.access_token
        kwargs['timeout'] = 10

        r = requests.get(*args, **kwargs)

        # If Unauthorized, refresh the token
        if r.status_code != 200:
            self.refresh_access_token()
            return self.make_request(*args, **kwargs)

        return r

    def get_new_posts(self, last_post_id):
        last_post_id = int(last_post_id, base=36)
        forward_ids = (last_post_id + 1 + i for i in range(0, 100))
        forward_ids = map(lambda id: 't3_' + int2base(id, 36), forward_ids)

        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) "\
                     "AppleWebKit/537.36 (KHTML, like Gecko)Chrome/57.0.2987.98"\
                     "Safari/537.36"
        url = "https://oauth.reddit.com/api/info"
        params = {'id': ','.join(forward_ids),
                  'raw_json': 1}
        r = self.make_request(url, params=params)
        result = r.json()
        children = result['data']['children']

        posts = map(lambda p: p['data'], children)

        # Only get subreddit posts
        posts = filter(lambda p: p.get('subreddit'), posts)

        return list(posts)

    def get_last_post_id(self):
        url = 'https://oauth.reddit.com/r/all/new'
        params = {'limit': 1, 'raw_json': 1}
        r = self.make_request(url, params=params)
        return r.json()['data']['children'][-1]['data']['id']

    def loop(self):
        if not self.last_post_id:
            self.last_post_id = self.get_last_post_id()
            self.log('Last subreddit post ID ' + self.last_post_id)

        posts = self.get_new_posts(self.last_post_id)

        self.log('Got {} new posts'.format(len(posts)))

        if len(posts) > 0:
            last_post = posts[-1]
            self.last_post_id = last_post['id']

        grouped_posts = groupby(posts, lambda p: p['subreddit'])
        for subreddit, subreddit_posts in grouped_posts:
            gevent.spawn(self.announce, subreddit, list(subreddit_posts))

    def announce(self, subreddit, subreddit_posts):
        subreddit = subreddit.lower()
        key = 'plugin.{}.subreddit.{}.guilds'.format(self.id, subreddit)
        guilds_ids = self.db.smembers(key)
        for guild_id in guilds_ids:
            if not self.check_guild(guild_id): continue

            self.log('Announcing /r/{} posts to {}'.format(subreddit,
                                                                guild_id))

            guild = Guild(id=guild_id, plugin=self)
            try:
                self.announce_posts(guild, subreddit_posts)
            except APIException as e:
                self.log('Got Api exception {}'.format(e.status_code))

    def announce_posts(self, guild, posts):
        messages = []
        for post in posts:
            message = MESSAGE_FORMAT.format(subreddit=post['subreddit'],
                                            title=post['title'],
                                            author=post['author'],
                                            link=post['url'],
                                            thread="https://www.reddit.com" + post["permalink"])
            message = message.replace('@everyone', '@ everyone')

            if len(messages) == 0:
                messages.append(message)
            else:
                if len(messages[-1] + message) > 2000:
                    messages.append(message)
                else:
                    messages[-1] += message

        announcement_channel = guild.config.get('announcement_channel')

        for message in messages:
            send_message(announcement_channel or guild.id, message)

