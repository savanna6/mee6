import requests
from mee6 import Plugin
from mee6.command import Command, Response


class Utils(Plugin):
    @Command.register('!spoopy <url:string>')
    def spoopy(self, ctx, url):
        r = requests.get("https://spoopy.link/api/v1/{}".format(url)).json()
        if r.status_code != 200:
            return Response.not_found(
                "There was an error calling the spoopy.link api")
        root = r["chain"][0]["url"]
        chain = " -> ".join("{1}<{0}>{1}".format(
            x["url"], "" if x["safe"] else "**") for x in r["chain"])
        if r["safe"]:
            return Response.ok("**__<{}>__ is safe!**".format(root))
        return Response.ok("""**__<{}>__ is unsafe!**\nChain: {}\n
(You can also type `https://spoopy.link/<url>` in chat for an instant report!)
""".format(root, chain))
