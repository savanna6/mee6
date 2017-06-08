from mee6 import Plugin
from mee6.discord import get_channel_messages, send_message, get_current_user
from time import time
from mee6.utils import timed
from mee6.exceptions import APIException

import hashlib
import math
import traceback


class Timers(Plugin):

    id = "timers"
    name = "Timers"
    description = "Send messages at specific intervals"

    timers_ids = {}

    me = get_current_user()

    def get_default_config(self, guild_id):
        default_config = {'timers': []}
        return default_config

    @Plugin.loop(sleep_time=0)
    def loop(self):
        for guild in self.get_guilds():
            with timed('timer_delay'):
                for timer in guild.config['timers']:
                    try:
                        self.process_timer(timer)
                    except Exception as e:
                        traceback.print_exc()

    def get_all_timers(self):
        return [timer for guild in self.get_guilds() for timer in guild.config['timers']]

    def get_timer_id(self, timer_message, timer_interval, channel):
        """ since storing timer ids on config is meh, i'm just using a hash.
        two identical timers will collision. But we don't care here."""

        phrase = '{}.{}.{}'.format(timer_message, timer_interval, channel)
        timer_id = self.timers_ids.get(phrase)
        if timer_id:
            return timer_id

        timer_id = hashlib.sha224(phrase.encode('utf-8')).hexdigest()
        self.timers_ids[phrase] = timer_id
        return timer_id

    def process_timer(self, timer):
        now = time()
        message = timer['message']
        channel = timer['channel']
        interval = timer['interval']
        timer_id = self.get_timer_id(message, interval, channel)

        last_post_timestamp = self.db.get('plugin.timers.{}.last_post_timestamp'.format(timer_id))
        last_post_timestamp = int(last_post_timestamp or 0)

        if last_post_timestamp + timer['interval'] > now:
            return

        last_messages = get_channel_messages(channel, limit=1)
        if len(last_messages) > 0:
            last_message = last_messages[-1]
            if last_message.author.id == self.me.id:
                return

        now = math.floor(time())
        self.db.set('plugin.timers.{}.last_post_timestamp'.format(timer_id), now)

        try:
            post_message = send_message(channel, message)
            self.log('Announcing timer message ({} interval) in {}'.format(interval, channel))
        except APIException as e:
            self.log('Couldn\'t announce timer message ({} interval) in {}, error: {}'.format(interval, channel, e.payload))
