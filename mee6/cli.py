from gevent import monkey
monkey.patch_all()

import click
import mee6.plugins

@click.command('')
@click.argument('plugin_name')
def run(plugin_name):
    plugins_name = plugin_name.capitalize()
    plugin =  getattr(mee6.plugins, plugin_name)()

    plugin.run()

run()
