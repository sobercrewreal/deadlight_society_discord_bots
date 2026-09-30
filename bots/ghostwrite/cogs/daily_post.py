import datetime
import logging
import random
from zoneinfo import ZoneInfo

from discord.ext import tasks

from shared import llm_client

log = logging.getLogger("ghostwrite.daily_post")

POST_TIME = datetime.time(hour=18, minute=0, tzinfo=ZoneInfo("America/Chicago"))


def build_loops(client, db, channel_id: int):
    @tasks.loop(time=POST_TIME)
    async def post_daily_story():
        channel = client.get_channel(channel_id)
        if channel is None:
            log.warning("Configured channel %s not found", channel_id)
            return

        is_real = random.random() < 0.5
        content = await llm_client.generate_story(is_real)

        message = await channel.send(
            "**A story from the other side...**\n\n"
            f"{content}\n\n"
            "Real or fake? Vote with `/verdict` — the truth comes out in 24 hours."
        )

        posted_at = datetime.datetime.now(datetime.timezone.utc)
        reveal_at = posted_at + datetime.timedelta(hours=24)
        await db.execute(
            "INSERT INTO stories (guild_id, channel_id, message_id, posted_at, reveal_at, is_real, content) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(channel.guild.id),
                str(channel.id),
                str(message.id),
                posted_at.isoformat(),
                reveal_at.isoformat(),
                int(is_real),
                content,
            ),
        )
        await db.commit()

    @tasks.loop(minutes=5)
    async def reveal_due_stories():
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        async with db.execute(
            "SELECT id, channel_id, is_real FROM stories WHERE revealed = 0 AND reveal_at <= ?",
            (now,),
        ) as cursor:
            due = await cursor.fetchall()

        for story_id, channel_id_str, is_real in due:
            channel = client.get_channel(int(channel_id_str))
            if channel is not None:
                async with db.execute(
                    "SELECT user_id, guess FROM votes WHERE story_id = ?", (story_id,)
                ) as cursor:
                    votes = await cursor.fetchall()

                answer = "REAL" if is_real else "FAKE"
                lines = [f"**The truth: that story was {answer}.**"]
                correct_ids = [uid for uid, guess in votes if guess == is_real]
                if not votes:
                    lines.append("Nobody voted on this one.")
                elif correct_ids:
                    mentions = ", ".join(f"<@{uid}>" for uid in correct_ids)
                    lines.append(f"Got it right: {mentions}")
                else:
                    lines.append("Nobody guessed right that time.")

                await channel.send("\n".join(lines))

            await db.execute("UPDATE stories SET revealed = 1 WHERE id = ?", (story_id,))

        if due:
            await db.commit()

    return post_daily_story, reveal_due_stories
