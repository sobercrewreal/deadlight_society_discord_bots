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

SCHEMA = """
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    posted_at TEXT NOT NULL,
    reveal_at TEXT NOT NULL,
    is_real INTEGER NOT NULL,
    content TEXT NOT NULL,
    revealed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS votes (
    story_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    guess INTEGER NOT NULL,
    PRIMARY KEY (story_id, user_id)
);
"""


class GhostWriteBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.db = None
        self.post_loop = None
        self.reveal_loop = None

    async def setup_hook(self):
        self.db = await db_module.connect(DB_PATH, SCHEMA)
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
