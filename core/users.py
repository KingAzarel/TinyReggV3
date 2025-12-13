from core.db import get_connection


# ─────────────────────────────────────────────────────────────
# User (account-level only)
# ─────────────────────────────────────────────────────────────

def ensure_user(user_id: str):
    """
    Ensures a base user record exists.
    This is account-level state ONLY.
    No identity, no consent, no presence logic.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR IGNORE INTO users (
            user_id,
            tokens,
            boss_tokens,
            theme,
            has_started
        )
        VALUES (?, 0, 0, 'purple_doll', 0)
        """,
        (user_id,),
    )

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# Token helpers
# ─────────────────────────────────────────────────────────────

def add_tokens(user_id: str, amount: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET tokens = tokens + ?
        WHERE user_id = ?
        """,
        (amount, user_id),
    )

    conn.commit()
    conn.close()


def spend_tokens(user_id: str, amount: int) -> bool:
    """
    Attempts to spend tokens.
    Returns True if successful.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT tokens FROM users WHERE user_id = ?",
        (user_id,),
    )
    row = cur.fetchone()

    if not row or row["tokens"] < amount:
        conn.close()
        return False

    cur.execute(
        """
        UPDATE users
        SET tokens = tokens - ?
        WHERE user_id = ?
        """,
        (amount, user_id),
    )

    conn.commit()
    conn.close()
    return True


# ─────────────────────────────────────────────────────────────
# Start flag
# ─────────────────────────────────────────────────────────────

def mark_started(user_id: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET has_started = 1
        WHERE user_id = ?
        """,
        (user_id,),
    )

    conn.commit()
    conn.close()


def has_started(user_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT has_started FROM users WHERE user_id = ?",
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()

    return bool(row and row["has_started"])
