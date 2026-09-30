import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ghostwrite")

intents = discord.Intents.default()


class GhostWriteBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


client = GhostWriteBot()


@client.event
async def on_ready():
    log.info("Logged in as %s (id=%s)", client.user, client.user.id)


@client.tree.command(name="ping", description="Check that Ghost Write is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong from the other side")


if __name__ == "__main__":
    token = os.environ["GHOSTWRITE_DISCORD_TOKEN"]
    client.run(token)
