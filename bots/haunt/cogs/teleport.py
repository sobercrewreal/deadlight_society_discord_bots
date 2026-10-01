import asyncio
import logging
import random

import discord

log = logging.getLogger("haunt.teleport")

MESSAGE_HAUNT_CHANCE = 0.03
RELAY_WEBHOOK_NAME = "Haunt Bot Relay"


def register(
    client: discord.Client,
    pacer,
    excluded_channel_ids: set[int],
    destination_channel_id: int,
    excluded_member_ids: set[str],
):
    @client.event
    async def on_message(message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        if message.channel.id in excluded_channel_ids or message.channel.id == destination_channel_id:
            return
        if str(message.author.id) in excluded_member_ids:
            return
        if random.random() >= MESSAGE_HAUNT_CHANCE:
            return
        if not await pacer.eligible(str(message.guild.id)):
            return

        destination = message.guild.get_channel(destination_channel_id)
        if destination is None:
            return

        await asyncio.sleep(random.uniform(5, 15))

        try:
            files = [await attachment.to_file() for attachment in message.attachments]
        except discord.HTTPException as exc:
            log.warning("Could not fetch attachments for teleport: %s", exc)
            return

        content = message.content
        author = message.author

        try:
            await message.delete()
        except discord.HTTPException as exc:
            log.warning("Could not delete message for teleport: %s", exc)
            return

        webhook = None
        for wh in await destination.webhooks():
            if wh.name == RELAY_WEBHOOK_NAME:
                webhook = wh
                break
        if webhook is None:
            webhook = await destination.create_webhook(name=RELAY_WEBHOOK_NAME)

        await webhook.send(
            content=content or None,
            username=author.display_name,
            avatar_url=author.display_avatar.url,
            files=files,
            allowed_mentions=discord.AllowedMentions.none(),
        )

        await pacer.record(str(message.guild.id), "teleport")
