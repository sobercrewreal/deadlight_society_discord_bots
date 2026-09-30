from pathlib import Path

import aiosqlite


async def connect(db_path: str, schema: str) -> aiosqlite.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path)
    await conn.executescript(schema)
    await conn.commit()
    return conn
