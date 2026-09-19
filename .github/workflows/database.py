# database.py — SQLite (aiosqlite)
import os
import datetime
import aiosqlite

DB_PATH = os.getenv("DB_PATH", "razor_x_bot.db")
_conn = None


async def get_db():
    global _conn
    if _conn is None:
        _conn = await aiosqlite.connect(DB_PATH)
        _conn.row_factory = aiosqlite.Row
        await _conn.execute("PRAGMA journal_mode=WAL")
    return _conn


class _DB:
    pass


db = _DB()


async def init_db():
    conn = await get_db()
    await conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            plan TEXT DEFAULT 'Bronze',
            expiry TEXT,
            banned INTEGER DEFAULT 0,
            banned_by INTEGER,
            premium_days INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            ip TEXT, port TEXT,
            username TEXT, password TEXT,
            proxy_url TEXT, proxy_type TEXT DEFAULT 'http',
            added_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_proxies_user ON proxies(user_id);

        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site TEXT UNIQUE,
            added_at TEXT
        );

        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card TEXT, status TEXT, response TEXT,
            gateway TEXT, price TEXT, user_id INTEGER,
            created_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_cards_created ON cards(created_at);

        CREATE TABLE IF NOT EXISTS joined_users (
            user_id INTEGER PRIMARY KEY,
            joined_at TEXT
        );

        CREATE TABLE IF NOT EXISTS keys (
            key TEXT PRIMARY KEY,
            plan TEXT, days INTEGER,
            max_claims INTEGER DEFAULT 1,
            claims_used INTEGER DEFAULT 0,
            created_at TEXT
        );
    """)
    await conn.commit()
    print("✅ RAZOR X SQLite DB initialised.")


# ============ USERS ============
async def ensure_user(user_id: int):
    conn = await get_db()
    await conn.execute(
        "INSERT OR IGNORE INTO users (user_id, plan, created_at) VALUES (?, 'Bronze', ?)",
        (user_id, datetime.datetime.utcnow().isoformat())
    )
    await conn.commit()


async def get_user_plan(user_id: int) -> str:
    conn = await get_db()
    async with conn.execute("SELECT plan, expiry FROM users WHERE user_id=?", (user_id,)) as c:
        row = await c.fetchone()
    if not row:
        return "Bronze"
    plan, expiry = row["plan"], row["expiry"]
    if expiry:
        try:
            if datetime.datetime.utcnow() > datetime.datetime.fromisoformat(expiry):
                await conn.execute("UPDATE users SET plan='Bronze', expiry=NULL WHERE user_id=?", (user_id,))
                await conn.commit()
                return "Bronze"
        except Exception:
            pass
    return plan


async def get_user_expiry(user_id: int):
    conn = await get_db()
    async with conn.execute("SELECT expiry FROM users WHERE user_id=?", (user_id,)) as c:
        row = await c.fetchone()
    if row and row["expiry"]:
        try:
            return datetime.datetime.fromisoformat(row["expiry"])
        except Exception:
            return None
    return None


async def set_user_plan(user_id: int, plan: str, days: int = 0):
    conn = await get_db()
    expiry = None
    if days > 0:
        expiry = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).isoformat()
    await conn.execute(
        "INSERT OR IGNORE INTO users (user_id, plan, created_at) VALUES (?, 'Bronze', ?)",
        (user_id, datetime.datetime.utcnow().isoformat())
    )
    await conn.execute(
        "UPDATE users SET plan=?, expiry=?, premium_days=?, updated_at=? WHERE user_id=?",
        (plan, expiry, days, datetime.datetime.utcnow().isoformat(), user_id)
    )
    await conn.commit()


async def is_premium_user(user_id: int) -> bool:
    return (await get_user_plan(user_id)) in ["Core", "Elite", "Root", "X"]


async def is_banned_user(user_id: int) -> bool:
    conn = await get_db()
    async with conn.execute("SELECT banned FROM users WHERE user_id=?", (user_id,)) as c:
        row = await c.fetchone()
    return bool(row["banned"]) if row else False


async def get_users_by_plan(plan: str):
    conn = await get_db()
    async with conn.execute("SELECT * FROM users WHERE plan=?", (plan,)) as c:
        return await c.fetchall()


# ============ JOINED CACHE ============
async def mark_user_joined(user_id: int):
    conn = await get_db()
    await conn.execute(
        "INSERT OR REPLACE INTO joined_users (user_id, joined_at) VALUES (?, ?)",
        (user_id, datetime.datetime.utcnow().isoformat())
    )
    await conn.commit()


async def is_user_marked_joined(user_id: int) -> bool:
    conn = await get_db()
    async with conn.execute("SELECT 1 FROM joined_users WHERE user_id=?", (user_id,)) as c:
        return (await c.fetchone()) is not None


async def remove_joined_mark(user_id: int):
    conn = await get_db()
    await conn.execute("DELETE FROM joined_users WHERE user_id=?", (user_id,))
    await conn.commit()


# ============ PROXIES ============
async def add_proxy_db(user_id: int, proxy_data: dict):
    conn = await get_db()
    await conn.execute(
        """INSERT INTO proxies (user_id, ip, port, username, password, proxy_url, proxy_type, added_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, proxy_data.get("ip"), proxy_data.get("port"),
         proxy_data.get("username"), proxy_data.get("password"),
         proxy_data.get("proxy_url"), proxy_data.get("type", "http"),
         datetime.datetime.utcnow().isoformat())
    )
    await conn.commit()


async def get_all_user_proxies(user_id: int):
    conn = await get_db()
    async with conn.execute("SELECT * FROM proxies WHERE user_id=? ORDER BY id ASC", (user_id,)) as c:
        rows = await c.fetchall()
    return [dict(r) for r in rows]


