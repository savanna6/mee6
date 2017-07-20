from mee6.utils import get_plugins, get
from flask import Flask, request, jsonify, abort
from functools import wrap
from modus.exceptions import ValidationError
from modus import Model
from modus.fields import Integer, String

app = Flask(__name__)

plugins = get_plugins(in_bot=False)

def get_plugin_or_abort(gid, pid):
    try:
        plugin = next(plugin for plugin in plugins if plugin.id == pid)
    except StopIteration:
        return abort(404)

    return plugin

def get_plugin_command_or_abort(plugin, command_name):
    try:
        command = next(command for command in plugin.commands if command.name == command_name)
    except StopIteration:
        return abort(404)

    return command

def get_token(): return request.headers.get('Authorization')

def get_discord_token(token):
    return rdb.get('token:{}:discord_token'.format(token))

def reset_token(token):
    rdb.delete('token:{}:discord_token'.format(token))
    rdb.delete('token:{}'.format(token))

def get_user_guilds(token):
    discord_token = get_discord_token(token)
    discord = make_session(discord_token)
    r = discord.get(DISCORD_API_BASE_URL + '/users/@me/guilds')
    if r.status_code != 200:
        reset_token(token)
        return abort(401)
    return r.json()

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = get_token()
        if token is None:
            return abort(401)

        is_expired = rdb.get('token:{}'.format(token)) is None
        if is_expired:
            return abort(401)

        return f(*args, **kwargs)
    return wrapper

def require_bot_master(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Fetch managed guilds
        user_guilds = get_user_guilds(token)
        predicate = lambda guild: g['owner'] is True or ((int(g['permissions']) >> 5) & 1)
        managed_guilds = [guild for guild in user_guilds in predicate(guild)]

        # Check if current guilds in managed guilds
        gid = kwargs.get('gid')
        if str(gid) not in map(lambda g: g.id, managed_guilds):
            return abort(403)

        return f(*args, **kwargs)

@app.route('/')
def root():
    return jsonify({'hello': 'world'})

@app.route('/plugins')
def get_plugins():
    return jsonify([plugin.to_dict() for plugin in plugins])

@app.route('/guilds/<int:gid>/plugins')
def get_guild_plugins(gid):
    return jsonify([plugin.to_dict(gid) for plugin in plugins])

@app.route('/guilds/<int:gid>/plugins/<string:pid>')
def get_guild_plugin(gid, pid):
    plugin = get_plugin_or_abort(gid, pid)
    return jsonify(plugin.to_dict(gid))

@app.route('/guilds/<int:gid>/plugins/<string:pid>', methods=['PATCH'])
def patch_guild_plugin(gid, pid):
    data = request.json
    enabled = data.get('enabled')
    if enabled is None:
        abort(400)

    plugin = get_plugin_or_abort(gid, pid)
    if enabled:
        plugin.enable(gid)
    else:
        plugin.disable(gid)

    return jsonify(plugin.to_dict(gid))

@app.route('/guilds/<int:gid>/plugins/<string:pid>/commands')
def get_guild_plugin_commands(gid, pid):
    plugin = get_plugin_or_abort(gid, pid)
    return jsonify(plugin.to_dict(gid)['commands'])

@app.route('/guilds/<int:gid>/plugins/<string:pid>/commands/<string:command_name>')
def get_guild_plugin_command(gid, pid, command_name):
    plugin = get_plugin_or_abort(gid, pid)
    command = get_plugin_command_or_abort(plugin, command_name)
    return jsonify(command.to_dict(gid))

@app.route('/guilds/<int:gid>/plugins/<string:pid>/commands/<string:command_name>/config')
def get_guild_plugin_command_config(gid, pid, command_name):
    plugin = get_plugin_or_abort(gid, pid)
    command = get_plugin_command_or_abort(plugin, command_name)
    return jsonify(command.to_dict(gid)['config'])

@app.route('/guilds/<int:gid>/plugins/<string:pid>/commands/<string:command_name>/config',
           methods=['PATCH'])
def patch_guild_plugin_command_config(gid, pid, command_name):
    plugin = get_plugin_or_abort(gid, pid)
    command = get_plugin_command_or_abort(plugin, command_name)
    data = request.json

    try:
        command.patch_config(gid, request.json)
    except ValidationError as e:
        return jsonify({'errors': e.errors}), 400

    return jsonify(command.to_dict(gid)['config'])

@app.route('/guilds/<int:gid>/plugins/<string:pid>/commands/<string:command_name>/config',
           methods=['DELETE'])
def delete_guild_plugin_command_config(gid, pid, command_name):
    plugin = get_plugin_or_abort(gid, pid)
    command = get_plugin_command_or_abort(plugin, command_name)
    command.delete_config(gid)
    return jsonify({}), 200


@app.route('/guilds/<int:gid>/plugins/<string:pid>/config')
def get_guild_plugin_config(gid, pid):
    plugin = get_plugin_or_abort(gid, pid)
    return jsonify(plugin.to_dict(gid)['config'])

@app.route('/guilds/<int:gid>/plugins/<string:pid>/config', methods=['PATCH'])
def patch_guild_plugin_config(gid, pid):
    plugin = get_plugin_or_abort(gid, pid)
    data = request.json
    plugin.patch_config(gid, data)
    return jsonify(plugin.to_dict(gid)['config'])


if __name__ == '__main__':
    app.debug = True
    app.run()
