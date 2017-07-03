from mee6.utils import get_plugins, get
from flask import Flask, request, jsonify, abort
from modus.exceptions import ValidationError

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
