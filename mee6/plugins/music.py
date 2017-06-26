from mee6 import Plugin
from mee6.rpc import voice_connect, voice_disconnect, voice_play, voice_stop
from mee6.command import Command, Response
from youtube_dl.utils import YoutubeDLError

import json
import youtube_dl
import os
import requests


YTDL_OPTS = {'format': 'webm[abr>0]/bestaudio/best',}

class Music(Plugin):
    id = "music"
    name = "Music"
    buff = True

    is_global = True

    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

    def get_music_info(self, music_url):
        ydl = youtube_dl.YoutubeDL(YTDL_OPTS)

        try:
            info = ydl.extract_info(music_url, download=False)
        except YoutubeDLError as e:
            return None

        if "entries" in info:
            info = info['entries'][0]

        music_info = {'name': info.get('title', ''),
                      'download_url': info.get('url'),
                      'url': music_url,
                      'description': info.get('description', ''),}

        return music_info

    def get_youtube_url(self, music):
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {'type': 'video',
                  'q': music,
                  'part': 'snippet',
                  'key': self.GOOGLE_API_KEY}
        r = requests.get(url, params=params)
        data = r.json()

        items = data.get('items')
        if items is None or len(items) == 0:
            return None

        video_url = "https://youtube.com/watch?v=" + items[0]["id"]["videoId"]
        return video_url

    def add_to_queue(self, guild, author, music_info):
        key = 'music.{}.music_queue'.format(guild.id)
        music_info['author'] = author.user.id
        self.db.lpush(key, json.dumps(music_info))

    def pop_music(self, guild):
        key = 'music.{}.music_queue'.format(guild.id)
        data = self.db.rpop(key)
        if not data:
            return None

        return json.loads(data)

    def get_default_config(self, guild_id):
        pass

    @Command.register('!add <music:str>')
    def add(self, ctx, music):
        if not music.startswith('http'):
            music = self.get_youtube_url(music)
            if not music:
                message = "Didn't find anything 😟 ."
                return Response.not_found(message)

        music_info = self.get_music_info(music)
        if not music_info:
            message = "Didn't find anything about that link 😟 ."
            return Response.not_found(message)

        self.add_to_queue(ctx.guild, ctx.author, music_info)

        message = "**{}'** added! 👌 ".format(music_info['name'])
        return Response.ok(message)

    @Command.register('!join')
    def join(self, ctx):
        voice_channel = ctx.author.get_voice_channel(ctx.guild)
        if not voice_channel:
            message = "You are not in a voice channel. Please join a voice " \
                      "channel and type !join again 🙏 "
            return Response.missing_requirements(message)

        if not voice_connect(ctx.guild.id, voice_channel.id):
            message = "Oops, something went wrong in Mee6 land! Please " \
                      "contact our support if it happens again 🙏 ."
            return Response.internal_error(message)

        message = "Connecting to **#{0.name}**...".format(voice_channel)
        return Response.ok(message)

    @Command.register('!play')
    def play(self, ctx):
        music = self.pop_music(ctx.guild)
        if music is None:
            message = "There's nothing to play mate 🙃 "
            return Response.not_found(message)

        if not voice_play(ctx.guild, music['download_url']):
            return Response.internal_error()

    @Command.register('!stop')
    def stop(self, ctx):
        voice_stop(ctx.guild)

    @Command.register('!leave')
    def leave(self, ctx):
        voice_disconnect(ctx.guild)