async def get_proxy_count(user_id: int) -> int:
    conn = await get_db()
    async with conn.execute("SELECT COUNT(*) AS n FROM proxies WHERE user_id=?", (user_id,)) as c:
        return (await c.fetchone())["n"]


async def get_random_proxy(user_id: int):
    import random
    proxies = await get_all_user_proxies(user_id)
    return random.choice(proxies) if proxies else None


async def remove_proxy_by_index(user_id: int, index: int):
    proxies = await get_all_user_proxies(user_id)
    if 0 <= index < len(proxies):
        conn = await get_db()
        p = proxies[index]
        await conn.execute("DELETE FROM proxies WHERE id=?", (p["id"],))
        await conn.commit()
        return p
    return None


async def remove_proxy_by_url(user_id: int, proxy_url: str):
    conn = await get_db()
    cur = await conn.execute("DELETE FROM proxies WHERE user_id=? AND proxy_url=?", (user_id, proxy_url))
    await conn.commit()
    return cur.rowcount > 0


async def clear_all_proxies(user_id: int) -> int:
    conn = await get_db()
    cur = await conn.execute("DELETE FROM proxies WHERE user_id=?", (user_id,))
    await conn.commit()
    return cur.rowcount


# ============ GLOBAL SITES ============
async def add_site_db(user_id: int, site: str) -> bool:
    conn = await get_db()
    try:
        await conn.execute(
            "INSERT INTO sites (site, added_at) VALUES (?, ?)",
            (site, datetime.datetime.utcnow().isoformat())
        )
        await conn.commit()
        return True
    except aiosqlite.IntegrityError:
        return False


async def get_user_sites(user_id: int):
    conn = await get_db()
    async with conn.execute("SELECT site FROM sites ORDER BY id ASC") as c:
        rows = await c.fetchall()
    return [r["site"] for r in rows]


async def remove_site_db(user_id: int, site: str) -> bool:
    conn = await get_db()
    cur = await conn.execute("DELETE FROM sites WHERE site=?", (site,))
    await conn.commit()
    return cur.rowcount > 0


async def get_global_sites():
    conn = await get_db()
    async with conn.execute("SELECT site FROM sites ORDER BY id ASC") as c:
        return [r["site"] for r in await c.fetchall()]


# ============ CARDS ============
async def save_card_to_db(card, status, response, gateway, price, user_id=0):
    conn = await get_db()
    await conn.execute(
        """INSERT INTO cards (card, status, response, gateway, price, user_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (card, status, response, gateway, str(price), user_id,
         datetime.datetime.utcnow().isoformat())
    )
    await conn.commit()


async def get_total_cards_count():
    conn = await get_db()
    async with conn.execute("SELECT COUNT(*) AS n FROM cards") as c:
        return (await c.fetchone())["n"]


async def get_charged_count():
    conn = await get_db()
    async with conn.execute("SELECT COUNT(*) AS n FROM cards WHERE status='CHARGED'") as c:
        return (await c.fetchone())["n"]


async def get_approved_count():
    conn = await get_db()
    async with conn.execute("SELECT COUNT(*) AS n FROM cards WHERE status='APPROVED'") as c:
        return (await c.fetchone())["n"]


# ============ STATS ============
async def get_total_users():
    conn = await get_db()
    async with conn.execute("SELECT COUNT(*) AS n FROM users") as c:
        return (await c.fetchone())["n"]


async def get_premium_count():
    conn = await get_db()
    async with conn.execute("SELECT COUNT(*) AS n FROM users WHERE plan IN ('Core','Elite','Root','X')") as c:
        return (await c.fetchone())["n"]


async def get_all_premium_users():
    conn = await get_db()
    async with conn.execute("SELECT * FROM users WHERE plan IN ('Core','Elite','Root','X')") as c:
        return await c.fetchall()


async def get_total_sites_count():
    conn = await get_db()
    async with conn.execute("SELECT COUNT(*) AS n FROM sites") as c:
        return (await c.fetchone())["n"]


async def get_users_with_sites():
    return await get_total_users()


async def get_sites_per_user():
    return []


async def get_all_sites_detail():
    conn = await get_db()
    async with conn.execute("SELECT * FROM sites") as c:
        return await c.fetchall()


# ============ KEYS ============
async def create_key(key: str, plan: str, max_claims: int, days: int):
    conn = await get_db()
    await conn.execute(
        "INSERT INTO keys (key, plan, max_claims, claims_used, days, created_at) VALUES (?, ?, ?, 0, ?, ?)",
        (key, plan, max_claims, days, datetime.datetime.utcnow().isoformat())
    )
    await conn.commit()


async def get_key(key: str):
    conn = await get_db()
    async with conn.execute("SELECT * FROM keys WHERE key=?", (key,)) as c:
        row = await c.fetchone()
    return dict(row) if row else None


async def claim_key(key: str):
    conn = await get_db()
    async with conn.execute("SELECT * FROM keys WHERE key=?", (key,)) as c:
        row = await c.fetchone()
    if not row:
        return None
    row = dict(row)
    if row["claims_used"] >= row["max_claims"]:
        return None
    await conn.execute("UPDATE keys SET claims_used=claims_used+1 WHERE key=?", (key,))
    await conn.commit()
    return row


async def list_keys():
    conn = await get_db()
    async with conn.execute("SELECT * FROM keys ORDER BY created_at DESC") as c:
        return [dict(r) for r in await c.fetchall()]

async def get_all_user_ids():
    conn = await get_db()
    async with conn.execute("SELECT user_id FROM users") as c:
        rows = await c.fetchall()
    return [r["user_id"] for r in rows]