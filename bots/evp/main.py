import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("evp")

intents = discord.Intents.default()


class EVPBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


client = EVPBot()


@client.tree.command(name="evp", description="...is anyone there?")
async def evp(interaction: discord.Interaction):
    await interaction.response.send_message("...can you hear this...")


@client.event
async def on_ready():
    log.info("Logged in as %s (id=%s)", client.user, client.user.id)


if __name__ == "__main__":
    token = os.environ["EVP_DISCORD_TOKEN"]
    client.run(token)
