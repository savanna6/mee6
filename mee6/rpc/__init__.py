from mee6.rpc.client import RPCClient

client = RPCClient()
get_guild = client.get_guild
get_guild_members = client.get_guild_members
get_guild_member = client.get_guild_member
voice_connect = client.voice_connect
voice_play = client.voice_play
voice_stop = client.voice_stop
voice_disconnect = client.voice_disconnect
