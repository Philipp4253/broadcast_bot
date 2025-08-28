import aiosqlite
from typing import List, Optional
from datetime import datetime

CREATE_USERS = '''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT,
    username TEXT,
    joined_at TEXT,
    last_active TEXT,
    is_blocked INTEGER DEFAULT 0
);
'''

CREATE_JOBS = '''
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT CHECK(type IN ('once','interval')) NOT NULL,
    text TEXT NOT NULL,
    media_file_id TEXT,
    parse_mode TEXT,
    scheduled_at TEXT,
    interval_seconds INTEGER,
    created_by INTEGER,
    status TEXT DEFAULT 'active'
);
'''

async def init_db(path: str):
    async with aiosqlite.connect(path) as db:
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_JOBS)
        await db.commit()

async def add_user(path: str, user_id: int, first_name: str, username: Optional[str]):
    async with aiosqlite.connect(path) as db:
        now = datetime.utcnow().isoformat()
        await db.execute(
            """INSERT OR IGNORE INTO users (user_id, first_name, username, joined_at, last_active)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, first_name, username, now, now)
        )
        await db.commit()

async def update_last_active(path: str, user_id: int):
    async with aiosqlite.connect(path) as db:
        now = datetime.utcnow().isoformat()
        await db.execute("UPDATE users SET last_active = ? WHERE user_id = ?", (now, user_id))
        await db.commit()

async def mark_blocked(path: str, user_id: int):
    async with aiosqlite.connect(path) as db:
        await db.execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def users_count(path: str) -> int:
    async with aiosqlite.connect(path) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 0") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

async def get_all_users(path: str) -> List[int]:
    async with aiosqlite.connect(path) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_blocked = 0") as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]

# Jobs
async def add_job_once(path: str, text: str, when_iso: str, created_by: int, media_file_id=None, parse_mode=None) -> int:
    async with aiosqlite.connect(path) as db:
        cur = await db.execute(
            """INSERT INTO jobs (type, text, media_file_id, parse_mode, scheduled_at, created_by)
               VALUES ('once', ?, ?, ?, ?, ?)""", (text, media_file_id, parse_mode, when_iso, created_by)
        )
        await db.commit()
        return cur.lastrowid

async def add_job_interval(path: str, text: str, interval_seconds: int, created_by: int, media_file_id=None, parse_mode=None) -> int:
    async with aiosqlite.connect(path) as db:
        cur = await db.execute(
            """INSERT INTO jobs (type, text, media_file_id, parse_mode, interval_seconds, created_by)
               VALUES ('interval', ?, ?, ?, ?, ?)""", (text, media_file_id, parse_mode, interval_seconds, created_by)
        )
        await db.commit()
        return cur.lastrowid

async def list_jobs(path: str):
    async with aiosqlite.connect(path) as db:
        async with db.execute("SELECT id, type, text, scheduled_at, interval_seconds, status FROM jobs ORDER BY id DESC") as cur:
            return await cur.fetchall()

async def cancel_job(path: str, job_id: int) -> bool:
    async with aiosqlite.connect(path) as db:
        await db.execute("UPDATE jobs SET status='cancelled' WHERE id=?", (job_id,))
        await db.commit()
        return True

async def active_jobs(path: str):
    async with aiosqlite.connect(path) as db:
        async with db.execute("SELECT id, type, text, scheduled_at, interval_seconds, media_file_id, parse_mode FROM jobs WHERE status='active'") as cur:
            return await cur.fetchall()
