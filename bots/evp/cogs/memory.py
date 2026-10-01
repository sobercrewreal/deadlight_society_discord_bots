import datetime
import logging

from discord.ext import tasks

from shared import llm_client

log = logging.getLogger("evp.memory")

DIGEST_INTERVAL_HOURS = 24
HISTORY_LIMIT_PER_CHANNEL = 300


def build_loop(client, db, excluded_channel_ids: set[int]):
    @tasks.loop(hours=DIGEST_INTERVAL_HOURS)
    async def digest():
        now = datetime.datetime.now(datetime.timezone.utc)

        for guild in client.guilds:
            async with db.execute(
                "SELECT content, last_digest_at FROM memory WHERE guild_id = ?",
                (str(guild.id),),
            ) as cursor:
                row = await cursor.fetchone()

            current_memory = row[0] if row else ""
            since = (
                datetime.datetime.fromisoformat(row[1])
                if row and row[1]
                else now - datetime.timedelta(hours=DIGEST_INTERVAL_HOURS)
            )

            lines = []
            for channel in guild.text_channels:
                if channel.id in excluded_channel_ids:
                    continue
                try:
                    async for message in channel.history(after=since, limit=HISTORY_LIMIT_PER_CHANNEL):
                        if message.author.bot or not message.content:
                            continue
                        lines.append(f"#{channel.name} {message.author.display_name}: {message.content}")
                except Exception as exc:
                    log.warning("Could not read history for #%s: %s", channel.name, exc)

            if not lines:
                continue

            try:
                updated_memory = await llm_client.generate_evp_digest(current_memory, "\n".join(lines))
            except Exception as exc:
                log.warning("Digest generation failed for guild %s: %s", guild.id, exc)
                continue

            await db.execute(
                "INSERT INTO memory (guild_id, content, last_digest_at) VALUES (?, ?, ?) "
                "ON CONFLICT(guild_id) DO UPDATE SET content = excluded.content, "
                "last_digest_at = excluded.last_digest_at",
                (str(guild.id), updated_memory, now.isoformat()),
            )
            await db.commit()
            log.info("Updated memory for guild %s (%d chars)", guild.id, len(updated_memory))

    return digest
