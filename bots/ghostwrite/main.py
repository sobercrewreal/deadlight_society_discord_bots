import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from cogs import daily_post, leaderboard, verdict
from shared import db as db_module

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ghostwrite")

intents = discord.Intents.default()

DB_PATH = "/app/data/ghostwrite.db"
CHANNEL_ID = int(os.environ["GHOSTWRITE_CHANNEL_ID"])


class GhostWriteBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.db = None
        self.post_loop = None
        self.reveal_loop = None

    async def setup_hook(self):
        self.db = await db_module.connect(DB_PATH)
        verdict.register(self.tree, self.db)
        leaderboard.register(self.tree, self.db)
        self.post_loop, self.reveal_loop = daily_post.build_loops(self, self.db, CHANNEL_ID)
        await self.tree.sync()


client = GhostWriteBot()


@client.event
async def on_ready():
    log.info("Logged in as %s (id=%s)", client.user, client.user.id)
    if not client.post_loop.is_running():
        client.post_loop.start()
    if not client.reveal_loop.is_running():
        client.reveal_loop.start()


if __name__ == "__main__":
    token = os.environ["GHOSTWRITE_DISCORD_TOKEN"]
    client.run(token)
