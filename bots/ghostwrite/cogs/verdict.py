import datetime

import discord
from discord import app_commands


def register(tree: app_commands.CommandTree, db):
    @tree.command(name="verdict", description="Guess whether today's ghost story is real or fake")
    @app_commands.describe(guess="Is the current story real or fake?")
    @app_commands.choices(
        guess=[
            app_commands.Choice(name="real", value="real"),
            app_commands.Choice(name="fake", value="fake"),
        ]
    )
    async def verdict(interaction: discord.Interaction, guess: app_commands.Choice[str]):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        async with db.execute(
            "SELECT id FROM stories WHERE guild_id = ? AND revealed = 0 AND reveal_at > ? "
            "ORDER BY posted_at DESC LIMIT 1",
            (str(interaction.guild_id), now),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            await interaction.response.send_message(
                "There's no active story to vote on right now.", ephemeral=True
            )
            return

        story_id = row[0]
        guess_value = 1 if guess.value == "real" else 0

        await db.execute(
            "INSERT INTO votes (story_id, user_id, guess) VALUES (?, ?, ?) "
            "ON CONFLICT(story_id, user_id) DO UPDATE SET guess = excluded.guess",
            (story_id, str(interaction.user.id), guess_value),
        )
        await db.commit()

        await interaction.response.send_message(
            f"Vote recorded: **{guess.value}**. Check back when the story's revealed.",
            ephemeral=True,
        )
