import asyncio
import logging
import random
from pathlib import Path

import discord
from discord import app_commands

log = logging.getLogger("haunt.vc_yank")

AUDIO_DIR = Path(__file__).resolve().parent.parent / "audio"

TIERS = {
    "quiet": AUDIO_DIR / "quiet",
    "normal": AUDIO_DIR / "normal",
    "high": AUDIO_DIR / "high",
}


def meter_tier(week_count: int) -> str:
    if week_count <= 2:
        return "quiet"
    if week_count <= 5:
        return "normal"
    return "high"


def _pick_clip(tier: str) -> Path | None:
    folder = TIERS.get(tier)
    if folder is None or not folder.exists():
        return None
    clips = [p for p in folder.iterdir() if p.suffix.lower() == ".mp3"]
    return random.choice(clips) if clips else None


async def yank(client: discord.Client, member: discord.Member, haunted_vc_id: int, tier: str):
    original_channel = member.voice.channel if member.voice else None
    if original_channel is None:
        return

    haunted_channel = member.guild.get_channel(haunted_vc_id)
    if haunted_channel is None:
        log.warning("Haunted VC %s not found", haunted_vc_id)
        return

    clip = _pick_clip(tier)

    try:
        await member.move_to(haunted_channel, reason="Haunt Bot")
    except discord.HTTPException as exc:
        log.warning("Could not move %s into the haunted VC: %s", member.display_name, exc)
        return

    try:
        voice_client = await haunted_channel.connect()
        try:
            if clip is not None:
                finished = asyncio.Event()

                def _after(error):
                    if error:
                        log.warning("Playback error: %s", error)
                    client.loop.call_soon_threadsafe(finished.set)

                voice_client.play(discord.FFmpegPCMAudio(str(clip)), after=_after)
                await asyncio.wait_for(finished.wait(), timeout=30)
            else:
                await asyncio.sleep(5)
        finally:
            await voice_client.disconnect()
    except (discord.HTTPException, discord.ClientException, asyncio.TimeoutError) as exc:
        log.warning("Voice playback failed: %s", exc)
    finally:
        try:
            await member.move_to(original_channel, reason="Haunt Bot return")
        except discord.HTTPException as exc:
            log.warning("Could not move %s back: %s", member.display_name, exc)


def register_status_command(tree: app_commands.CommandTree, pacer):
    @tree.command(name="ghost_status", description="How haunted has this server been lately?")
    async def ghost_status(interaction: discord.Interaction):
        count = await pacer.week_count(str(interaction.guild_id))
        tier = meter_tier(count)
        await interaction.response.send_message(
            f"**{count}** hauntings in the last 7 days — currently running **{tier}**."
        )


def register_test_command(tree: app_commands.CommandTree, client: discord.Client, haunted_vc_id: int):
    @tree.command(name="test", description="Trigger a haunt on yourself right now, to check the bot is working")
    async def test(interaction: discord.Interaction):
        member = interaction.user
        if member.voice is None or member.voice.channel is None:
            await interaction.response.send_message(
                "You need to be in a voice channel to test this.", ephemeral=True
            )
            return
        tier = random.choice(list(TIERS.keys()))
        await interaction.response.send_message(f"Haunting you now (tier: {tier})...", ephemeral=True)
        await yank(client, member, haunted_vc_id, tier)
