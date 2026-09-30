import logging
import random

import discord
from discord.ext import tasks

from . import vc_yank

log = logging.getLogger("haunt.scheduler")

TICK_MINUTES = 5
FIRE_PROBABILITY = 0.15


def build_loop(client: discord.Client, pacer, haunted_vc_id: int, excluded_vc_ids: set[int]):
    @tasks.loop(minutes=TICK_MINUTES)
    async def tick():
        for guild in client.guilds:
            if not await pacer.eligible(str(guild.id)):
                continue

            eligible_members = [
                member
                for vc in guild.voice_channels
                if vc.id not in excluded_vc_ids
                for member in vc.members
                if not member.bot
            ]
            if not eligible_members:
                continue

            if random.random() >= FIRE_PROBABILITY:
                continue

            last_victim_id = await pacer.last_victim(str(guild.id))
            pool = [m for m in eligible_members if str(m.id) != last_victim_id] or eligible_members
            victim = random.choice(pool)

            week_count = await pacer.week_count(str(guild.id))
            tier = vc_yank.meter_tier(week_count)

            log.info("Haunting %s (tier=%s)", victim.display_name, tier)
            await vc_yank.yank(client, victim, haunted_vc_id, tier)
            await pacer.record(str(guild.id), "vc_yank", str(victim.id))

    return tick
