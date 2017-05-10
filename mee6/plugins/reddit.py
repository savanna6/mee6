import gevent
import requests

from collections import defaultdict
from itertools import groupby
from mee6 import Plugin, PluginConfig, api
from mee6.utils import chunk

MESSAGE_FORMAT = "`New post from /r/{subreddit}`\n\n"\
                 "**{title}** *by {author}*\n"\
                 "**Link** {link}\n"\
                 "**Thread** {thread} \n\n"

class Reddit(Plugin):

    id = "reddit"
    name = "Reddit"
    description = "Get posts from your favourite subreddits directly to your Discord server"

    def get_config(self, guild):
        config = PluginConfig()
        config.subreddits = guild.storage.smembers('subs')
        return config

    def announce(self, posts, guild):
        to_announce = []
        for post in posts:
            if self.db.sismember('Reddit.{}:announced'.format(guild.id),
                                 post['id']): continue
            to_announce.append(post)

        messages = []
        for post in to_announce:
            message = MESSAGE_FORMAT.format(subreddit=post['subreddit'],
                                            title=post['title'],
                                            author=post['author'],
                                            link=post['url'],
                                            thread="https://www.reddit.com" +post["permalink"])
            message = message.replace('@everyone', '@ everyone')

            if len(messages) == 0:
                messages.append(message)
            else:
                if len(messages[-1] + message) > 2000:
                    messages.append(message)
                else:
                    messages[-1] += message

        for message in messages:
            message = api.send_message(283751583177637888, message)
            self.log('>> ' + message.content)

    def loop(self):
        subreddits = self.time_log('Getting subreddits list',
                                   self.db.smembers,
                                   'Reddit.#:subs')

        guilds = self.time_log('Getting guilds', self.get_guilds)

        subreddits_map = defaultdict(list)
        for guild in guilds:
            for subreddit in guild.config.subreddits:
                subreddits_map[subreddit].append(guild)

        subreddits_posts = {}
        for subs in chunk(subreddits, 100):
            posts = self.time_log('Getting {} posts'.format(subs),
                                  self.get_posts, subs)
            subreddits_posts.update(posts)

        for subreddit, guilds in subreddits_map.items():
            posts = subreddits_posts.get(subreddit, ())

            for guild in guilds: self.announce(posts, guild)

            gevent.sleep(3)

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

