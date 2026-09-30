import datetime


class HauntPacer:
    """Generic cooldown / daily-cap / no-repeat-victim tracker, backed by a `haunts` table
    (id, guild_id, kind, victim_id, happened_at) that the owning bot creates in its own schema."""

    def __init__(self, db, cooldown_minutes: int, daily_cap: int):
        self.db = db
        self.cooldown = datetime.timedelta(minutes=cooldown_minutes)
        self.daily_cap = daily_cap

    async def eligible(self, guild_id: str) -> bool:
        now = datetime.datetime.now(datetime.timezone.utc)

        async with self.db.execute(
            "SELECT happened_at FROM haunts WHERE guild_id = ? ORDER BY happened_at DESC LIMIT 1",
            (guild_id,),
        ) as cursor:
            row = await cursor.fetchone()
        if row is not None:
            last = datetime.datetime.fromisoformat(row[0])
            if now - last < self.cooldown:
                return False

        today = now.date().isoformat()
        async with self.db.execute(
            "SELECT COUNT(*) FROM haunts WHERE guild_id = ? AND substr(happened_at, 1, 10) = ?",
            (guild_id, today),
        ) as cursor:
            (count,) = await cursor.fetchone()
        return count < self.daily_cap

    async def last_victim(self, guild_id: str) -> str | None:
        async with self.db.execute(
            "SELECT victim_id FROM haunts WHERE guild_id = ? AND victim_id IS NOT NULL "
            "ORDER BY happened_at DESC LIMIT 1",
            (guild_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return row[0] if row else None

    async def week_count(self, guild_id: str) -> int:
        since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).isoformat()
        async with self.db.execute(
            "SELECT COUNT(*) FROM haunts WHERE guild_id = ? AND happened_at >= ?",
            (guild_id, since),
        ) as cursor:
            (count,) = await cursor.fetchone()
        return count

    async def record(self, guild_id: str, kind: str, victim_id: str | None = None):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await self.db.execute(
            "INSERT INTO haunts (guild_id, kind, victim_id, happened_at) VALUES (?, ?, ?, ?)",
            (guild_id, kind, victim_id, now),
        )
        await self.db.commit()
