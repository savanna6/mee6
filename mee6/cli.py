from gevent import monkey
monkey.patch_all(httplib=True)

from mee6.utils import get, init_dd_agent
from mee6 import worker as mee6_worker

import click
import mee6.plugins

init_dd_agent()

@click.group()
def cli(): pass

@cli.command('run')
@click.argument('plugin_name')
def plugin(plugin_name):
    plugins_name = plugin_name.capitalize()
    plugin =  get(mee6.plugins, plugin_name)()

    plugin.run()

@cli.command('workers')
@click.argument('plugins', nargs=-1)
def worker(plugins):
    plugins = [get(mee6.plugins, plugin_name) for plugin_name in plugins]

    mee6_worker.run(*plugins)

@cli.command('api')
def api():
    from mee6.api.api import app
    app.run()

cli()
