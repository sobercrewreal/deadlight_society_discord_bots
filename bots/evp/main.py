import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from cogs import interject, memory, status
from shared import db as db_module
from shared.pacing import HauntPacer

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("evp")

intents = discord.Intents.default()
intents.message_content = True

DB_PATH = "/app/data/evp.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS interjections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    victim_id TEXT,
    happened_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory (
    guild_id TEXT PRIMARY KEY,
    content TEXT NOT NULL DEFAULT '',
    last_digest_at TEXT
);
"""

EXCLUDED_CHANNEL_IDS = {int(x) for x in os.environ.get("EVP_EXCLUDED_CHANNEL_IDS", "").split(",") if x}
EXCLUDED_MEMBER_IDS = {x.strip() for x in os.environ.get("EVP_EXCLUDED_MEMBER_IDS", "").split(",") if x.strip()}
COOLDOWN_MINUTES = int(os.environ.get("EVP_COOLDOWN_MINUTES", "20"))
DAILY_CAP = int(os.environ.get("EVP_DAILY_CAP", "15"))


class EVPBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.db = None
        self.pacer = None
        self.digest_loop = None

    async def setup_hook(self):
        self.db = await db_module.connect(DB_PATH, SCHEMA)
        self.pacer = HauntPacer(self.db, COOLDOWN_MINUTES, DAILY_CAP, table="interjections")

        interject.register(self, self.db, self.pacer, EXCLUDED_CHANNEL_IDS, EXCLUDED_MEMBER_IDS)
        status.register_memory_command(self.tree, self.db)
        status.register_test_command(self.tree, self, self.db)

        self.digest_loop = memory.build_loop(self, self.db, EXCLUDED_CHANNEL_IDS)
        await self.tree.sync()


client = EVPBot()


@client.tree.command(name="evp", description="...is anyone there?")
async def evp(interaction: discord.Interaction):
    await interaction.response.send_message("...can you hear this...")


@client.event
async def on_ready():
    log.info("Logged in as %s (id=%s)", client.user, client.user.id)
    if not client.digest_loop.is_running():
        client.digest_loop.start()


if __name__ == "__main__":
    token = os.environ["EVP_DISCORD_TOKEN"]
    client.run(token)
