import discord
from discord import app_commands


def register(tree: app_commands.CommandTree, db):
    @tree.command(name="leaderboard", description="See who's best at spotting real vs fake ghost stories")
    async def leaderboard(interaction: discord.Interaction):
        async with db.execute(
            "SELECT v.user_id, "
            "SUM(CASE WHEN v.guess = s.is_real THEN 1 ELSE 0 END) AS correct, "
            "COUNT(*) AS total "
            "FROM votes v "
            "JOIN stories s ON s.id = v.story_id "
            "WHERE s.guild_id = ? AND s.revealed = 1 "
            "GROUP BY v.user_id "
            "ORDER BY correct DESC, total DESC",
            (str(interaction.guild_id),),
        ) as cursor:
            rows = await cursor.fetchall()

        if not rows:
            await interaction.response.send_message("No revealed stories to score yet.", ephemeral=True)
            return

        lines = []
        for i, (user_id, correct, total) in enumerate(rows, start=1):
            pct = round(100 * correct / total)
            lines.append(f"{i}. <@{user_id}> — {correct}/{total} ({pct}%)")

        embed = discord.Embed(title="Ghost Write Leaderboard", description="\n".join(lines))
        await interaction.response.send_message(embed=embed)
