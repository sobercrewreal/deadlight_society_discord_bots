import logging
import random

import discord

from shared import llm_client

log = logging.getLogger("evp.interject")

MESSAGE_INTERJECT_CHANCE = 0.03
HISTORY_CONTEXT_LIMIT = 15


def register(
    client: discord.Client,
    db,
    pacer,
    excluded_channel_ids: set[int],
    excluded_member_ids: set[str],
):
    @client.event
    async def on_message(message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        if message.channel.id in excluded_channel_ids:
            return
        if str(message.author.id) in excluded_member_ids:
            return
        if random.random() >= MESSAGE_INTERJECT_CHANCE:
            return
        if not await pacer.eligible(str(message.guild.id)):
            return

        async with db.execute(
            "SELECT content FROM memory WHERE guild_id = ?", (str(message.guild.id),)
        ) as cursor:
            row = await cursor.fetchone()
        memory = row[0] if row and row[0] else ""

        recent = [
            f"{m.author.display_name}: {m.content}"
            async for m in message.channel.history(limit=HISTORY_CONTEXT_LIMIT)
            if m.content
        ]
        recent.reverse()

        try:
            line = await llm_client.generate_evp_interjection(memory, "\n".join(recent))
        except Exception as exc:
            log.warning("Interjection generation failed: %s", exc)
            return

        await message.channel.send(line)
        await pacer.record(str(message.guild.id), "interject")
