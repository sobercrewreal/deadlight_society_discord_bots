import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from cogs import scheduler, teleport, vc_yank
from shared import db as db_module
from shared.pacing import HauntPacer

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("haunt")

intents = discord.Intents.default()
intents.message_content = True

DB_PATH = "/app/data/haunt.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS haunts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    victim_id TEXT,
    happened_at TEXT NOT NULL
);
"""

DESTINATION_CHANNEL_ID = int(os.environ["HAUNT_DESTINATION_CHANNEL_ID"])
HAUNTED_VC_ID = int(os.environ["HAUNT_VC_ID"])
EXCLUDED_VC_IDS = {int(x) for x in os.environ.get("HAUNT_EXCLUDED_VC_IDS", "").split(",") if x}
EXCLUDED_MEMBER_IDS = {x.strip() for x in os.environ.get("HAUNT_EXCLUDED_MEMBER_IDS", "").split(",") if x.strip()}
COOLDOWN_MINUTES = int(os.environ.get("HAUNT_COOLDOWN_MINUTES", "27"))
DAILY_CAP = int(os.environ.get("HAUNT_DAILY_CAP", "3"))


class HauntBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.db = None
        self.pacer = None
        self.tick_loop = None

    async def setup_hook(self):
        self.db = await db_module.connect(DB_PATH, SCHEMA)
        self.pacer = HauntPacer(self.db, COOLDOWN_MINUTES, DAILY_CAP)

        teleport.register(
            self, self.pacer, EXCLUDED_VC_IDS, DESTINATION_CHANNEL_ID, EXCLUDED_MEMBER_IDS
        )
        vc_yank.register_status_command(self.tree, self.pacer)
        vc_yank.register_test_command(self.tree, self, HAUNTED_VC_ID)
        vc_yank.register_haunt_command(
            self.tree,
            self,
            self.pacer,
            HAUNTED_VC_ID,
            EXCLUDED_VC_IDS | {HAUNTED_VC_ID},
            EXCLUDED_MEMBER_IDS,
        )

        self.tick_loop = scheduler.build_loop(
            self, self.pacer, HAUNTED_VC_ID, EXCLUDED_VC_IDS | {HAUNTED_VC_ID}, EXCLUDED_MEMBER_IDS
        )
        await self.tree.sync()


client = HauntBot()


@client.event
async def on_ready():
    log.info("Logged in as %s (id=%s)", client.user, client.user.id)
    if not client.tick_loop.is_running():
        client.tick_loop.start()


if __name__ == "__main__":
    token = os.environ["HAUNT_DISCORD_TOKEN"]
    client.run(token)
