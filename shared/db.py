from pathlib import Path

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    posted_at TEXT NOT NULL,
    reveal_at TEXT NOT NULL,
    is_real INTEGER NOT NULL,
    content TEXT NOT NULL,
    revealed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS votes (
    story_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    guess INTEGER NOT NULL,
    PRIMARY KEY (story_id, user_id)
);
"""


async def connect(db_path: str) -> aiosqlite.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path)
    await conn.executescript(SCHEMA)
    await conn.commit()
    return conn
