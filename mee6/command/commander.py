from mee6.utils import get
from mee6.command import Command


class Commander:
    def __init__(self, commands=[], db=None, db_prefix=''):
        self.commands = commands
        self.db_prefix = db_prefix
        self.db = db

    def execute_commands(self, guild, message):
        for command in self.commands:
            command.execute(guild, message)

