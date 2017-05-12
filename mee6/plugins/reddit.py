import gevent
import gevent.queue
import requests

from collections import defaultdict
from itertools import groupby
from mee6 import Plugin, PluginConfig
from mee6.utils import chunk
from mee6.discord.api.http import APIException
from mee6.discord import send_message

MESSAGE_FORMAT = "`New post from /r/{subreddit}`\n\n"\
                 "**{title}** *by {author}*\n"\
                 "**Link** {link}\n"\
                 "**Thread** {thread} \n\n"
SENDER_PACE = 0.1
SUBREDDITS_BATCH_SIZE = 50

class Reddit(Plugin):

    id = "reddit"
    name = "Reddit"
    description = "Get posts from your favourite subreddits directly to your Discord server"

    sender_queue = gevent.queue.Queue()
    sender_worker_instance = None

    def sender_worker(self, wait_time):
        while True:
            channel_id, message, guild, num = self.sender_queue.get()
            try:
                send_message(channel_id, message)
                self.log('Sent {} posts to {}\'s channel #{}'.format(num,
                                                                     guild,
                                                                     channel_id))
            except APIException as e:
                self.log('An exception occured sending message in'\
                         '{} // {}'.format(guild.id, e.payload))
            except Exception as e:
                self.log('An unknown expection occured sending message...'\
                         '{}'.format(e))
            finally:
                gevent.sleep(wait_time)

    def get_config(self, guild):
        config = PluginConfig()
        config.subreddits = guild.storage.smembers('subs')
        return config

    def announce(self, posts, guild):
        to_announce = []
        for post in posts:
            #if guild.storage.sismember('announced', post['id']): continue
            to_announce.append(post)

        messages = []
        posts_ids  = []
        for post in to_announce:
            message = MESSAGE_FORMAT.format(subreddit=post['subreddit'],
                                            title=post['title'],
                                            author=post['author'],
                                            link=post['url'],
                                            thread="https://www.reddit.com" +post["permalink"])
            message = message.replace('@everyone', '@ everyone')

            if len(messages) == 0:
                messages.append(message)
                posts_ids.append([post['id']])
            else:
                if len(messages[-1] + message) > 2000:
                    messages.append(message)
                    posts_ids.append([post['id']])
                else:
                    messages[-1] += message
                    posts_ids[-1].append(post['id'])

        display_channel_id = guild.storage.get('display_channel') or guild.id
        for message, posts_ids in zip(messages, posts_ids):
            self.sender_queue.put((display_channel_id, message, guild,
                                   len(posts_ids)))
            guild.storage.sadd('announced', *posts_ids)

    def loop(self):
        if self.sender_worker_instance is None:
            self.sender_worker_instance = gevent.spawn(self.sender_worker,
                                                       SENDER_PACE)

        subreddits = self.time_log('Fetching subreddits list',
                                   self.db.smembers,
                                   'Reddit.#:subs')

        guilds = self.time_log('Fetching guilds', self.get_guilds)
        self.log('Found {} guilds'.format(len(guilds)))

        subreddits_map = defaultdict(list)
        for guild in guilds:
            for subreddit in guild.config.subreddits:
                subreddits_map[subreddit].append(guild)

        subreddits_posts = {}
        for subs in chunk(subreddits, SUBREDDITS_BATCH_SIZE):
            posts = self.time_log('Getting {} posts'.format('+'.join(subs)),
                                  self.get_posts, subs)
            gevent.sleep(1)
            for subreddit, subreddit_posts in posts.items():
                guilds = subreddits_map.get(subreddit, [])
                for guild in guilds:
                    gevent.spawn(self.announce, list(reversed(subreddit_posts)), guild)

    def get_posts(self, subreddits):
        url ='https://www.reddit.com/r/{subs}/new.json?limit=100'.format(subs='+'.join(subreddits))
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) "\
                     "AppleWebKit/537.36 (KHTML, like Gecko)Chrome/57.0.2987.98"\
                     "Safari/537.36"
        req = requests.get(url, headers={'user-agent': user_agent})

        if req.status_code != 200:
            return {}

        data = req.json().get('data')
        if not data:
            return {}

        posts = map(lambda c: c['data'], data['children'])

        return {sub : list(posts) for sub, posts in groupby(posts, lambda p: p['subreddit'])}

