# core/admin_services.py

import logging
from datetime import date
from core.db import get_connection

log = logging.getLogger("tinyregg.admin_services")


# ─────────────────────────────────────────────────────────────
# DAILY TASKS
# ─────────────────────────────────────────────────────────────

async def dispatch_daily_tasks():
    """
    Re-dispatch daily tasks for all active profiles.
    """
    conn = get_connection()
    cur = conn.cursor()

    today = date.today().isoformat()

    profiles = cur.execute("""
        SELECT profile_id FROM profiles WHERE is_active = 1
    """).fetchall()

    for row in profiles:
        profile_id = row["profile_id"]

        # NOTE: this assumes your existing task assignment logic
        # lives somewhere else and uses assigned_tasks table.
        # For now we just clear + reassign.
        cur.execute("""
            DELETE FROM assigned_tasks
            WHERE profile_id = ? AND date = ?
        """, (profile_id, today))

        # TODO: call your real task assignment function here

    conn.commit()
    conn.close()

    log.warning("Admin dispatched daily tasks")


async def force_daily_reset():
    """
    Force a global daily reset.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM task_history")
    cur.execute("DELETE FROM assigned_tasks")

    cur.execute("""
        INSERT OR REPLACE INTO task_reset_state (id, last_reset_date)
        VALUES (1, ?)
    """, (date.today().isoformat(),))

    conn.commit()
    conn.close()

    log.critical("Admin forced daily reset")


# ─────────────────────────────────────────────────────────────
# USER CONTROL
# ─────────────────────────────────────────────────────────────

async def reset_user_state(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT profile_id FROM profiles WHERE user_id = ?
    """, (str(user_id),))

    row = cur.fetchone()
    if not row:
        conn.close()
        return

    profile_id = row["profile_id"]

    cur.execute("DELETE FROM assigned_tasks WHERE profile_id = ?", (profile_id,))
    cur.execute("DELETE FROM task_history WHERE profile_id = ?", (profile_id,))
    cur.execute("DELETE FROM boss_progress WHERE profile_id = ?", (profile_id,))

    conn.commit()
    conn.close()

    log.warning("Admin reset user state: %s", user_id)


async def set_user_streak(user_id: int, value: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT profile_id FROM profiles WHERE user_id = ?
    """, (str(user_id),))

    row = cur.fetchone()
    if not row:
        conn.close()
        return

    profile_id = row["profile_id"]

    cur.execute("""
        INSERT OR REPLACE INTO profile_streaks (
            profile_id,
            required_streak,
            intimacy_streak,
            kink_streak,
            explicit_streak,
            regression_streak
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (profile_id, value, value, value, value, value))

    conn.commit()
    conn.close()

    log.critical("Admin set streaks for user %s → %s", user_id, value)


# ─────────────────────────────────────────────────────────────
# TOKENS
# ─────────────────────────────────────────────────────────────

async def add_tokens(user_id: int, amount: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (user_id, tokens)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
        tokens = tokens + ?
    """, (str(user_id), amount, amount))

    conn.commit()
    conn.close()

    log.warning("Admin added %s tokens to %s", amount, user_id)


async def remove_tokens(user_id: int, amount: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET tokens = MAX(tokens - ?, 0)
        WHERE user_id = ?
    """, (amount, str(user_id)))

    conn.commit()
    conn.close()

    log.warning("Admin removed %s tokens from %s", amount, user_id)
