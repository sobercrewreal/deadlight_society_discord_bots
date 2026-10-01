import discord
from discord import app_commands

from shared import llm_client


def register_memory_command(tree: app_commands.CommandTree, db):
    @tree.command(name="evp_memory", description="What does EVP currently remember?")
    async def evp_memory(interaction: discord.Interaction):
        async with db.execute(
            "SELECT content FROM memory WHERE guild_id = ?", (str(interaction.guild_id),)
        ) as cursor:
            row = await cursor.fetchone()
        memory = row[0] if row and row[0] else None
        if not memory:
            await interaction.response.send_message("...nothing yet... static...")
            return
        await interaction.response.send_message(f"```{memory[:1900]}```")


def register_test_command(tree: app_commands.CommandTree, client: discord.Client, db):
    @tree.command(
        name="evp_test",
        description="Force EVP to interject right now, to check the mechanism is working",
    )
    async def evp_test(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        async with db.execute(
            "SELECT content FROM memory WHERE guild_id = ?", (str(interaction.guild_id),)
        ) as cursor:
            row = await cursor.fetchone()
        memory = row[0] if row and row[0] else ""

        recent = [
            f"{m.author.display_name}: {m.content}"
            async for m in interaction.channel.history(limit=15)
            if m.content
        ]
        recent.reverse()

        line = await llm_client.generate_evp_interjection(memory, "\n".join(recent))
        await interaction.channel.send(line)
        await interaction.followup.send("...sent...", ephemeral=True)
