from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent.parent / "data" / "vibemaster.db"

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME,
    total_tzs INTEGER DEFAULT 0
)
"""

CREATE_TECHNICAL_SPECS = """
CREATE TABLE IF NOT EXISTS technical_specs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
"""

CREATE_GENERATION_LOGS = """
CREATE TABLE IF NOT EXISTS generation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT CHECK(type IN ('tz','image','video','code_audit')),
    model_used TEXT,
    success BOOLEAN,
    tokens_used INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""

# Ограничение: хранить не более 5 ТЗ на пользователя
CLEANUP_OLD_TZS = """
DELETE FROM technical_specs
WHERE user_id = ? AND id NOT IN (
    SELECT id FROM technical_specs
    WHERE user_id = ?
    ORDER BY created_at DESC
    LIMIT 5
)
"""


async def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_TECHNICAL_SPECS)
        await db.execute(CREATE_GENERATION_LOGS)
        await db.commit()


async def upsert_user(user_id: int, username: str | None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, first_seen, last_activity)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                last_activity = CURRENT_TIMESTAMP
            """,
            (user_id, username),
        )
        await db.commit()


async def save_tz(user_id: int, content: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO technical_specs (user_id, content) VALUES (?, ?)",
            (user_id, content),
        )
        tz_id = cursor.lastrowid
        await db.execute(
            "UPDATE users SET total_tzs = total_tzs + 1 WHERE user_id = ?",
            (user_id,),
        )
        await db.execute(CLEANUP_OLD_TZS, (user_id, user_id))
        await db.commit()
    return tz_id


async def get_user_tzs(user_id: int, limit: int = 5) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id, content, created_at FROM technical_specs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_tz_by_id(tz_id: int, user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, content, created_at FROM technical_specs WHERE id = ? AND user_id = ?",
            (tz_id, user_id),
        )
        row = await cursor.fetchone()
    return dict(row) if row else None


async def log_generation(
    user_id: int,
    gen_type: str,
    model_used: str,
    success: bool,
    tokens_used: int | None = None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO generation_logs (user_id, type, model_used, success, tokens_used)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, gen_type, model_used, success, tokens_used),
        )
        await db.commit()
