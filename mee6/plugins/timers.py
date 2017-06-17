from mee6 import Plugin
from mee6.discord import get_channel_messages, send_webhook_message, send_message, get_current_user
from time import time
from mee6.utils import timed
from mee6.exceptions import APIException
from gevent.lock import Semaphore

import hashlib
import math
import traceback
import gevent


class Timers(Plugin):

    id = "timers"
    name = "Timers"
    description = "Send messages at specific intervals"

    _lock = Semaphore(value=10)

    timers_ids = {}

    guild_jobs = {}

    def get_default_config(self, guild_id):
        default_config = {'timers': []}
        return default_config

    @Plugin.loop(sleep_time=0)
    def loop(self):
        guilds = self.get_guilds()
        self.log('Got {} guilds'.format(len(guilds)))
        job_count = 0
        for guild in guilds:
            job = self.guild_jobs.get(guild.id)
            if job is None or job.ready():
                self.guild_jobs[guild.id] = gevent.spawn(self.process_timers, guild)
                job_count += 1
        self.log('Relaunched {} jobs out of {}'.format(job_count,
                                                       len(self.guild_jobs.keys())))

    def process_timers(self, guild):
        for timer in guild.config['timers']:
            try:
                self.process_timer(timer)
            except APIException as e:
                self.log('Got Api exception {} {}'.format(e.status_code, e.payload))

                # Disabling the plugin in case of an error
                # Unauthorized or channel not found
                if e.status_code in (403, 404):
                    self.log('Disabling plugin for {}'.format(guild.id))
                    self.disable(guild)

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

        if now - last_post_timestamp < timer['interval']:
            return

        with self._lock:
            last_messages = get_channel_messages(channel, limit=1)

        if len(last_messages) > 0:
            last_message = last_messages[-1]
            if self.db.sismember('plugin.timers.webhooks', last_message.webhook_id):
                return

        now = math.floor(time())

        self.db.set('plugin.timers.{}.last_post_timestamp'.format(timer_id), now)

        webhook_id = 'timers:{}'.format(channel)

        post_message = send_webhook_message(webhook_id, channel, message)

        self.db.sadd('plugin.timers.webhooks', post_message.webhook_id)

        self.log('Announcing timer message ({} interval) in {}'.format(interval, channel))

